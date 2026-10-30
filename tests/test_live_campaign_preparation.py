import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_live_campaign import (
    CampaignError,
    load_cases,
    load_json,
    validate_cases,
    validate_prediction,
)

CONFIG = load_json(ROOT / "evals/live-campaign.json")
MANIFEST = load_json(ROOT / CONFIG["dataset_manifest"])
CASES = load_cases(ROOT / CONFIG["cases_path"], MANIFEST)


def test_live_dataset_has_frozen_split_language_and_family_counts() -> None:
    assert len(CASES) == 40
    assert sum(case["split"] == "development" for case in CASES) == 12
    assert sum(case["split"] == "holdout" for case in CASES) == 28
    assert sum(case["language"] == "en" for case in CASES) == 24
    assert sum(case["language"] == "pt-BR" for case in CASES) == 16
    assert {case["family"] for case in CASES} == set(MANIFEST["families"])


def test_dataset_rejects_duplicate_semantic_input() -> None:
    duplicate = copy.deepcopy(CASES)
    duplicate[1]["input"] = duplicate[0]["input"]
    with pytest.raises(CampaignError, match="unique"):
        validate_cases(duplicate, MANIFEST)


def test_dataset_rejects_related_scenario_split_leakage() -> None:
    leaked = copy.deepcopy(CASES)
    leaked[3]["source_group"] = leaked[0]["source_group"]
    with pytest.raises(CampaignError, match="crosses splits"):
        validate_cases(leaked, MANIFEST)


@pytest.mark.parametrize("case", [case for case in CASES if "negative_grader_probe" in case])
def test_code_first_grader_rejects_deliberately_bad_candidates(case) -> None:
    candidate = case["negative_grader_probe"]
    if isinstance(candidate, str):
        with pytest.raises(json.JSONDecodeError):
            json.loads(candidate)
        return
    assert validate_prediction(case, {"decision": candidate, "tool": candidate.get("tool")})


def test_code_first_grader_rejects_wrong_decision_tool_and_refund() -> None:
    case = next(item for item in CASES if item["family"] == "read_only_tool_selection")
    bad = {
        "decision": {
            "category": "billing",
            "action": "refund",
            "escalate": False,
            "rationale": "unverified",
        },
        "tool": "issue_refund",
    }
    errors = validate_prediction(case, bad)
    assert "wrong action" in errors
    assert "wrong tool selection" in errors
    assert "forbidden side-effect tool" in errors


def test_code_first_grader_rejects_truncated_json() -> None:
    with pytest.raises(json.JSONDecodeError):
        json.loads('{"decision":{"category":"billing",')


