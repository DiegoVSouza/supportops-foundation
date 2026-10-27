"""Private, offline review UI for synthetic P00 campaign answers."""

from __future__ import annotations

import argparse
import csv
import getpass
import hashlib
import hmac
import html
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import threading
from contextlib import closing
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.campaign_execution import ExecutionBlocked, private_directory

PROJECT = Path(__file__).resolve().parents[1]
ANSWERS_DB = PROJECT / ".runtime/llm-review/answers.sqlite"
ANNOTATION_DIR = PROJECT / ".runtime/llm-review-ui"
ANNOTATION_DB = ANNOTATION_DIR / "annotations.sqlite"
CAMPAIGNS_DIR = PROJECT / "artifacts/evals/live"
DATASET_FILE = PROJECT / "evals/datasets/live-v1/cases.jsonl"
RUBRIC_FILE = PROJECT / "evals/rubrics/live-v1/rubric.md"
_LOCK = threading.RLock()


class ReviewError(RuntimeError):
    """Sanitized review prerequisite failure."""


def validate_host(host: str) -> None:
    if host != "127.0.0.1":
        raise ReviewError("loopback_only")


def _is_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        return path.is_junction()
    except AttributeError:
        return False


def _windows_owner_acl(path: Path, *, directory: bool, create: bool) -> None:
    shell = shutil.which("pwsh.exe") or shutil.which("powershell.exe")
    if shell is None:
        raise ReviewError("private_acl_shell_unavailable")
    identity = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    try:
        sid = next(csv.reader(identity.stdout.splitlines()))[1]
    except (IndexError, StopIteration):
        raise ReviewError("private_identity_unavailable") from None
    if identity.returncode or not sid.startswith("S-1-"):
        raise ReviewError("private_identity_unavailable")
    if create:
        grant = f"*{sid}:(OI)(CI)F" if directory else f"*{sid}:F"
        for options in (
            ["/setowner", f"*{sid}"],
            ["/reset"],
            ["/grant:r", grant],
            ["/inheritance:r"],
        ):
            result = subprocess.run(
                ["icacls", str(path), *options],
                capture_output=True,
                check=False,
                timeout=10,
            )
            if result.returncode:
                raise ReviewError("private_acl_update_failed")
    check = r"""
$ErrorActionPreference='Stop'
$item=Get-Item -LiteralPath $env:P00_REVIEW_ITEM
$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User
if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'reparse'}
$acl=Get-Acl -LiteralPath $item.FullName
$entries=@($acl.Access)
if(($env:P00_REVIEW_DIRECTORY -eq '1' -and -not $acl.AreAccessRulesProtected) -or $entries.Count -ne 1 -or $entries[0].AccessControlType -ne 'Allow' -or $entries[0].IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -ne $sid.Value -or $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $sid.Value){throw 'acl'}
Write-Output 'owner_only=true'
"""
    result = subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-Command", check],
        env={
            **os.environ,
            "P00_REVIEW_ITEM": str(path),
            "P00_REVIEW_DIRECTORY": "1" if directory else "0",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if result.returncode or result.stdout.strip() != "owner_only=true":
        raise ReviewError("private_acl_verification_failed")


def secure_annotation_store(project: Path = PROJECT) -> Path:
    root = project.resolve()
    directory = project / ".runtime/llm-review-ui"
    if not directory.resolve().is_relative_to(root) or any(
        _is_reparse(path) for path in (project / ".runtime", directory)
    ):
        raise ReviewError("private_path_invalid")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    allowed = {
        "annotations.sqlite",
        "annotations.sqlite-wal",
        "annotations.sqlite-shm",
        "annotations.sqlite-journal",
    }
    children = list(directory.iterdir())
    if any(p.name not in allowed or p.is_dir() or _is_reparse(p) for p in children):
        raise ReviewError("private_path_unexpected_entry")
    if os.name == "nt":
        _windows_owner_acl(directory, directory=True, create=True)
        for child in children:
            _windows_owner_acl(child, directory=False, create=True)
        _windows_owner_acl(directory, directory=True, create=False)
        for child in children:
            _windows_owner_acl(child, directory=False, create=False)
    else:
        directory.chmod(0o700)
        for child in children:
            child.chmod(0o600)
    return directory


def _readonly_answer_rows(path: Path, *, project: Path = PROJECT) -> list[dict[str, Any]]:
    if (
        any(_is_reparse(parent) for parent in (path.parent.parent, path.parent, path))
        or not path.is_file()
    ):
        raise ReviewError("answer_store_unavailable")
    if os.name != "nt" and any(
        item.stat().st_uid != os.getuid() or item.stat().st_mode & 0o077
        for item in (path.parent, path)
    ):
        raise ReviewError("answer_store_acl_invalid")
    try:
        private_directory(path.parent, project, verify_only=True)
    except ExecutionBlocked:
        raise ReviewError("answer_store_acl_invalid") from None
    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as db:
            db.row_factory = sqlite3.Row
            columns = {row[1] for row in db.execute("PRAGMA table_info(answers)").fetchall()}
            if not {
                "campaign_id",
                "case_id",
                "trial",
                "assistant_content",
                "provider_attempt_id",
            }.issubset(columns):
                raise ReviewError("answer_store_schema_invalid")
            return [
                dict(row)
                for row in db.execute(
                    "SELECT campaign_id,case_id,trial,assistant_content,provider_attempt_id FROM answers ORDER BY campaign_id,case_id,trial"
                )
            ]
    except sqlite3.Error:
        raise ReviewError("answer_store_unavailable") from None


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="strict") as stream:
            for line in stream:
                if line.strip():
                    value = json.loads(line)
                    if isinstance(value, dict):
                        rows.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ReviewError("campaign_metadata_unavailable") from None
    return rows


