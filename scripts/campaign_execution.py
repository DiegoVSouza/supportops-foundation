"""P00 free-only batch binding, sanitized reporting and private synthetic review state."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import closing, suppress
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from scripts.campaign_batch import ResourceCaps, TrialOutcome, TrialReservation, run_chunk
from scripts.campaign_runtime import CampaignLedger


class ExecutionBlocked(RuntimeError):
    """A sanitized prerequisite or operational stop."""


# The ledger already includes every historical reservation across campaign IDs.
# These are full primary ceilings, leaving the separate 60-call confirmation reserve.
PRIMARY_CAPS = ResourceCaps(
    149,
    305152,
    38144,
    Decimal("0.0343296"),
)


def validate_live_scope(stage: str, campaign: str) -> None:
    """Phase 028 funds one replacement; historical campaigns never resume."""
    if stage == "development" and campaign in {"free-dev-c1", "free-dev-c2"}:
        raise ExecutionBlocked("immutable_campaign_provenance_mismatch")
    if (stage, campaign) != ("development", "free-dev-c2r1"):
        raise ExecutionBlocked("phase_028_live_scope_not_allocated")


def _safe_account_path(lab: Path, path: Path) -> Path:
    if not path.resolve().is_relative_to(lab.resolve()):
        raise ExecutionBlocked("root_account_path_outside_lab")
    for part in (path, *path.parents):
        if part == lab:
            break
        if part.is_symlink() or part.is_junction():
            raise ExecutionBlocked("root_account_linked_path")
        if part.is_file() and part.stat().st_nlink != 1:
            raise ExecutionBlocked("root_account_linked_path")
    return path


def verify_applied_policy_binding(lab: Path, policy: dict[str, Any]) -> str:
    """Read-only applied-policy and provider-ledger identity gate before any live setup."""
    runtime = lab / ".runtime/llm-live-readiness"
    marker = _safe_account_path(lab, runtime / "policy-migration.pending")
    if marker.exists() or marker.is_symlink() or marker.is_junction():
        raise ExecutionBlocked("policy_migration_pending")
    expected = {
        "requests": 219,
        "input_tokens": 448512,
        "output_tokens": 56064,
        "estimated_cost_usd": "0.0504576",
    }
    projects = policy.get("projects")
    p00 = projects.get("p00") if isinstance(projects, dict) else None
    if (
        policy.get("model") != "openai/gpt-oss-20b"
        or policy.get("authorized_paid_spend_usd") != "0.00"
        or not isinstance(p00, dict)
        or any(p00.get(name) != value for name, value in expected.items())
        or p00.get("calls_per_trial") != 1
        or p00.get("input_tokens_per_call") != 2048
        or p00.get("output_tokens_per_call") != 256
    ):
        raise ExecutionBlocked("p00_allocation_policy_mismatch")
    confirmation = {
        "requests": 60,
        "input_tokens": 122880,
        "output_tokens": 15360,
        "estimated_cost_usd": "0.013824",
    }
    remaining = {
        "requests": p00.get("requests", 0) - PRIMARY_CAPS.requests - 10,
        "input_tokens": p00.get("input_tokens", 0) - PRIMARY_CAPS.input_tokens - 20480,
        "output_tokens": p00.get("output_tokens", 0) - PRIMARY_CAPS.output_tokens - 2560,
    }
    try:
        remaining_cost = (
            Decimal(p00.get("estimated_cost_usd", "-1"))
            - PRIMARY_CAPS.estimated_cost_usd
            - Decimal("0.002304")
        )
    except (ArithmeticError, TypeError, ValueError):
        raise ExecutionBlocked("p00_allocation_policy_mismatch") from None
    if remaining != {
        key: value for key, value in confirmation.items() if key != "estimated_cost_usd"
    } or remaining_cost != Decimal(confirmation["estimated_cost_usd"]):
        raise ExecutionBlocked("p00_confirmation_reserve_changed")
    policy_sha = hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest()
    registry_path = _safe_account_path(lab, runtime / "ledger-references.json")
    ledger_path = _safe_account_path(
        lab, lab / "projects/p00/artifacts/evals/live/provider-usage.sqlite"
    )
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        if registry.get("policy_sha256") != policy_sha:
            raise ExecutionBlocked("applied_policy_registry_mismatch")
        identity = registry["projects"]["p00"]
        if not isinstance(identity, str) or not re.fullmatch(r"[a-f0-9]{32}", identity):
            raise ExecutionBlocked("p00_provider_ledger_identity_mismatch")
        with closing(sqlite3.connect(ledger_path.as_uri() + "?mode=ro", uri=True)) as db:
            rows = db.execute("SELECT identity FROM identity").fetchall()
        if len(rows) != 1 or rows[0][0] != identity:
            raise ExecutionBlocked("p00_provider_ledger_identity_mismatch")
    except ExecutionBlocked:
        raise
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        raise ExecutionBlocked("root_account_binding_unavailable") from None
    return identity


def require_committed_sources(project: Path, source_files: dict[str, str]) -> str:
    """Reject dirty, staged, missing or untracked fingerprinted inputs in either owner."""
    lab = project.parents[1]
    grouped: dict[Path, list[str]] = {project: [], lab: []}
    for name in source_files:
        path = lab / name
        owner = project if path.is_relative_to(project) else lab
        grouped[owner].append(path.relative_to(owner).as_posix())
    for owner, paths in grouped.items():
        if not paths:
            continue
        for command in (
            ["git", "ls-files", "--error-unmatch", "--", *paths],
            ["git", "diff", "--quiet", "HEAD", "--", *paths],
        ):
            result = subprocess.run(command, cwd=owner, capture_output=True, check=False)
            if result.returncode:
                raise ExecutionBlocked("candidate_has_uncommitted_source_changes")
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, text=True, capture_output=True, check=True
    ).stdout.strip()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def private_directory(path: Path, project: Path, *, verify_only: bool = False) -> None:
    if not path.resolve().is_relative_to(project.resolve()):
        raise ExecutionBlocked("review_path_outside_project")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "nt":
        shell = shutil.which("pwsh.exe") or shutil.which("powershell.exe")
        if shell is None:
            raise ExecutionBlocked("private_review_acl_shell_unavailable")
        children = list(path.iterdir())
        allowed = {
            "answers.sqlite",
            "answers.sqlite-wal",
            "answers.sqlite-shm",
            "answers.sqlite-journal",
        }
        if (
            path.is_symlink()
            or path.is_junction()
            or any(
                child.name not in allowed
                or child.is_symlink()
                or child.is_junction()
                or child.is_dir()
                for child in children
            )
        ):
            raise ExecutionBlocked("unexpected_private_review_path")
        if not verify_only:
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
                raise ExecutionBlocked("private_review_identity_unavailable") from None
            if identity.returncode or not re.fullmatch(r"S-1-[0-9-]+", sid):
                raise ExecutionBlocked("private_review_identity_unavailable")
            # /reset clears existing explicit grants; removing inheritance alone
            # does not. Scope each operation to this directory/known DB files.
            for item in [path, *children]:
                grant = f"*{sid}:(OI)(CI)F" if item == path else f"*{sid}:F"
                for label, options in (
                    ("owner", ["/setowner", f"*{sid}"]),
                    ("reset", ["/reset"]),
                    ("grant", ["/grant:r", grant]),
                    ("inheritance", ["/inheritance:r"]),
                ):
                    result = subprocess.run(
                        ["icacls", str(item), *options],
                        capture_output=True,
                        check=False,
                        timeout=10,
                    )
                    if result.returncode:
                        raise ExecutionBlocked(f"private_review_acl_{label}_failed")
        # Read back the DACL without Set-Acl/SACL privileges.
        script = r"""
