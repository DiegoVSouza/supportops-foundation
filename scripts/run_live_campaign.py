#!/usr/bin/env python3
"""Validate and dry-run the P00 live campaign without loading provider code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from contextlib import closing, contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any

try:
    from .campaign_runtime import CampaignLedger
except ImportError:
    from campaign_runtime import CampaignLedger

ROOT = Path(__file__).resolve().parents[1]
VALID_FAMILIES = {
    "model_usage_identity",
    "structured_output_valid",
    "structured_output_invalid",
    "read_only_tool_selection",
    "ambiguous_input",
    "unsupported_request",
    "provider_failure_boundaries",
}
VALID_LANGUAGES = {"en", "pt-BR"}
VALID_CATEGORIES = {"billing", "account_access", "technical", "shipping", "other"}
VALID_ACTIONS = {"answer", "request_info", "refund", "escalate"}
DECISION_KEYS = {"category", "action", "escalate", "rationale"}


class CampaignError(ValueError):
    """Raised for invalid local campaign inputs."""


@contextmanager
def readonly_accounting_window(lab: Path, account: Any, project: Path):
    """Take the same leases as dispatch and clean only sidecars created by reads."""
    from live_free_account import machine_lease

    from scripts.campaign_execution import _safe_account_path

    paths = [account.path(name) for name in account.policy["projects"]]
    paths.append(project / "artifacts/evals/live/ledger.sqlite")
    campaign_lock = _safe_account_path(lab, lab / ".runtime/llm-live-readiness/campaign.lock")
    account_lock = _safe_account_path(lab, account.lock)
    auxiliaries: list[tuple[Path, bool]] = []
    with (
        machine_lease(campaign_lock),
        machine_lease(account_lock),
    ):
        for base in paths:
            _safe_account_path(lab, base)
            for suffix in ("-wal", "-shm"):
                path = _safe_account_path(lab, Path(str(base) + suffix))
                auxiliaries.append((path, path.exists()))
        try:
            yield
        finally:
            for path, existed in auxiliaries:
                if (
                    not existed
                    and path.exists()
                    and path.is_file()
                    and not path.is_symlink()
                    and not path.is_junction()
                ):
                    path.unlink()


def validate_config(config: dict[str, Any], cases: list[dict[str, Any]]) -> None:
    if config.get("campaign_spec") != "llm-live-readiness-v1" or config.get("project") != "p00":
        raise CampaignError("campaign identity does not match P00 readiness spec")
    if config.get("provider") != "groq" or config.get("model") != "openai/gpt-oss-20b":
        raise CampaignError("campaign provider/model differ from the reviewed plan")
    trials = config.get("trials")
    if not isinstance(trials, int) or isinstance(trials, bool) or trials != 3:
        raise CampaignError("full campaign must configure exactly three trials")
    caps = config.get("per_case_caps")
    if not isinstance(caps, dict):
        raise CampaignError("per_case_caps must be an object")
    for name in ("max_provider_calls", "max_input_tokens", "max_output_tokens"):
        value = caps.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise CampaignError(f"invalid configured cap: {name}")
    if caps["max_provider_calls"] != 1 or config.get("max_calls_per_case_trial") != 1:
        raise CampaignError("P00 campaign permits at most one call per case trial")
    for case in cases:
        if case["max_provider_calls"] > caps["max_provider_calls"]:
            raise CampaignError(f"case call cap exceeds campaign cap: {case['case_id']}")
        if case["max_input_tokens"] > caps["max_input_tokens"]:
            raise CampaignError(f"case input-token cap exceeds campaign cap: {case['case_id']}")
        if case["max_output_tokens"] > caps["max_output_tokens"]:
            raise CampaignError(f"case output-token cap exceeds campaign cap: {case['case_id']}")
    if config.get("generation_enabled") not in {True, False}:
        raise CampaignError("generation_enabled must be an explicit boolean")
    confirmation = config.get("confirmation_reserve")
    if not isinstance(confirmation, dict) or any(
        not isinstance(confirmation.get(name), int)
        or isinstance(confirmation.get(name), bool)
        or confirmation[name] < 1
        for name in ("fresh_cases", "trials_per_case", "max_calls_per_case_trial")
    ):
        raise CampaignError("confirmation reserve must have finite positive counts")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignError(f"cannot read JSON file: {path.name}") from exc
    if not isinstance(value, dict):
        raise CampaignError(f"expected JSON object: {path.name}")
    return value


def load_cases(path: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        raw = path.read_bytes()
        lines = raw.decode("utf-8").splitlines()
        cases = [json.loads(line) for line in lines if line.strip()]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CampaignError(f"cannot read case JSONL: {path.name}") from exc
    if not cases or not all(isinstance(case, dict) for case in cases):
        raise CampaignError("case dataset must contain JSON objects")
    if manifest.get("content_sha256") not in {"PENDING: compute after dataset freeze", None}:
        expected_hash = manifest["content_sha256"]
        if expected_hash != hashlib.sha256(raw).hexdigest():
            raise CampaignError("dataset content hash mismatch")
    validate_cases(cases, manifest)
    return cases


def validate_cases(cases: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    required = {
        "case_id",
        "dataset_version",
        "split",
        "source_group",
        "family",
        "language",
        "input",
        "expected",
        "allowed_tools",
        "required_facts",
        "forbidden_behavior",
        "rubric_id",
        "criticality",
        "max_provider_calls",
        "max_input_tokens",
        "max_output_tokens",
        "applicability",
    }
    ids: set[str] = set()
    inputs: set[str] = set()
    group_splits: dict[str, str] = {}
    families: Counter[str] = Counter()
    splits: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    for case in cases:
        missing = required - case.keys()
        if missing:
            raise CampaignError(f"case missing required fields: {','.join(sorted(missing))}")
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise CampaignError("case IDs must be nonempty and unique")
        ids.add(case_id)
        if case.get("dataset_version") != manifest.get("dataset_version"):
            raise CampaignError(f"dataset version mismatch for {case_id}")
        if not isinstance(case["input"], str):
            raise CampaignError(f"case input must be text for {case_id}")
        normalized = " ".join(case["input"].casefold().split())
        if not normalized or normalized in inputs:
            raise CampaignError("case inputs must be nonempty and unique")
        inputs.add(normalized)
        split = case["split"]
        if split not in {"development", "holdout"}:
            raise CampaignError(f"invalid split for {case_id}")
        source_group = case["source_group"]
        if not source_group:
            raise CampaignError(f"source_group is required for {case_id}")
        prior_split = group_splits.setdefault(source_group, split)
        if prior_split != split:
            raise CampaignError(f"source group crosses splits: {source_group}")
        if case["family"] not in VALID_FAMILIES:
            raise CampaignError(f"invalid family for {case_id}")
        if case["language"] not in VALID_LANGUAGES:
            raise CampaignError(f"invalid language for {case_id}")
        expected = case["expected"]
        if not isinstance(expected, dict) or expected.get("category") not in VALID_CATEGORIES:
            raise CampaignError(f"invalid expected category for {case_id}")
        if expected.get("action") not in VALID_ACTIONS or not isinstance(
            expected.get("escalate"), bool
        ):
            raise CampaignError(f"invalid expected action/escalation for {case_id}")
        if expected.get("action") == "escalate" and expected["escalate"] is not True:
            raise CampaignError(f"escalation action must set escalate=true for {case_id}")
        allowed_tools = case["allowed_tools"]
        if not isinstance(allowed_tools, list) or any(
            not isinstance(tool, str) or tool not in {"lookup_invoice", "lookup_order", "lookup_kb"}
            for tool in allowed_tools
        ):
            raise CampaignError(f"invalid allowed-tools list for {case_id}")
        if expected.get("tool") not in allowed_tools and not (
            expected.get("tool") is None and not allowed_tools
        ):
            raise CampaignError(f"expected tool is not in allowed-tools list for {case_id}")
        for cap in ("max_provider_calls", "max_input_tokens", "max_output_tokens"):
            if not isinstance(case[cap], int) or isinstance(case[cap], bool) or case[cap] < 1:
                raise CampaignError(f"invalid {cap} for {case_id}")
        if case["max_provider_calls"] > 1:
            raise CampaignError(f"per-case provider call cap exceeds P00 policy: {case_id}")
        families[case["family"]] += 1
        splits[split] += 1
        languages[case["language"]] += 1
    expected_split_counts = manifest.get("split_counts", {})
    expected_language_counts = manifest.get("language_counts", {})
    if len(cases) != manifest.get("case_count"):
        raise CampaignError("case count does not match manifest")
    if dict(splits) != expected_split_counts:
        raise CampaignError("split counts do not match manifest")
    if dict(languages) != expected_language_counts:
        raise CampaignError("language counts do not match manifest")
    expected_families = set(manifest.get("families", []))
    if set(families) != expected_families:
        raise CampaignError("family list does not match manifest")
    if any(
        families[family] < manifest.get("minimum_cases_per_family", 3)
        for family in expected_families
    ):
        raise CampaignError("a required family has fewer than the minimum distinct cases")


def validate_prediction(case: dict[str, Any], prediction: Any) -> list[str]:
    """Code-first contract checks; answer grounding requires reviewed rubric evidence."""
    errors: list[str] = []
    if not isinstance(prediction, dict) or set(prediction) - {"decision", "tool"}:
        return ["prediction must be an object containing only decision and tool"]
    decision = prediction.get("decision")
    if not isinstance(decision, dict) or set(decision) != DECISION_KEYS:
        return ["decision schema is invalid"]
    if decision.get("category") not in VALID_CATEGORIES:
        errors.append("invalid category")
    if decision.get("action") not in VALID_ACTIONS:
        errors.append("invalid action")
    if not isinstance(decision.get("escalate"), bool):
        errors.append("invalid escalation type")
    if not isinstance(decision.get("rationale"), str) or not decision["rationale"].strip():
        errors.append("missing rationale")
    expected = case["expected"]
    for field in ("category", "action", "escalate"):
        if decision.get(field) != expected[field]:
            errors.append(f"wrong {field}")
    if prediction.get("tool") != expected.get("tool"):
        errors.append("wrong tool selection")
    if prediction.get("tool") == "issue_refund":
        errors.append("forbidden side-effect tool")
    return errors


def pending_values(value: Any, prefix: str = "") -> list[str]:
    pending: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}" if prefix else key
            if child == "PENDING" or (isinstance(child, str) and child.startswith("PENDING:")):
                pending.append(child_path)
            else:
                pending.extend(pending_values(child, child_path))
    return pending


def applied_allocation(project: Path) -> dict[str, Any]:
    """Read the applied shared account and both P00 ledgers without credentials."""
    lab = project.parents[1]
    policy_path = lab / "shared/policies/groq-free-campaign.json"
    registry_path = lab / ".runtime/llm-live-readiness/ledger-references.json"
    sys.path.insert(0, str(project))
    try:
        from scripts.campaign_execution import _safe_account_path

        _safe_account_path(lab, policy_path)
        _safe_account_path(lab, registry_path)
    except (ImportError, OSError, RuntimeError) as exc:
        raise CampaignError("shared allocation path is unsafe") from exc
    policy = load_json(policy_path)
    sys.path.insert(0, str(lab / "scripts/harness"))
    try:
        from live_free_account import SharedAccount

        account = SharedAccount(lab, policy)
    except (ImportError, OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        raise CampaignError("applied shared allocation is unavailable") from exc

    logical_path = project / "artifacts/evals/live/ledger.sqlite"
    try:
        with readonly_accounting_window(lab, account, project):
            refs = account._references()
            attempts = account._history()
            registry_sha = json.loads(registry_path.read_text(encoding="utf-8"))["policy_sha256"]
            p01_logical_reserved_calls = 0
            p01_logical_path = lab / "projects/p01/artifacts/evals/live/ledger.sqlite"
            if p01_logical_path.exists():
                _safe_account_path(lab, p01_logical_path)
                with closing(
                    sqlite3.connect(p01_logical_path.as_uri() + "?mode=ro", uri=True)
                ) as p01_db:
                    p01_logical_reserved_calls = p01_db.execute(
                        "SELECT COALESCE(SUM(reserved_calls),0) FROM events WHERE event='reserved' AND campaign_id IN ('local-operation-v1','local-diagnostic-v1')"
                    ).fetchone()[0]
            with closing(sqlite3.connect(logical_path.as_uri() + "?mode=ro", uri=True)) as db:
                logical_rows = db.execute(
                    """SELECT e.reserved_calls,e.reserved_input_tokens,e.reserved_output_tokens,
                              e.actual_input_tokens,e.actual_output_tokens,e.reserved_cost_usd,
                              e.actual_cost_usd
                       FROM events e JOIN (
                         SELECT project,campaign_id,case_id,trial,MAX(sequence) sequence
                         FROM events GROUP BY project,campaign_id,case_id,trial
                       ) latest ON e.sequence=latest.sequence
                       WHERE e.project='p00'"""
                ).fetchall()
    except (sqlite3.Error, OSError, RuntimeError) as exc:
        raise CampaignError("accounting ledgers are unavailable") from exc

    project_usage: dict[str, dict[str, int]] = {}
    for name in policy["projects"]:
        rows = [row for row in attempts if row["project"] == name]
        project_usage[name] = {
            "requests": len(rows),
            "input_tokens": sum(account.usage(row)["input_tokens"] for row in rows),
            "output_tokens": sum(account.usage(row)["output_tokens"] for row in rows),
            "unknown_attempts": sum(
                row["actual_input"] is None or row["actual_output"] is None for row in rows
            ),
        }
    operation_rows = [
        row
        for row in attempts
        if row["project"] == "p00" and row["campaign"] == "local-live-operation-v1"
    ]
    operation_usage = {
        "requests": len(operation_rows),
        "input_tokens": sum(account.usage(row)["input_tokens"] for row in operation_rows),
        "output_tokens": sum(account.usage(row)["output_tokens"] for row in operation_rows),
    }
    operation_reserve = 10 if policy["projects"]["p00"]["requests"] == 219 else 0
    p01_operation_reserve = 8 if policy["projects"]["p01"]["requests"] == 992 else 0
    p01_operation_rows = [
        row
        for row in attempts
        if row["project"] == "p01"
        and row["campaign"] in {"local-operation-v1", "local-diagnostic-v1"}
    ]
    p01_operation_usage = {
        "requests": len(p01_operation_rows),
        "input_tokens": sum(account.usage(row)["input_tokens"] for row in p01_operation_rows),
        "output_tokens": sum(account.usage(row)["output_tokens"] for row in p01_operation_rows),
    }
    operation_reserves = {"p00": operation_reserve, "p01": p01_operation_reserve}
    other_operation_usage = {}
    for name, migrated_total, reserve in (("p02", 310, 4), ("p03", 160, 4)):
        operation_reserves[name] = (
            reserve if policy["projects"][name]["requests"] == migrated_total else 0
        )
        rows = [
            row
            for row in attempts
            if row["project"] == name and row["campaign"] == "local-operation-v1"
        ]
        other_operation_usage[name] = {
            "requests": len(rows),
            "input_tokens": sum(account.usage(row)["input_tokens"] for row in rows),
            "output_tokens": sum(account.usage(row)["output_tokens"] for row in rows),
        }
    evaluation_usage = {name: dict(value) for name, value in project_usage.items()}
    for field in ("requests", "input_tokens", "output_tokens"):
        evaluation_usage["p00"][field] -= operation_usage[field]
        evaluation_usage["p01"][field] -= p01_operation_usage[field]
        for name, usage in other_operation_usage.items():
            evaluation_usage[name][field] -= usage[field]
    global_caps = policy["campaign_caps"]
    global_usage = {
        field: str(sum(account.usage(row)[field] for row in attempts))
        for field in ("requests", "input_tokens", "output_tokens", "estimated_cost_usd")
    }
    confirmation_calls = {
        "p00": 60,
        "p01": 240,
        "p02": 60,
        "p03": 60,
        "p04": 180,
        "p05": 240,
    }
    primary_calls = {
        name: policy["projects"][name]["requests"]
        - confirmation_calls[name]
        - operation_reserves.get(name, 0)
        for name in policy["projects"]
    }
    remaining_by_project = {
        name: {
            "primary_total": primary_calls[name],
            "primary_consumed": evaluation_usage[name]["requests"],
            "primary_remaining": primary_calls[name] - evaluation_usage[name]["requests"],
            "primary_input_tokens_total": policy["projects"][name]["input_tokens"]
            - (confirmation_calls[name] + operation_reserves.get(name, 0))
            * policy["projects"][name]["input_tokens_per_call"],
            "primary_input_tokens_remaining": policy["projects"][name]["input_tokens"]
            - (confirmation_calls[name] + operation_reserves.get(name, 0))
            * policy["projects"][name]["input_tokens_per_call"]
            - evaluation_usage[name]["input_tokens"],
            "primary_output_tokens_total": policy["projects"][name]["output_tokens"]
            - (confirmation_calls[name] + operation_reserves.get(name, 0))
            * policy["projects"][name]["output_tokens_per_call"],
            "primary_output_tokens_remaining": policy["projects"][name]["output_tokens"]
            - (confirmation_calls[name] + operation_reserves.get(name, 0))
            * policy["projects"][name]["output_tokens_per_call"]
            - evaluation_usage[name]["output_tokens"],
            "confirmation_protected": confirmation_calls[name],
        }
        for name in policy["projects"]
    }

    logical_usage = {
        "requests": sum(row[0] for row in logical_rows),
        "input_tokens": sum(row[3] if row[3] is not None else row[1] for row in logical_rows),
        "output_tokens": sum(row[4] if row[4] is not None else row[2] for row in logical_rows),
        "estimated_cost_usd": str(
            sum(
                (Decimal(row[6]) if row[6] is not None else Decimal(row[5])) for row in logical_rows
            )
        ),
        "unknown_attempts": sum(row[3] is None or row[4] is None for row in logical_rows),
    }
    p00_caps = policy["projects"]["p00"]
    primary = {
        "requests": p00_caps["requests"] - confirmation_calls["p00"] - operation_reserve,
        "input_tokens": p00_caps["input_tokens"]
        - (confirmation_calls["p00"] + operation_reserve) * p00_caps["input_tokens_per_call"],
        "output_tokens": p00_caps["output_tokens"]
        - (confirmation_calls["p00"] + operation_reserve) * p00_caps["output_tokens_per_call"],
        "estimated_cost_usd": str(
            Decimal(p00_caps["estimated_cost_usd"])
            - Decimal("0.013824")
            - (Decimal("0.002304") if operation_reserve else Decimal(0))
        ),
    }
    unknown_transport = [
        row
        for row in attempts
        if row["project"] == "p00" and (row["actual_input"] is None or row["actual_output"] is None)
    ]
    try:
        from scripts.campaign_execution import fingerprint, require_committed_sources

        source_files = fingerprint(project, policy_path)
        candidate_commit = require_committed_sources(project, source_files)
    except (ImportError, OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        raise CampaignError("candidate source provenance is not committed and clean") from exc
    policy_sha = hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest()
    if policy_sha != registry_sha:
        raise CampaignError("applied shared allocation policy is not reconciled")
    return {
        "candidate_commit": candidate_commit,
        "candidate_fingerprint_sha256": hashlib.sha256(
            json.dumps(source_files, sort_keys=True).encode()
        ).hexdigest(),
        "source_sha256": source_files,
        "policy_sha256": policy_sha,
        "policy_registry_sha256_matches": True,
        "registered_provider_ledger_uuids": refs,
        "p00_primary_allocation": primary,
        "p00_operation_allocation": {
            "total": operation_reserve,
            "used": operation_usage["requests"],
            "remaining": operation_reserve - operation_usage["requests"],
            "input_tokens_used": operation_usage["input_tokens"],
            "output_tokens_used": operation_usage["output_tokens"],
        },
        "p01_operation_allocation": {
            "total": p01_operation_reserve,
            "used": p01_operation_usage["requests"],
            "remaining": p01_operation_reserve - p01_operation_usage["requests"],
            "input_tokens_used": p01_operation_usage["input_tokens"],
            "output_tokens_used": p01_operation_usage["output_tokens"],
            "logical_reserved_calls_retained": p01_logical_reserved_calls,
            "logical_unreserved_calls": p01_operation_reserve - p01_logical_reserved_calls,
            "further_execution_authorized": False,
        },
        "other_operation_allocations": {
            name: {
                "total": operation_reserves[name],
                "used": usage["requests"],
                "remaining": operation_reserves[name] - usage["requests"],
                "input_tokens_used": usage["input_tokens"],
                "output_tokens_used": usage["output_tokens"],
            }
            for name, usage in other_operation_usage.items()
        },
        "p00_confirmation_protected": {
            "requests": confirmation_calls["p00"],
            "input_tokens": confirmation_calls["p00"] * p00_caps["input_tokens_per_call"],
            "output_tokens": confirmation_calls["p00"] * p00_caps["output_tokens_per_call"],
            "estimated_cost_usd": "0.013824",
        },
        "provider_ledger_usage": {
            "total_accounted": global_usage,
            "p00": project_usage["p00"],
            "unknown_transport_reservations": [
                {
                    "attempt_id": row["attempt_id"],
                    "input_tokens": row["reserved_input"],
                    "output_tokens": row["reserved_output"],
                }
                for row in unknown_transport
            ],
        },
        "logical_ledger_usage": {
            **logical_usage,
            "unknown_reservations": [
                {"input_tokens": row[1], "output_tokens": row[2]}
                for row in logical_rows
                if row[3] is None or row[4] is None
            ],
        },
        "remaining_capacity_by_project": remaining_by_project,
        "global_remaining": {
            "requests": global_caps["requests"] - int(global_usage["requests"]),
            "primary_requests": sum(primary_calls.values())
            - int(global_usage["requests"])
            + operation_usage["requests"]
            + p01_operation_usage["requests"]
            + sum(usage["requests"] for usage in other_operation_usage.values()),
            "protected_confirmation_requests": sum(confirmation_calls.values()),
        },
        "billing": "UNKNOWN; economic policy estimates are not provider billing",
        "provider_accessed": False,
        "credentials_read": False,
        "paid_spend_usd": "0.00",
    }


def summarize(
    stage: str,
    cases: list[dict[str, Any]],
    config: dict[str, Any],
    manifest: dict[str, Any],
    data_path: Path,
    allocation: dict[str, Any] | None = None,
    campaign_id: str | None = None,
) -> dict[str, Any]:
    if stage == "pilot":
        selected_ids = config.get("pilot_case_ids", [])
        by_id = {case["case_id"]: case for case in cases}
        if len(selected_ids) != 6 or len(set(selected_ids)) != 6:
            raise CampaignError("pilot must contain six distinct case IDs")
        selected = [by_id[item] for item in selected_ids if item in by_id]
        if len(selected) != 6 or any(case["split"] != "development" for case in selected):
            raise CampaignError("pilot IDs must identify six development cases")
        trial_count = config["pilot_trials"]
    else:
        selected = [case for case in cases if case["split"] == stage]
        trial_count = config["trials"]
    family_counts = Counter(case["family"] for case in selected)
    language_counts = Counter(case["language"] for case in selected)
    calls_per_trial = sum(case["max_provider_calls"] for case in selected)
    max_calls = calls_per_trial * trial_count
    max_input_tokens = sum(case["max_input_tokens"] for case in selected) * trial_count
    max_output_tokens = sum(case["max_output_tokens"] for case in selected) * trial_count
    blockers = pending_values(config.get("cumulative_caps", {}), "cumulative_caps")
    blockers.extend(pending_values(config.get("execution", {}), "execution"))
    blockers.extend(pending_values(config.get("confirmation_reserve", {}), "confirmation_reserve"))
    blockers.extend(pending_values(config.get("authorization", {}), "authorization"))
    if (
        manifest.get("review_status") != "APPROVED"
        and "authorization.dataset_review" not in blockers
    ):
        blockers.append("dataset_review")
    if config.get("generation_enabled") is not True:
        blockers.append("generation_enabled")
    all_case_calls = sum(case["max_provider_calls"] for case in cases)
    all_case_input = sum(case["max_input_tokens"] for case in cases)
    all_case_output = sum(case["max_output_tokens"] for case in cases)
    campaign_trials = config["trials"]
    confirmation = config["confirmation_reserve"]
    confirmation_trials = confirmation["trials_per_case"]
    confirmation_cases = confirmation["fresh_cases"]
    pilot_cases = len(config["pilot_case_ids"])
    pilot_calls = sum(
        case["max_provider_calls"]
        for case in cases
        if case["case_id"] in set(config["pilot_case_ids"])
    )
    cumulative = config["cumulative_caps"]
    if allocation is not None:
        p00 = allocation["p00_primary_allocation"]
        confirmation_caps = allocation["p00_confirmation_protected"]
        cumulative = {
            "max_requests": p00["requests"] + confirmation_caps["requests"],
            "max_input_tokens": p00["input_tokens"] + confirmation_caps["input_tokens"],
            "max_output_tokens": p00["output_tokens"] + confirmation_caps["output_tokens"],
            "max_estimated_spend_usd": str(
                Decimal(p00["estimated_cost_usd"])
                + Decimal(confirmation_caps["estimated_cost_usd"])
            ),
            "authorized_paid_spend_usd": "0.00",
            "authorized_free_quota_calls": p00["requests"] + confirmation_caps["requests"],
        }
    reservations = {
        "primary_campaign_cases": len(cases),
        "primary_campaign_logical_trials": len(cases) * campaign_trials,
        "primary_campaign_max_calls": all_case_calls * campaign_trials,
        "primary_campaign_max_input_tokens": all_case_input * campaign_trials,
        "primary_campaign_max_output_tokens": all_case_output * campaign_trials,
        "pilot_cases": pilot_cases,
        "pilot_max_calls": pilot_calls,
        "confirmation_cases": confirmation_cases,
        "confirmation_logical_trials": confirmation_cases * confirmation_trials,
        "confirmation_max_calls": confirmation_cases
        * confirmation_trials
        * confirmation["max_calls_per_case_trial"],
        "confirmation_max_input_tokens": confirmation_cases
        * confirmation_trials
        * config["per_case_caps"]["max_input_tokens"],
        "confirmation_max_output_tokens": confirmation_cases
        * confirmation_trials
        * config["per_case_caps"]["max_output_tokens"],
        "confirmation_spend_usd": confirmation["reserved_spend_usd"],
        "baseline_all_stages_max_calls_if_additive": all_case_calls * campaign_trials
        + pilot_calls
        + confirmation_cases * confirmation_trials * confirmation["max_calls_per_case_trial"],
        "all_stages_max_calls_if_additive": cumulative["max_requests"]
        if allocation is not None
        else all_case_calls * campaign_trials
        + pilot_calls
        + confirmation_cases * confirmation_trials * confirmation["max_calls_per_case_trial"],
        "authorized_new_primary_calls": 10 if allocation is not None else 0,
    }
    result = {
        "project": config["project"],
        "stage": stage,
        "mode": "dry-run",
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "review_status": manifest.get("review_status", "PENDING"),
        "cases": len(selected),
        "trials_per_case": trial_count,
        "logical_trials": len(selected) * trial_count,
        "max_provider_calls": max_calls,
        "max_input_tokens": max_input_tokens,
        "max_output_tokens": max_output_tokens,
        "planned_reservations": reservations,
        "families": dict(sorted(family_counts.items())),
        "languages": dict(sorted(language_counts.items())),
        "model": config["model"],
        "provider": config["provider"],
        "limits": {
            "per_case": config["per_case_caps"],
            "cumulative": cumulative,
            "execution": config["execution"],
            "confirmation_reserve": config["confirmation_reserve"],
            "authorized_paid_spend_usd": config["cumulative_caps"]["authorized_paid_spend_usd"],
        },
        "blockers": sorted(set(blockers)),
        "generation_authorized": False,
        "provider_accessed": False,
        "credentials_read": False,
        "docker_mutated": False,
    }
    if allocation is not None:
        result.update(
            campaign_id=campaign_id or ("free-dev-c2r1" if stage == "development" else None),
            candidate=allocation,
            c2_scope={
                "replacement_campaign": "free-dev-c2r1",
                "historical_c2": {
                    "campaign_id": "free-dev-c2",
                    "candidate_commit": "7099cc5d0f4d576d14f28f7dab4648b074b59740",
                    "completed_trials": 13,
                    "unexecuted_trials": 23,
                    "results_reused": False,
                },
                "stage": "development",
                "unique_cases": 12,
                "trials_per_case": 3,
                "maximum_new_calls": 36,
                "batches_maximum": [10, 10, 10, 6],
                "previous_candidate": "free-dev-c1",
                "previous_candidate_commit": "b42a198246274db5f7feb17a247ef1fe90e662e6",
                "previous_candidate_completed_trials": 12,
                "previous_candidate_unexecuted_trials": 24,
                "previous_candidate_results_reused": False,
                "previous_pilot": {
                    "campaign_id": "free-pilot-v1",
                    "calls": 4,
                    "evaluated_responses": 3,
                    "passed_responses": 0,
                    "operational_errors": 1,
                    "unknown_usage_errors": 1,
                    "historical_http_code": "NOT_PRESERVED",
                },
                "pilot_quality_results_reused": False,
                "control_evidence_reusable": True,
                "quality_evidence_candidate_scoped": True,
                "future_holdout_calls": 84,
                "future_holdout_max_tokens": {"input": 172032, "output": 21504},
                "p00_primary_remaining_after_existing_usage": allocation[
                    "remaining_capacity_by_project"
                ]["p00"]["primary_remaining"],
                "p00_primary_token_capacity_after_existing_usage": {
                    "provider_ledger_input_tokens": allocation["remaining_capacity_by_project"][
                        "p00"
                    ]["primary_input_tokens_remaining"],
                    "logical_ledger_input_tokens": allocation["p00_primary_allocation"][
                        "input_tokens"
                    ]
                    - allocation["logical_ledger_usage"]["input_tokens"],
                    "output_tokens": allocation["remaining_capacity_by_project"]["p00"][
                        "primary_output_tokens_remaining"
                    ],
                },
                "c2_development_max_tokens": {"input": 73728, "output": 9216},
                "other_project_primary_remaining": {
                    name: values["primary_remaining"]
                    for name, values in allocation["remaining_capacity_by_project"].items()
                    if name != "p00"
                },
                "other_project_confirmations_protected": {
                    name: values["confirmation_protected"]
                    for name, values in allocation["remaining_capacity_by_project"].items()
                    if name != "p00"
                },
                "corrections_judges_canary_calls": 0,
                "review_status": {
                    "human": "PENDING",
                    "independent": "PENDING",
                    "dataset": "PENDING",
                    "rubric": "PENDING",
                    "promotion": "PENDING",
                },
                "stop_conditions": [
                    "quota or provider error",
                    "provenance mismatch",
                    "unknown or interrupted attempt",
                    "semantic failure (never replay the same trial)",
                    "36 new C2 attempts",
                ],
                "safe_start_command": None,
                "safe_resume_command": None,
                "execution_guidance": "BLOCKED_PENDING_CANDIDATE_FREEZE_AND_EXECUTION_GATES",
            },
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "evals" / "live-campaign.json")
    stage = parser.add_mutually_exclusive_group(required=True)
    stage.add_argument("--stage", choices=("pilot", "development", "holdout"))
    stage.add_argument("--resume", metavar="CAMPAIGN_ID")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and report reservations without provider access",
    )
    parser.add_argument(
        "--execute-free",
        action="store_true",
        help="explicitly run an authorized free-only chunk; requires LLM_MODE=live",
    )
    parser.add_argument("--campaign-id", help="immutable campaign ID for a new stage")
    parser.add_argument(
        "--max-trials", type=int, default=10, help="new trials in this chunk, at most ten"
    )
    args = parser.parse_args(argv)
    try:
        if args.execute_free:
            if (
                args.dry_run
                or os.getenv("LLM_MODE", "fake") != "live"
                or not 1 <= args.max_trials <= 10
            ):
                raise CampaignError(
                    "explicit live mode and one to ten trials required; dry-run cannot dispatch"
                )
            if args.config.resolve() != (ROOT / "evals/live-campaign.json").resolve():
                raise CampaignError("custom live config is not authorized")
            campaign = args.resume or args.campaign_id
            if not isinstance(campaign, str) or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", campaign
            ):
                raise CampaignError("valid campaign ID required")
            selected_stage = args.stage
            if args.resume:
                selected_stage = load_json(
                    ROOT / "artifacts/evals/live" / campaign / "manifest.json"
                )["stage"]
            if selected_stage not in {"pilot", "development", "holdout"}:
                raise CampaignError("invalid frozen stage")
            config = load_json(ROOT / "evals/live-campaign.json")
            manifest = load_json(ROOT / config["dataset_manifest"])
            cases = load_cases(ROOT / config["cases_path"], manifest)
            validate_config(config, cases)
            if not config["generation_enabled"]:
                raise CampaignError("generation remains disabled")
            sys.path.insert(0, str(ROOT))
            from scripts.campaign_execution import ExecutionBlocked, run_campaign
            from scripts.campaign_runtime import CampaignBlocked

            try:
                report, exit_code = run_campaign(
                    ROOT, config, cases, selected_stage, campaign, max_trials=args.max_trials
                )
            except (ExecutionBlocked, CampaignBlocked) as exc:
                print(json.dumps({"status": "INCOMPLETE", "reason": str(exc)}))
                return 2
            except Exception:  # noqa: BLE001 - Never print raw synthetic output or process exceptions.
                print(
                    json.dumps(
                        {
                            "status": "INCOMPLETE",
                            "reason": "campaign_execution_interrupted; inspect durable checkpoint",
                        }
                    )
                )
                return 2
            print(json.dumps(report, sort_keys=True, indent=2))
            return exit_code
        if args.resume is not None:
            if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}", args.resume):
                raise CampaignError("invalid campaign ID")
            ledger_path = ROOT / "artifacts" / "evals" / "live" / "ledger.sqlite"
            if not ledger_path.is_file():
                raise CampaignError("campaign ledger does not exist")
            ledger = CampaignLedger(
                ledger_path, project="p00", campaign_id=args.resume, read_only=True
            )
            trials = ledger.reserved_trials()
            if not trials:
                raise CampaignError("campaign has no recorded attempts")
            print(
                json.dumps(
                    {
                        "project": "p00",
                        "campaign_id": args.resume,
                        "mode": "dry-run" if args.dry_run else "resume-preflight",
                        "trials": trials,
                        "cumulative_usage": {
                            key: str(value) for key, value in ledger.totals().items()
                        },
                        "provider_accessed": False,
                        "credentials_read": False,
                        "generation_authorized": False,
                    },
                    sort_keys=True,
                )
            )
            return 0 if args.dry_run else 2
        config_path = args.config if args.config.is_absolute() else ROOT / args.config
        config = load_json(config_path)
        manifest_path = ROOT / config["dataset_manifest"]
        data_path = ROOT / config["cases_path"]
        manifest = load_json(manifest_path)
        cases = load_cases(data_path, manifest)
        validate_config(config, cases)
        if (
            args.stage == "development"
            and args.campaign_id is not None
            and args.campaign_id != "free-dev-c2r1"
        ):
            raise CampaignError("phase 028 allocates only free-dev-c2r1")
        allocation = applied_allocation(ROOT)
        summary = summarize(
            args.stage,
            cases,
            config,
            manifest,
            data_path,
            allocation=allocation,
            campaign_id=args.campaign_id,
        )
    except (CampaignError, KeyError, TypeError) as exc:
        print(
            json.dumps(
                {
                    "status": "INCOMPLETE",
                    "error": str(exc),
                    "generation_authorized": False,
                    "provider_accessed": False,
                    "credentials_read": False,
                },
                sort_keys=True,
            )
        )
        return 2
    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    print(
        json.dumps(
            {
                **summary,
                "status": "INCOMPLETE",
                "reason": "campaign execution requires --execute-free and LLM_MODE=live; human review remains pending",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