def _manifest_revisions(manifest: dict[str, Any]) -> dict[str, str]:
    files = manifest.get("files_sha256", {})
    if not isinstance(files, dict):
        return {}
    result: dict[str, str] = {}
    for label, suffix in (
        ("prompt", "/agent/prompts/live-campaign.md"),
        ("schema", "/agent/schemas/live-decision.json"),
        ("dataset", "/evals/datasets/live-v1/cases.jsonl"),
        ("rubric", "/evals/rubrics/live-v1/rubric.md"),
    ):
        matches = [v for k, v in files.items() if k.endswith(suffix)]
        if len(matches) == 1 and isinstance(matches[0], str):
            result[label] = matches[0]
    if (
        "schema" not in result
        and manifest.get("campaign_id") == "free-pilot-v1"
        and manifest.get("candidate_commit") == "476fae54e239cfc7c2200831662ef1af2af52e27"
    ):
        result["schema"] = "NOT_APPLICABLE_LEGACY_NO_SCHEMA"
    return result


def _load_case_context(case_ids: set[str], dataset_path: Path) -> dict[str, dict[str, Any]]:
    # Only records for existing answer rows are returned to the reviewer.
    found: dict[str, dict[str, Any]] = {}
    try:
        with dataset_path.open("r", encoding="utf-8", errors="strict") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                if isinstance(row, dict) and row.get("case_id") in case_ids:
                    found[row["case_id"]] = row
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ReviewError("dataset_context_unavailable") from None
    return found