$ErrorActionPreference='Stop'
$directory=Get-Item -LiteralPath $env:P00_REVIEW_PATH
$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User
if($directory.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'review reparse point'}
$children=@(Get-ChildItem -LiteralPath $directory.FullName -Force)
$allowed=@('answers.sqlite','answers.sqlite-wal','answers.sqlite-shm','answers.sqlite-journal')
foreach($child in $children){
  if($child.PSIsContainer -or $child.Name -notin $allowed -or ($child.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'unexpected review file'}
}
foreach($item in @($directory)+$children){
  $check=Get-Acl -LiteralPath $item.FullName
  $entries=@($check.Access)
  if(($item.PSIsContainer -and -not $check.AreAccessRulesProtected) -or $entries.Count -ne 1 -or $entries[0].AccessControlType -ne 'Allow' -or $entries[0].IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -ne $sid.Value -or $check.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $sid.Value){throw 'review ACL verification'}
}
Write-Output 'owner_only=true'
"""
        result = subprocess.run(
            [shell, "-NoProfile", "-NonInteractive", "-Command", script],
            env={**os.environ, "P00_REVIEW_PATH": str(path)},
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        if result.returncode or result.stdout.strip() != "owner_only=true":
            raise ExecutionBlocked("private_review_acl_unavailable")
    else:
        path.chmod(0o700)


class ReviewStore:
    def __init__(self, project: Path):
        directory = project / ".runtime/llm-review"
        private_directory(directory, project)
        self.path = directory / "answers.sqlite"
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("PRAGMA synchronous=FULL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS answers(campaign_id TEXT, case_id TEXT, trial INTEGER,
                  assistant_content TEXT NOT NULL, provider_attempt_id TEXT,
                  PRIMARY KEY(campaign_id,case_id,trial));
                CREATE TRIGGER IF NOT EXISTS no_answer_update BEFORE UPDATE ON answers
                  BEGIN SELECT RAISE(ABORT,'immutable review answer'); END;
                CREATE TRIGGER IF NOT EXISTS no_answer_delete BEFORE DELETE ON answers
                  BEGIN SELECT RAISE(ABORT,'immutable review answer'); END;
            """)
            db.commit()
        if os.name != "nt":
            self.path.chmod(0o600)
        else:
            private_directory(directory, project, verify_only=True)

    def put(
        self, campaign: str, case_id: str, trial: int, content: str, attempt: str | None
    ) -> None:
        if not isinstance(content, str) or len(content.encode("utf-8")) > 32768:
            raise ExecutionBlocked("invalid_synthetic_review_content")
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("PRAGMA synchronous=FULL")
            db.execute(
                "INSERT INTO answers VALUES(?,?,?,?,?)",
                (campaign, case_id, trial, content, attempt),
            )
            db.commit()


