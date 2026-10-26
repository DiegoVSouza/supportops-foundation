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


def test_dry_run_works_without_site_packages_or_provider_imports() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            str(ROOT / "scripts/run_live_campaign.py"),
            "--stage",
            "pilot",
            "--dry-run",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["cases"] == 6
    assert report["logical_trials"] == 6
    assert report["max_provider_calls"] == 6
    assert report["generation_authorized"] is False
    assert report["provider_accessed"] is False
    assert report["credentials_read"] is False
    assert "authorization.dataset_review" in report["blockers"]
    assert report["planned_reservations"]["primary_campaign_max_calls"] == 120
    assert report["planned_reservations"]["confirmation_max_calls"] == 60
    assert report["planned_reservations"]["all_stages_max_calls_if_additive"] == 186
    assert report["limits"]["cumulative"]["max_requests"] == 186
    assert report["limits"]["cumulative"]["max_input_tokens"] == 380928
    assert report["limits"]["cumulative"]["max_output_tokens"] == 47616
    assert report["limits"]["cumulative"]["authorized_paid_spend_usd"] == "0.00"


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


def test_generation_is_incomplete_without_creating_a_provider_client(capsys) -> None:
    from scripts.run_live_campaign import main

    assert main(["--stage", "pilot"]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "INCOMPLETE"
    assert "requires --execute-free and LLM_MODE=live" in report["reason"]


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