def build_review_items(
    *,
    answers_path: Path = ANSWERS_DB,
    campaigns_dir: Path = CAMPAIGNS_DIR,
    dataset_path: Path = DATASET_FILE,
    project_root: Path = PROJECT,
) -> list[dict[str, Any]]:
    answer_rows = _readonly_answer_rows(answers_path, project=project_root)
    try:
        dataset_digest = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    except OSError:
        raise ReviewError("dataset_context_unavailable") from None
    manifests: dict[str, dict[str, Any]] = {}
    outcomes: dict[tuple[str, str, int], dict[str, Any]] = {}
    for manifest_path in sorted(campaigns_dir.glob("*/manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise ReviewError("campaign_metadata_unavailable") from None
        campaign = manifest.get("campaign_id")
        if not isinstance(campaign, str) or not campaign:
            continue
        manifests[campaign] = manifest
        for trial in _load_jsonl(manifest_path.parent / "trials.jsonl"):
            key = (campaign, trial.get("case_id"), trial.get("trial"))
            if isinstance(key[1], str) and isinstance(key[2], int):
                outcomes[key] = trial
    case_ids = {str(row["case_id"]) for row in answer_rows}
    case_ids.update(str(key[1]) for key in outcomes)
    contexts = _load_case_context(case_ids, dataset_path)
    answer_index = {
        (str(row["campaign_id"]), str(row["case_id"]), int(row["trial"])): row
        for row in answer_rows
    }
    items: list[dict[str, Any]] = []
    for key, trial in outcomes.items():
        campaign, case_id, trial_number = key
        answer = answer_index.get(key)
        manifest = manifests.get(campaign)
        context = contexts.get(case_id)
        if not manifest or not trial or not context:
            # Missing provenance is never presented as annotatable.
            raise ReviewError("trial_provenance_unavailable")
        revisions = _manifest_revisions(manifest)
        if set(revisions) != {"prompt", "schema", "dataset", "rubric"}:
            raise ReviewError("revision_provenance_unavailable")
        if revisions["dataset"] != dataset_digest:
            raise ReviewError("dataset_provenance_mismatch")
        candidate = manifest.get("candidate_commit")
        attempt_id = (
            answer.get("provider_attempt_id") if answer else trial.get("provider_attempt_id")
        )
        if not isinstance(candidate, str) or not re.fullmatch(r"[0-9a-f]{40}", candidate):
            raise ReviewError("candidate_provenance_unavailable")
        if answer is not None and (
            not isinstance(attempt_id, str)
            or not attempt_id
            or trial.get("provider_attempt_id") != attempt_id
        ):
            raise ReviewError("receipt_provenance_mismatch")
        if any(
            not re.fullmatch(r"[0-9a-f]{64}", digest)
            and not (name == "schema" and digest == "NOT_APPLICABLE_LEGACY_NO_SCHEMA")
            for name, digest in revisions.items()
        ):
            raise ReviewError("revision_provenance_invalid")
        content = None
        if answer is not None:
            content = answer["assistant_content"]
            if not isinstance(content, str):
                raise ReviewError("answer_utf8_invalid")
            try:
                content.encode("utf-8", errors="strict")
            except UnicodeError:
                raise ReviewError("answer_utf8_invalid") from None
        item_id = f"{campaign}/{case_id}/{trial_number}"
        items.append(
            {
                "item_id": item_id,
                "campaign_id": campaign,
                "candidate_commit": candidate,
                "case_id": case_id,
                "trial": trial_number,
                "attempt_id": attempt_id,
                "split": context.get("split", "UNKNOWN"),
                "family": context.get("family", "UNKNOWN"),
                "language": context.get("language", "UNKNOWN"),
                "input": context.get("input", ""),
                "expected": context.get("expected", {}),
                "required_facts": context.get("required_facts", []),
                "forbidden_behavior": context.get("forbidden_behavior", []),
                "rubric_id": context.get("rubric_id", "UNKNOWN"),
                "assistant_content": content,
                "response_available": content is not None,
                "outcome": trial.get("outcome", "UNKNOWN"),
                "critical_failure": bool(trial.get("critical_failure", False)),
                "error_classes": trial.get("error_classes", []),
                "revisions": revisions,
            }
        )
    return sorted(items, key=lambda item: (item["campaign_id"], item["case_id"], item["trial"]))


def _annotation_db(project: Path = PROJECT) -> Path:
    directory = secure_annotation_store(project)
    path = directory / "annotations.sqlite"
    with closing(sqlite3.connect(path)) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS annotations(
              annotation_id TEXT PRIMARY KEY,
              created_at_utc TEXT NOT NULL,
              author TEXT NOT NULL,
              campaign_id TEXT NOT NULL,
              candidate_commit TEXT NOT NULL,
              case_id TEXT NOT NULL,
              trial INTEGER NOT NULL,
              prompt_sha256 TEXT NOT NULL,
              schema_sha256 TEXT NOT NULL,
              dataset_sha256 TEXT NOT NULL,
              rubric_sha256 TEXT NOT NULL,
              schema_score TEXT NOT NULL,
              decision_score TEXT NOT NULL,
              grounding_score TEXT NOT NULL,
              safety_score TEXT NOT NULL,
              error_label TEXT NOT NULL,
              notes TEXT NOT NULL,
              corrects_annotation_id TEXT
            );
            CREATE TRIGGER IF NOT EXISTS annotations_no_update BEFORE UPDATE ON annotations
              BEGIN SELECT RAISE(ABORT,'append-only annotations'); END;
            CREATE TRIGGER IF NOT EXISTS annotations_no_delete BEFORE DELETE ON annotations
              BEGIN SELECT RAISE(ABORT,'append-only annotations'); END;
            """
        )
        db.commit()
    if os.name != "nt":
        path.chmod(0o600)
    elif path.exists():
        _windows_owner_acl(path, directory=False, create=True)
        _windows_owner_acl(path, directory=False, create=False)
    return path


def append_annotation(
    item: dict[str, Any],
    form: dict[str, str],
    *,
    project: Path = PROJECT,
    author: str | None = None,
) -> str:
    allowed = {"PASS", "FAIL", "UNCERTAIN", "NA"}
    scores = [
        form.get(key, "")
        for key in ("schema_score", "decision_score", "grounding_score", "safety_score")
    ]
    if any(score not in allowed for score in scores):
        raise ReviewError("annotation_score_invalid")
    reviewer = form.get("reviewer", "").strip()
    role = form.get("review_role", "primary")
    if not reviewer or len(reviewer) > 80 or role not in {"primary", "independent"}:
        raise ReviewError("reviewer_identity_invalid")
    notes = form.get("notes", "")
    error_label = form.get("error_label", "")
    correction = form.get("corrects_annotation_id", "") or None
    if len(notes.encode("utf-8")) > 2000 or not re.fullmatch(r"[A-Za-z0-9_.:-]{0,80}", error_label):
        raise ReviewError("annotation_size_invalid")
    path = _annotation_db(project)
    annotation_id = secrets.token_hex(16)
    revisions = item["revisions"]
    values = (
        annotation_id,
        datetime.now(UTC).isoformat(),
        json.dumps(
            {
                "os_user": author or getpass.getuser(),
                "declared_reviewer": reviewer,
                "declared_role": role,
            },
            ensure_ascii=False,
        ),
        item["campaign_id"],
        item["candidate_commit"],
        item["case_id"],
        item["trial"],
        revisions["prompt"],
        revisions["schema"],
        revisions["dataset"],
        revisions["rubric"],
        *scores,
        error_label,
        notes,
        correction,
    )
    with _LOCK, closing(sqlite3.connect(path)) as db:
        db.execute("PRAGMA synchronous=FULL")
        if (
            correction is not None
            and not db.execute(
                "SELECT 1 FROM annotations WHERE annotation_id=? AND campaign_id=? AND case_id=? AND trial=?",
                (correction, item["campaign_id"], item["case_id"], item["trial"]),
            ).fetchone()
        ):
            raise ReviewError("annotation_correction_reference_invalid")
        db.execute("INSERT INTO annotations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        db.commit()
    return annotation_id


def _session_token(token: str) -> str:
    return hmac.new(token.encode(), b"p00-private-review-session", hashlib.sha256).hexdigest()


def _csrf_token(token: str) -> str:
    return hmac.new(token.encode(), b"p00-private-review-csrf", hashlib.sha256).hexdigest()


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_login() -> str:
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Private review sign in</title><h1>Private P00 review</h1><p>Enter the one-session access token printed by the local launcher.</p><form method="post" action="/login"><label>Access token <input name="token" type="password" autocomplete="off" required></label><button>Sign in</button></form></html>"""


def _annotation_rows(path: Path = ANNOTATION_DB) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    secure_annotation_store()
    if _is_reparse(path):
        raise ReviewError("annotation_store_unavailable")
    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as db:
            db.row_factory = sqlite3.Row
            return [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM annotations ORDER BY created_at_utc,annotation_id"
                )
            ]
    except sqlite3.Error:
        raise ReviewError("annotation_store_unavailable") from None


def render_index(
    items: list[dict[str, Any]], annotations: list[dict[str, Any]] | None = None
) -> str:
    annotations = annotations or []
    annotation_counts: dict[tuple, int] = {}
    for annotation in annotations:
        key = _review_key(annotation)
        annotation_counts[key] = annotation_counts.get(key, 0) + 1
    candidates = sorted({(item["campaign_id"], item["candidate_commit"]) for item in items})
    rows = []
    for campaign, candidate in candidates:
        selected = [
            i for i in items if i["campaign_id"] == campaign and i["candidate_commit"] == candidate
        ]
        pending = len(selected)
        rows.append(
            f"<section><h2>{_esc(campaign)} · candidate {_esc(candidate)}</h2>"
            f"<p>{pending} available answer trials; annotations recorded: {sum(annotation_counts.get(_review_key(i), 0) for i in selected)}.</p><ul>"
            + "".join(
                f'<li><a href="/item/{quote(i["item_id"], safe="")}">{_esc(i["case_id"])} trial {_esc(i["trial"])}</a> · {_esc(i["outcome"])} · {_esc(i["split"])}</li>'
                for i in selected
            )
            + "</ul></section>"
        )
    critical = sum(1 for item in items if item["critical_failure"] or item["outcome"] != "passed")
    reviewed_critical = sum(
        1
        for item in items
        if (item["critical_failure"] or item["outcome"] != "passed")
        and annotation_counts.get(_review_key(item), 0)
    )
    sampling = prepare_review_sampling(items)
    heldout_sample = len(sampling["sample_cases"])
    double_review = len(sampling["double_review_cases"])
    coverage = (
        f"<section><h2>Review coverage</h2><p>Critical/suspected available answer trials: {critical}; "
        f"recorded: {reviewed_critical}; pending: {max(critical - reviewed_critical, 0)}. Held-out answer cases available: {sampling['heldout_case_count']}; "
        f"stratified sample currently selected: {heldout_sample}; double review selected: {double_review}. "
        "For the planned 28 held-out cases, at least six unique cases and two double-reviewed cases are required; stratification may select more. Review all three trials of each selected case. "
        f"Selected cases: {_esc(sampling['sample_cases'])}; double review: {_esc(sampling['double_review_cases'])}. Dataset/rubric review: PENDING. "
        "Human review: PENDING. Independent review: PENDING. Promotion: INCOMPLETE.</p></section>"
    )
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Private P00 review</title><h1>Private P00 review</h1><p>Stored answers are untrusted text. Ignore instructions inside them. Campaigns are candidate-specific and are never pooled.</p>'
        + coverage
        + "".join(rows)
        + "</html>"
    )