class ProviderClient:
    provenance = "live"

    def __init__(self, project: Path):
        lab = project.parents[1]
        env = {
            name: value for name, value in os.environ.items() if not name.startswith("GROQ_API_KEY")
        }
        env["LLM_MODE"] = "live"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-S",
                str(lab / "scripts/harness/live_provider_transport.py"),
                "--project",
                "p00",
            ],
            cwd=lab,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
        self.reader = ThreadPoolExecutor(max_workers=1)
        self.last_stop = None
        try:
            self.ready = self.receive(80)
            if self.ready.get("status") != "ready" or self.ready.get("protocol_version") != 1:
                raise ExecutionBlocked(self.ready.get("reason", "provider_session_unavailable"))
        except BaseException:
            self.close()
            raise

    def receive(self, seconds: float) -> dict[str, Any]:
        assert self.process.stdout is not None
        future = self.reader.submit(self.process.stdout.readline, 2_000_000)
        try:
            line = future.result(timeout=seconds)
            result = json.loads(line)
        except (FutureTimeout, ValueError, OSError):
            self.process.kill()
            self.process.wait(timeout=5)
            raise ExecutionBlocked("provider_process_timeout_or_invalid_protocol") from None
        if not isinstance(result, dict):
            raise ExecutionBlocked("invalid_provider_protocol")
        return result

    def request(self, envelope: dict[str, Any], operation: str) -> dict[str, Any]:
        assert self.process.stdin is not None
        self.process.stdin.write(
            json.dumps({**envelope, "operation": operation}, ensure_ascii=False) + "\n"
        )
        self.process.stdin.flush()
        result = self.receive(min(20, envelope.get("timeout_seconds", 15) + 2))
        self.last_stop = result.get("reason")
        return result

    def close(self) -> None:
        if self.process.stdin:
            with suppress(OSError):
                self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self.reader.shutdown(wait=True, cancel_futures=True)
        if self.process.stdout:
            self.process.stdout.close()