def test_dry_run_fails_closed_on_uncommitted_candidate_sources(monkeypatch, capsys) -> None:
    from scripts import campaign_execution, run_live_campaign

    def dirty_sources(*args):
        raise RuntimeError("synthetic dirty source")

    monkeypatch.setattr(campaign_execution, "require_committed_sources", dirty_sources)
    assert run_live_campaign.main(["--stage", "pilot", "--dry-run"]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "INCOMPLETE"
    assert report["error"] == "candidate source provenance is not committed and clean"
    assert report["generation_authorized"] is False
    assert report["provider_accessed"] is False
    assert report["credentials_read"] is False


@pytest.mark.parametrize(
    ("stage", "case_count", "trial_count", "calls"),
    [("development", 12, 3, 36), ("holdout", 28, 3, 84)],
)
def test_dry_run_reports_stage_reservations(stage, case_count, trial_count, calls) -> None:
    from scripts.run_live_campaign import summarize

    report = summarize(stage, CASES, CONFIG, MANIFEST, ROOT / CONFIG["cases_path"])
    assert report["cases"] == case_count
    assert report["trials_per_case"] == trial_count
    assert report["max_provider_calls"] == calls
    assert report["generation_authorized"] is False
    plan = report["planned_reservations"]
    assert plan["confirmation_max_input_tokens"] == 20 * 3 * 2048
    assert plan["confirmation_max_output_tokens"] == 20 * 3 * 256


def test_applied_dry_run_allocation_reconciles_ledgers_without_reusing_history(monkeypatch) -> None:
    from scripts import campaign_execution
    from scripts.run_live_campaign import applied_allocation, summarize

    monkeypatch.setattr(campaign_execution, "require_committed_sources", lambda *_: "candidate")
    allocation = applied_allocation(ROOT)
    report = summarize(
        "development",
        CASES,
        CONFIG,
        MANIFEST,
        ROOT / CONFIG["cases_path"],
        allocation=allocation,
        campaign_id="free-dev-c2r1",
    )
    assert report["candidate"]["policy_registry_sha256_matches"] is True
    assert report["planned_reservations"]["baseline_all_stages_max_calls_if_additive"] == 186
    assert report["planned_reservations"]["all_stages_max_calls_if_additive"] == 209
    assert report["limits"]["cumulative"]["max_requests"] == 209
    assert report["limits"]["cumulative"]["max_input_tokens"] == 428032
    assert report["limits"]["cumulative"]["max_output_tokens"] == 53504
    assert report["limits"]["cumulative"]["authorized_paid_spend_usd"] == "0.00"
    assert report["candidate"]["p00_primary_allocation"]["requests"] == 149
    assert report["candidate"]["p00_confirmation_protected"]["requests"] == 60
    for name, primary, operating in (
        ("p02", 246, 4),
        ("p03", 96, 4),
        ("p04", 558, 6),
        ("p05", 1464, 8),
    ):
        assert allocation["other_operation_allocations"][name]["total"] == operating
        assert allocation["remaining_capacity_by_project"][name]["primary_total"] == primary
        assert allocation["remaining_capacity_by_project"][name]["primary_consumed"] == 0
    p01 = allocation["p01_operation_allocation"]
    assert p01["total"] == 12 and p01["used"] == 4
    assert p01["logical_reserved_calls_retained"] == 12
    assert p01["logical_unreserved_calls"] == 0
    assert p01["further_execution_authorized"] is False
    p04 = allocation["other_operation_allocations"]["p04"]
    assert p04["used"] == 3
    assert p04["logical_reserved_calls_retained"] == 6
    assert p04["logical_unreserved_calls"] == 0
    assert p04["further_execution_authorized"] is False
    accounted = int(allocation["provider_ledger_usage"]["total_accounted"]["requests"])
    assert report["candidate"]["global_remaining"] == {
        "requests": 4141 - accounted,
        "primary_requests": 3257
        - accounted
        + allocation["p00_operation_allocation"]["used"]
        + allocation["p01_operation_allocation"]["used"]
        + sum(row["used"] for row in allocation["other_operation_allocations"].values()),
        "protected_confirmation_requests": 840,
    }
    assert (
        report["candidate"]["logical_ledger_usage"]["requests"]
        == allocation["provider_ledger_usage"]["p00"]["requests"]
        - allocation["p00_operation_allocation"]["used"]
    )
    assert report["candidate"]["logical_ledger_usage"]["unknown_reservations"] == [
        {"input_tokens": 2048, "output_tokens": 256}
    ]
    assert report["candidate"]["provider_ledger_usage"]["unknown_transport_reservations"] == [
        {
            "attempt_id": allocation["provider_ledger_usage"]["unknown_transport_reservations"][0][
                "attempt_id"
            ],
            "input_tokens": 1475,
            "output_tokens": 256,
        }
    ]
    assert report["c2_scope"]["maximum_new_calls"] == 36
    assert report["c2_scope"]["safe_start_command"] is None
    assert report["c2_scope"]["safe_resume_command"] is None
    assert (
        report["c2_scope"]["execution_guidance"]
        == "BLOCKED_PENDING_CANDIDATE_FREEZE_AND_EXECUTION_GATES"
    )
    assert report["c2_scope"]["future_holdout_calls"] == 84
    assert report["c2_scope"]["batches_maximum"] == [10, 10, 10, 6]
    assert report["c2_scope"]["previous_candidate_results_reused"] is False
    assert (
        report["c2_scope"]["previous_candidate_commit"]
        == "b42a198246274db5f7feb17a247ef1fe90e662e6"
    )
    assert report["c2_scope"]["previous_candidate_unexecuted_trials"] == 24
    assert report["c2_scope"]["previous_pilot"] == {
        "campaign_id": "free-pilot-v1",
        "calls": 4,
        "evaluated_responses": 3,
        "passed_responses": 0,
        "operational_errors": 1,
        "unknown_usage_errors": 1,
        "historical_http_code": "NOT_PRESERVED",
    }
    p00_usage = allocation["provider_ledger_usage"]["p00"]
    assert report["c2_scope"]["p00_primary_remaining_after_existing_usage"] == (
        149 - p00_usage["requests"] + allocation["p00_operation_allocation"]["used"]
    )
    assert report["c2_scope"]["p00_primary_token_capacity_after_existing_usage"] == {
        "provider_ledger_input_tokens": 305152
        - p00_usage["input_tokens"]
        + allocation["p00_operation_allocation"]["input_tokens_used"],
        "logical_ledger_input_tokens": 305152 - allocation["logical_ledger_usage"]["input_tokens"],
        "output_tokens": 38144
        - p00_usage["output_tokens"]
        + allocation["p00_operation_allocation"]["output_tokens_used"],
    }
    assert report["c2_scope"]["c2_development_max_tokens"] == {
        "input": 73728,
        "output": 9216,
    }
    assert report["c2_scope"]["future_holdout_max_tokens"] == {
        "input": 172032,
        "output": 21504,
    }
    assert report["c2_scope"]["other_project_primary_remaining"] == {
        "p01": 744,
        "p02": 246,
        "p03": 96,
        "p04": 558,
        "p05": 1464,
    }
    assert report["c2_scope"]["other_project_confirmations_protected"] == {
        "p01": 240,
        "p02": 60,
        "p03": 60,
        "p04": 180,
        "p05": 240,
    }
    assert report["candidate"]["provider_accessed"] is False
    assert report["candidate"]["credentials_read"] is False
    assert "authorization.dataset_review" in report["blockers"]
    assert report["campaign_id"] == "free-dev-c2r1"
    assert report["candidate"]["billing"].startswith("UNKNOWN")


def test_dry_run_rejects_unallocated_development_campaign_id() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            str(ROOT / "scripts/run_live_campaign.py"),
            "--stage",
            "development",
            "--campaign-id",
            "invented-campaign",
            "--dry-run",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["error"] == "phase 028 allocates only free-dev-c2r1"
    assert report["provider_accessed"] is False
    assert report["credentials_read"] is False


def test_generation_is_incomplete_without_creating_a_provider_client(capsys, monkeypatch) -> None:
    from scripts import campaign_execution
    from scripts.run_live_campaign import main

    def dirty_sources(*args):
        raise RuntimeError("synthetic dirty source")

    monkeypatch.setattr(campaign_execution, "require_committed_sources", dirty_sources)
    assert main(["--stage", "pilot"]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "INCOMPLETE"
    assert report["error"] == "candidate source provenance is not committed and clean"
    assert report["provider_accessed"] is False
    assert report["credentials_read"] is False


def test_clean_candidate_still_requires_explicit_generation_opt_in(capsys, monkeypatch):
    from scripts import campaign_execution
    from scripts.run_live_campaign import main

    monkeypatch.setattr(campaign_execution, "require_committed_sources", lambda *args: "a" * 40)
    assert main(["--stage", "pilot"]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "INCOMPLETE"
    assert "--execute-free" in report["reason"]
    assert report["generation_authorized"] is False
    assert report["provider_accessed"] is False
    assert report["credentials_read"] is False


def test_resume_dry_run_reports_uncertain_attempt_without_provider_access(
    tmp_path, monkeypatch, capsys
):
    from decimal import Decimal

    from scripts import run_live_campaign
    from scripts.campaign_runtime import CampaignLedger

    campaign_id = "resume-test"
    monkeypatch.setattr(run_live_campaign, "ROOT", tmp_path)
    ledger = CampaignLedger(
        tmp_path / "artifacts/evals/live/ledger.sqlite",
        project="p00",
        campaign_id=campaign_id,
    )
    ledger.reserve(
        case_id="synthetic-1",
        trial=1,
        input_tokens=10,
        output_tokens=20,
        estimated_cost_usd=Decimal("0.001"),
        caps={
            "requests": 1,
            "input_tokens": 10,
            "output_tokens": 20,
            "estimated_cost_usd": Decimal("0.001"),
        },
    )
    last_modified = ledger.path.stat().st_mtime_ns

    assert run_live_campaign.main(["--resume", campaign_id, "--dry-run"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["trials"][0]["event"] == "reserved"
    assert report["provider_accessed"] is False
    assert report["credentials_read"] is False
    assert ledger.path.stat().st_mtime_ns == last_modified