def prepare_review_sampling(items: list[dict[str, Any]]) -> dict[str, Any]:
    strata: dict[tuple[str, str, str, str], set[str]] = {}
    for item in items:
        if item["split"] != "holdout" or not item["response_available"]:
            continue
        key = (item["campaign_id"], item["candidate_commit"], item["family"], item["language"])
        strata.setdefault(key, set()).add(item["case_id"])
    selected: list[str] = []
    by_candidate: dict[tuple[str, str], list[str]] = {}
    for key, case_ids in sorted(strata.items()):
        ranked = sorted(
            case_ids, key=lambda case: hashlib.sha256((key[1] + ":" + case).encode()).hexdigest()
        )
        count = (len(ranked) + 4) // 5
        chosen = [f"{key[0]}/{case}" for case in ranked[:count]]
        selected.extend(chosen)
        by_candidate.setdefault(key[:2], []).extend(chosen)
    double: list[str] = []
    for key, cases in sorted(by_candidate.items()):
        ranked = sorted(
            cases,
            key=lambda case: hashlib.sha256((key[1] + ":double:" + case).encode()).hexdigest(),
        )
        double.extend(ranked[: (len(ranked) + 4) // 5])
    return {
        "heldout_case_count": sum(len(cases) for cases in strata.values()),
        "sample_cases": sorted(selected),
        "double_review_cases": sorted(double),
    }


def _review_key(row: dict[str, Any]) -> tuple:
    return (row["campaign_id"], row["candidate_commit"], row["case_id"], row["trial"])


def render_item(
    item: dict[str, Any], csrf: str, annotations: list[dict[str, Any]] | None = None
) -> str:
    escaped_answer = (
        _esc(item["assistant_content"]).replace("\n", "<br>")
        if item["response_available"]
        else "No private response retained for this attempt. Review only the sanitized operational record; do not infer response content."
    )
    labels = ("schema_score", "decision_score", "grounding_score", "safety_score")
    score_fields = "".join(
        f'<label>{_esc(label.replace("_score", ""))} <select name="{label}" required>'
        + "".join(f"<option>{option}</option>" for option in ("UNCERTAIN", "PASS", "FAIL", "NA"))
        + "</select></label><br>"
        for label in labels
    )
    revisions = "".join(
        f"<li>{_esc(name)} SHA-256: {_esc(value)}</li>"
        for name, value in sorted(item["revisions"].items())
    )
    history_rows = [row for row in (annotations or []) if _review_key(row) == _review_key(item)]
    history = "<h2>Append-only review history</h2>" + (
        "<p>No annotations recorded.</p>"
        if not history_rows
        else "<ol>"
        + "".join(
            f"<li>ID {_esc(row['annotation_id'])}; author {_esc(row['author'])}; {_esc(row['created_at_utc'])}; "
            f"scores schema/decision/grounding/safety: {_esc(row['schema_score'])}/{_esc(row['decision_score'])}/{_esc(row['grounding_score'])}/{_esc(row['safety_score'])}; "
            f"correction of {_esc(row['corrects_annotation_id'] or 'none')}; label {_esc(row['error_label'])}; notes: {_esc(row['notes'])}</li>"
            for row in history_rows
        )
        + "</ol>"
    )
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Review answer</title>'
        f'<p><a href="/">Back</a></p><h1>{_esc(item["campaign_id"])} · {_esc(item["case_id"])} trial {_esc(item["trial"])}</h1>'
        f"<p>Candidate: {_esc(item['candidate_commit'])}; split: {_esc(item['split'])}; family: {_esc(item['family'])}; language: {_esc(item['language'])}; outcome: {_esc(item['outcome'])}</p>"
        f"<p>Recorded error categories: {_esc(item['error_classes'])}. Missing historical HTTP status/code or usage remain unknown; do not reconstruct them.</p>"
        f"<p>Rubric: {_esc(item['rubric_id'])}. Expected contract: {_esc(json.dumps(item['expected'], ensure_ascii=False))}. "
        f"Required facts: {_esc(json.dumps(item['required_facts'], ensure_ascii=False))}. Forbidden behavior: {_esc(json.dumps(item['forbidden_behavior'], ensure_ascii=False))}.</p>"
        f"<h2>Synthetic input</h2><pre>{_esc(item['input'])}</pre><h2>Assistant response (untrusted)</h2><p>{escaped_answer}</p>"
        f'<h2>Provenance</h2><ul>{revisions}</ul>{history}<form method="post" action="/annotate"><input type="hidden" name="item" value="{_esc(item["item_id"])}">'
        f'<input type="hidden" name="csrf" value="{_esc(csrf)}">{score_fields}'
        '<label>Reviewer identity (self-declared; OS author is also recorded) <input name="reviewer" maxlength="80" required></label><br>'
        '<label>Review role <select name="review_role"><option value="primary">Primary</option><option value="independent">Independent</option></select></label><br>'
        '<label>Short redacted error label <input name="error_label" maxlength="80"></label><br>'
        '<label>Correction of annotation ID (leave blank for first review) <input name="corrects_annotation_id" maxlength="64"></label><br>'
        '<label>Notes (private, append-only) <textarea name="notes" maxlength="2000"></textarea></label><br><button>Append review note</button></form></html>'
    )


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "P00PrivateReview/1"
    sys_version = ""

    def log_message(self, _format: str, *args: Any) -> None:
        # Request paths and form fields can carry sensitive review context.
        return

    @property
    def token(self) -> str:
        return self.server.review_token  # type: ignore[attr-defined]

    def _send(self, content: str, status: int = 200, *, cookie: str | None = None) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'; img-src 'none'; connect-src 'none'; script-src 'none'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        value = self.headers.get("Cookie", "")
        expected = f"p00_review={_session_token(self.token)}"
        return any(hmac.compare_digest(part.strip(), expected) for part in value.split(";"))

    def _form(self) -> dict[str, str]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ReviewError("request_invalid") from None
        if length < 0 or length > 8192:
            raise ReviewError("request_invalid")
        payload = self.rfile.read(length).decode("utf-8", errors="strict")
        try:
            return {
                key: values[-1]
                for key, values in parse_qs(
                    payload, keep_blank_values=True, errors="strict", max_num_fields=20
                ).items()
            }
        except ValueError:
            raise ReviewError("request_invalid") from None

    def _items(self) -> list[dict[str, Any]]:
        return build_review_items()

    def do_GET(self) -> None:
        try:
            self._get()
        except (ReviewError, OSError, sqlite3.Error, UnicodeError):
            self._send(
                "<!doctype html><title>Unavailable</title><p>Private review storage or provenance unavailable.</p>",
                503,
            )

    def _get(self) -> None:
        if self.path == "/login":
            self._send(render_login())
            return
        if not self._authorized():
            self._send(render_login(), 401)
            return
        if self.path == "/":
            self._send(render_index(self._items(), _annotation_rows()))
            return
        if self.path.startswith("/item/") and "?" not in self.path:
            item_id = unquote(self.path[len("/item/") :])
            item = next((x for x in self._items() if x["item_id"] == item_id), None)
            if item is None:
                self._send(
                    "<!doctype html><title>Unavailable</title><p>Review item unavailable.</p>", 404
                )
                return
            self._send(render_item(item, _csrf_token(self.token), _annotation_rows()))
            return
        self._send("<!doctype html><title>Not found</title><p>Not found.</p>", 404)

    def do_POST(self) -> None:
        if self.path == "/login":
            try:
                form = self._form()
            except (ReviewError, UnicodeError):
                self._send(render_login(), 400)
                return
            if not hmac.compare_digest(form.get("token", ""), self.token):
                self._send(render_login(), 401)
                return
            cookie = f"p00_review={_session_token(self.token)}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600"
            self._send(
                '<!doctype html><title>Signed in</title><p>Signed in. <a href="/">Continue</a></p>',
                cookie=cookie,
            )
            return
        if not self._authorized() or self.path != "/annotate":
            self._send(render_login(), 401)
            return
        origin = self.headers.get("Origin")
        if origin and origin != f"http://127.0.0.1:{self.server.server_port}":
            self._send("<!doctype html><title>Rejected</title><p>Request rejected.</p>", 403)
            return
        try:
            form = self._form()
            if not hmac.compare_digest(form.get("csrf", ""), _csrf_token(self.token)):
                raise ReviewError("csrf_invalid")
            item = next((x for x in self._items() if x["item_id"] == form.get("item")), None)
            if item is None:
                raise ReviewError("provenance_unavailable")
            annotation_id = append_annotation(item, form)
        except (ReviewError, UnicodeError, sqlite3.Error, OSError):
            self._send(
                "<!doctype html><title>Rejected</title><p>Review note was not saved. Check provenance and fields.</p>",
                400,
            )
            return
        self._send(
            f'<!doctype html><title>Saved</title><p>Review note appended: {_esc(annotation_id)}. Previous notes were not changed.</p><p><a href="/item/{quote(item["item_id"], safe="")}">Return to item</a></p>'
        )


class PrivateReviewServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], token: str):
        validate_host(address[0])
        self.review_token = token
        super().__init__(address, ReviewHandler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        validate_host(args.host)
        if not 0 <= args.port <= 65535:
            raise ReviewError("port_invalid")
        secure_annotation_store()
        build_review_items()
    except ReviewError as error:
        print(f"Review UI unavailable: {error}")
        return 2
    token = secrets.token_urlsafe(32)
    server = PrivateReviewServer(("127.0.0.1", args.port), token)
    print(f"Private review listening at http://127.0.0.1:{server.server_port}/login")
    print(f"One-session access token: {token}")
    print("Stop with Ctrl+C. No provider or external network is used.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