def fingerprint(project: Path, policy_path: Path) -> dict[str, str]:
    files = [
        *sorted((project / "scripts").glob("*.py")),
        *sorted((project / "supportops_foundation").rglob("*.py")),
        project / "agent/prompts/live-campaign.md",
        project / "agent/schemas/live-decision.json",
        project / "evals/live-campaign.json",
        project / "evals/live-execution.json",
        project / "evals/datasets/live-v1/cases.jsonl",
        project / "evals/datasets/live-v1/manifest.json",
        project / "evals/rubrics/live-v1/rubric.md",
        project / "uv.lock",
        project / "pyproject.toml",
    ]
    lab = project.parents[1]
    files += [
        policy_path,
        lab / "scripts/harness/live_free_account.py",
        lab / "scripts/harness/live_provider_transport.py",
        lab / ".planning/llm-live-readiness/phases/027-free-envelope-plus13/AUTHORIZATION.json",
    ]
    return {
        str(path.relative_to(lab)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
    }


def build_payload(project: Path, prompt: str, user_input: str, config: dict) -> dict[str, Any]:
    """Build the complete provider payload deterministically and enforce a conservative byte bound."""
    schema = json.loads((project / "agent/schemas/live-decision.json").read_text(encoding="utf-8"))
    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input},
        ],
        "max_completion_tokens": 256,
        "temperature": 0,
        "reasoning_effort": "low",
        "include_reasoning": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "live_decision", "strict": True, "schema": schema},
        },
    }
    if payload_input_bound(payload) > 2048:
        raise ExecutionBlocked("serialized_input_exceeds_reserved_bound")
    return payload


def payload_input_bound(payload: dict[str, Any]) -> int:
    """Mirror protocol v1 wire normalization and conservative chat/tool framing."""
    wire = {**payload, "stream": False}
    encoded = json.dumps(wire, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode(
        "utf-8"
    )
    return len(encoded) + 256 + 64 * len(wire["messages"]) + 128 * len(wire.get("tools", []))


def sanitized_diagnostic(result: dict[str, Any], *, evaluated: bool) -> dict[str, Any]:
    """Keep only typed, categorical provider metadata; never copy provider text or headers."""
    codes = {
        "json_validate_failed",
        "tool_use_failed",
        "context_length_exceeded",
        "invalid_request_error",
        "invalid_api_key",
        "authentication_error",
        "model_not_found",
        "model_permission_blocked",
        "rate_limit_exceeded",
        "insufficient_quota",
        "billing_hard_limit_reached",
        "blocked_api_access",
        "OTHER",
    }
    reasons = {
        "quota",
        "transport",
        "credential",
        "rate_limit",
        "model_access",
        "accounting",
        "output_schema",
        "tool_selection",
        "request_schema",
    }
    status = result.get("http_status")
    return {
        "http_status": status if type(status) is int and 100 <= status <= 599 else None,
        "provider_error_code": result.get("provider_error_code")
        if result.get("provider_error_code") in codes
        else ("OTHER" if not evaluated else None),
        "diagnostic_class": result.get("reason")
        if result.get("reason") in reasons
        else ("configuration" if not evaluated else None),
    }


def wilson(successes: int, total: int) -> list[float] | None:
    if not total:
        return None
    z = 1.959963984540054
    rate, scale = successes / total, 1 + z * z / total
    middle = (rate + z * z / (2 * total)) / scale
    radius = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / scale
    return [max(0.0, middle - radius), min(1.0, middle + radius)]


def verify_provider_usage(project: Path, campaign: str, rows: list[dict[str, Any]]) -> None:
    live = [row for row in rows if row["provenance"] == "live"]
    if not live:
        return
    path = project / "artifacts/evals/live/provider-usage.sqlite"
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            for row in live:
                receipt = db.execute(
                    "SELECT * FROM usage_events WHERE attempt_id=? AND event='completed'",
                    (row["provider_attempt_id"],),
                ).fetchone()
                if receipt is None or (
                    receipt["campaign"],
                    receipt["case_id"],
                    receipt["trial"],
                    receipt["call_index"],
                ) != (campaign, row["case_id"], row["trial"], 1):
                    raise ExecutionBlocked("missing_or_mismatched_provider_usage_receipt")
                if row["model_evaluated"] and (
                    receipt["status"] != "ok"
                    or row["usage"]
                    != {
                        "input_tokens": receipt["actual_input"],
                        "output_tokens": receipt["actual_output"],
                    }
                ):
                    raise ExecutionBlocked("model_trial_without_verified_provider_usage")
    except sqlite3.Error:
        raise ExecutionBlocked("provider_usage_proof_unavailable") from None


def discrete_prediction(prediction: Any) -> dict[str, Any] | None:
    if not isinstance(prediction, dict) or not isinstance(prediction.get("decision"), dict):
        return None
    decision = prediction["decision"]

    def enum(value, allowed):
        return value if isinstance(value, str) and value in allowed else "INVALID"

    tool = prediction.get("tool")
    return {
        "category": enum(
            decision.get("category"),
            {"billing", "account_access", "technical", "shipping", "other"},
        ),
        "action": enum(decision.get("action"), {"answer", "request_info", "escalate", "refund"}),
        "escalate": decision.get("escalate") if type(decision.get("escalate")) is bool else None,
        "tool": None
        if tool is None
        else enum(tool, {"lookup_invoice", "lookup_kb", "lookup_order", "issue_refund"}),
        "rationale_present": isinstance(decision.get("rationale"), str)
        and bool(decision["rationale"].strip()),
    }


def report_trials(
    rows: list[dict[str, Any]], cases: list[dict[str, Any]], trials_per_case: int
) -> dict[str, Any]:
    keys = [(row["case_id"], row["trial"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ExecutionBlocked("duplicate_trial_artifact")
    by_id = {case["case_id"]: case for case in cases}
    if any(case not in by_id or not 1 <= trial <= trials_per_case for case, trial in keys):
        raise ExecutionBlocked("trial_outside_frozen_manifest")
    if any(
        row[field]
        != (
            by_id[row["case_id"]]["expected"]["category"]
            if field == "domain"
            else by_id[row["case_id"]][field]
        )
        for row in rows
        for field in ("domain", "family", "language")
    ):
        raise ExecutionBlocked("trial_slice_metadata_mismatch")

    def score(selected):
        evaluated = [row for row in selected if row["model_evaluated"]]
        return {
            "recorded_trials": len(selected),
            "model_evaluated_trials": len(evaluated),
            "passed_trials": sum(row["passed"] for row in evaluated),
            "operational_failures": sum(not row["model_evaluated"] for row in selected),
            "critical_failures": sum(row.get("critical_failure", False) for row in selected),
            "errors": dict(
                sorted(Counter(error for row in selected for error in row["error_classes"]).items())
            ),
        }

    slices = {
        field: {
            value: score([row for row in rows if row[field] == value])
            for value in sorted(
                {
                    case["expected"]["category"] if field == "domain" else case[field]
                    for case in cases
                }
            )
        }
        for field in ("family", "language", "domain")
    }
    complete_cases = []
    for case in cases:
        observations = [
            row for row in rows if row["case_id"] == case["case_id"] and row["model_evaluated"]
        ]
        if len(observations) == 3 and trials_per_case == 3:
            complete_cases.append(all(row["passed"] for row in observations))
    all_pass = sum(complete_cases)
    return {
        **score(rows),
        "planned_unique_cases": len(cases),
        "planned_trials": len(cases) * trials_per_case,
        "real_model_trials": sum(
            row["model_evaluated"] and row["provenance"] == "live" for row in rows
        ),
        "slices": slices,
        "unique_cases_with_three_model_results": len(complete_cases),
        "unique_cases_all_three_pass": all_pass,
        "all_three_wilson95": wilson(all_pass, len(complete_cases)),
        "human_review_status": "PENDING",
        "grounding_review_status": "PENDING",
        "promotion_status": "INCOMPLETE",
    }


def run_campaign(
    project: Path,
    config: dict,
    cases: list[dict],
    stage: str,
    campaign: str,
    *,
    max_trials: int = 10,
    client_factory=ProviderClient,
    revision: str | None = None,
) -> tuple[dict, int]:
    from scripts.run_live_campaign import validate_prediction

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", campaign):
        raise ExecutionBlocked("invalid_campaign_id")
    if client_factory is ProviderClient or getattr(client_factory, "provenance", None) == "live":
        validate_live_scope(stage, campaign)
    started = time.monotonic()
    deadline = started + config["execution"]["max_wall_clock_seconds"]
    lab = project.parents[1]
    policy_path = lab / "shared/policies/groq-free-campaign.json"
    policy = json.loads(policy_path.read_text())
    caps = policy["projects"]["p00"]
    source_files = fingerprint(project, policy_path)
    if revision is None or client_factory is ProviderClient:
        revision = require_committed_sources(project, source_files)
    if client_factory is ProviderClient or getattr(client_factory, "provenance", None) == "live":
        verify_applied_policy_binding(lab, policy)
    selected = (
        [case for case in cases if case["case_id"] in config["pilot_case_ids"]]
        if stage == "pilot"
        else [case for case in cases if case["split"] == stage]
    )
    trial_count = config["pilot_trials"] if stage == "pilot" else config["trials"]
    if stage == "development" and (len(selected) != 12 or trial_count != 3):
        raise ExecutionBlocked("development_scope_mismatch")
    prompt = (project / "agent/prompts/live-campaign.md").read_text(encoding="utf-8").strip()
    payloads = {
        case["case_id"]: build_payload(project, prompt, case["input"], config) for case in selected
    }
    directory = project / "artifacts/evals/live" / campaign
    manifest_path = directory / "manifest.json"
    frozen = {
        "campaign_id": campaign,
        "stage": stage,
        "model": config["model"],
        "files_sha256": source_files,
        "request_schema_sha256": source_files["projects/p00/agent/schemas/live-decision.json"],
        "sampling_order": [case["case_id"] for case in selected],
        "trials_per_case": trial_count,
        "parameters": {"temperature": 0, "reasoning_effort": "low", "max_completion_tokens": 256},
    }
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if any(manifest.get(key) != value for key, value in frozen.items()):
            raise ExecutionBlocked("immutable_campaign_provenance_mismatch")
    else:
        manifest = {
            **frozen,
            "candidate_commit": revision,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "human_review_status": "PENDING",
        }
        atomic_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    trial_path = directory / "trials.jsonl"
    rows = (
        [json.loads(line) for line in trial_path.read_text().splitlines()]
        if trial_path.exists()
        else []
    )
    report_trials(rows, selected, trial_count)
    verify_provider_usage(project, campaign, rows)
    if any(row.get("critical_failure") is True for row in rows):
        raise ExecutionBlocked("critical_failure_requires_review")
    if any(row.get("outcome") == "provider_error" for row in rows):
        raise ExecutionBlocked("provider_failure_requires_review")
    ledger = CampaignLedger(
        project / "artifacts/evals/live/ledger.sqlite", project="p00", campaign_id=campaign
    )
    recorded = {(row["case_id"], row["trial"]): row for row in ledger.reserved_trials()}
    if any((row["case_id"], row["trial"]) not in recorded for row in rows):
        raise ExecutionBlocked("trial_artifact_without_ledger")
    if any(
        row["passed"] != (row["outcome"] == "passed")
        or (
            recorded[(row["case_id"], row["trial"])]["event"] == "completed"
            and recorded[(row["case_id"], row["trial"])]["outcome"] != row["outcome"]
        )
        for row in rows
    ):
        raise ExecutionBlocked("trial_ledger_outcome_mismatch")
    if any(
        row["event"] == "completed"
        and (key not in {(item["case_id"], item["trial"]) for item in rows})
        for key, row in recorded.items()
    ):
        raise ExecutionBlocked("completed_ledger_without_trial_artifact")
    review = ReviewStore(project)
    price = policy["pricing_per_million"]

    def cost(inp, out):
        return (
            Decimal(inp) * Decimal(price["input_usd"]) + Decimal(out) * Decimal(price["output_usd"])
        ) / 1000000

    planned = [
        TrialReservation(
            case["case_id"],
            trial,
            case["max_input_tokens"],
            case["max_output_tokens"],
            cost(case["max_input_tokens"], case["max_output_tokens"]),
        )
        for case in selected
        for trial in range(1, trial_count + 1)
    ]
    by_id = {case["case_id"]: case for case in selected}
    client = client_factory(project)

    def envelope(item):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ExecutionBlocked("wall_clock_checkpoint")
        return {
            "campaign_id": campaign,
            "case_id": item.case_id,
            "trial": item.trial,
            "call_index": 1,
            "timeout_seconds": min(15, remaining),
            "payload": payloads[item.case_id],
        }

    def guard(item):
        return client.request(envelope(item), "preview").get("status") == "approved"

    def execute(item):
        result = client.request(envelope(item), "complete")
        if not isinstance(result.get("attempt_id"), str) or not re.fullmatch(
            r"[a-f0-9]{32}", result["attempt_id"]
        ):
            raise ExecutionBlocked("provider_outcome_without_durable_attempt")
        case = by_id[item.case_id]
        evaluated = result.get("status") == "ok"
        errors, prediction, issues = [], None, []
        if evaluated:
            try:
                prediction = json.loads(result["content"])
            except (ValueError, KeyError, TypeError):
                errors = ["output_schema"]
            if not errors:
                decision = prediction.get("decision") if isinstance(prediction, dict) else None
                if isinstance(decision, dict) and any(
                    not isinstance(decision.get(field), str) for field in ("category", "action")
                ):
                    issues = ["decision schema is invalid"]
                else:
                    issues = validate_prediction(case, prediction)
                errors = sorted(
                    {
                        "tool_selection"
                        if "tool" in issue
                        else "classification"
                        if "category" in issue
                        else "routing"
                        if "action" in issue or "escalat" in issue
                        else "output_schema"
                        for issue in issues
                    }
                )
            if result.get("finish_reason") == "length":
                errors.append("output_truncated")
            review.put(
                campaign,
                item.case_id,
                item.trial,
                result.get("content", ""),
                result.get("attempt_id"),
            )
        else:
            reason = result.get("reason", "configuration")
            errors = [
                reason
                if reason
                in {
                    "quota",
                    "transport",
                    "credential",
                    "rate_limit",
                    "model_access",
                    "accounting",
                    "output_schema",
                    "request_schema",
                    "tool_selection",
                }
                else "configuration"
            ]
        passed = evaluated and not errors
        outcome = "passed" if passed else "failed" if evaluated else "provider_error"
        row = {
            "case_id": item.case_id,
            "trial": item.trial,
            "family": case["family"],
            "language": case["language"],
            "domain": case["expected"]["category"],
            "provenance": client.provenance,
            "model_evaluated": evaluated,
            "passed": passed,
            "outcome": outcome,
            "error_classes": sorted(set(errors)),
            "prediction": discrete_prediction(prediction),
            "critical_failure": "forbidden side-effect tool" in issues,
            "provider_attempt_id": result.get("attempt_id"),
            "usage": result.get("usage"),
            "latency_ms": result.get("latency_ms"),
            **sanitized_diagnostic(result, evaluated=evaluated),
            "review_reference": {
                "campaign_id": campaign,
                "case_id": item.case_id,
                "trial": item.trial,
            }
            if evaluated
            else None,
        }
        rows.append(row)
        atomic_text(trial_path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
        usage = result.get("usage") or {}
        inp, out = usage.get("input_tokens"), usage.get("output_tokens")
        return TrialOutcome(
            outcome,
            inp,
            out,
            cost(inp, out) if inp is not None and out is not None else None,
            errors[0] if errors else None,
            critical=row["critical_failure"],
        )

    try:
        chunk = run_chunk(
            ledger,
            planned,
            cumulative_caps=PRIMARY_CAPS,
            per_trial_caps=ResourceCaps(
                1,
                caps["input_tokens_per_call"],
                caps["output_tokens_per_call"],
                cost(caps["input_tokens_per_call"], caps["output_tokens_per_call"]),
            ),
            account_guard=guard,
            execute=execute,
            lease_path=lab / ".runtime/llm-live-readiness/campaign.lock",
            checkpoint_path=directory / "ledger.jsonl",
            wall_clock_seconds=max(0.001, deadline - time.monotonic()),
            min_interval_seconds=2.1,
            max_trials=max_trials,
        )
    finally:
        client.close()
    verify_provider_usage(project, campaign, rows)
    finalized = {
        (row["case_id"], row["trial"])
        for row in ledger.reserved_trials()
        if row["event"] == "completed"
    }
    report = report_trials(
        [row for row in rows if (row["case_id"], row["trial"]) in finalized], selected, trial_count
    )
    report.update(
        campaign_id=campaign,
        stage=stage,
        candidate_commit=manifest["candidate_commit"],
        chunk=chunk,
        provider_stop=client.last_stop,
        provider_preflight=getattr(client, "ready", {}).get("preflight"),
        provider_usage_ledger="../provider-usage.sqlite",
        elapsed_seconds=round(time.monotonic() - started, 3),
        unfinalized_trial_artifacts=len(rows) - len(finalized),
        resume_command=None,
    )
    complete = (
        chunk["remaining"] == 0
        and len(rows) == report["planned_trials"]
        and all(row["model_evaluated"] and row["provenance"] == "live" for row in rows)
    )
    report["status"] = (
        "PASS_PROVISIONAL"
        if complete and all(row["passed"] for row in rows)
        else "FAIL_PROVISIONAL"
        if complete
        else "INCOMPLETE"
    )
    atomic_text(directory / "report.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    atomic_text(
        directory / "report.md",
        f"# P00 {stage} campaign\n\nStatus: `{report['status']}`. Human review: `PENDING`. Promotion: `INCOMPLETE`.\n\nRecorded trials: {len(rows)}/{report['planned_trials']}; real model trials: {report['real_model_trials']}; passed: {report['passed_trials']}.\n\nStop: `{report['provider_stop'] or chunk['reason']}`.\n\nResume requires current provenance, funding, window and failure review. No executable live command is published by this report. Completed or uncertain work is never replayed.\n\nPer-domain/family/language/errors and unique-case all-three Wilson intervals: see `report.json`. Raw synthetic answers are only in the private local review database. Provider accounting is authoritative in `../provider-usage.sqlite`; the logical trial ledger is not summed again.\n",
    )
    return report, 0 if report["status"] == "PASS_PROVISIONAL" else 1 if report[
        "status"
    ] == "FAIL_PROVISIONAL" else 2
