from __future__ import annotations

import copy
import json
import shutil
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from typing import ClassVar

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts import campaign_execution as execution
from scripts.campaign_batch import run_chunk as real_chunk
from scripts.run_live_campaign import load_cases, load_json

PROJECT = Path(__file__).resolve().parents[2]
LAB = PROJECT.parents[1]


class FixtureClient:
    provenance = "fixture"
    calls: ClassVar[list[tuple[str, int]]] = []
    response = None
    deny = False

    def __init__(self, project):
        self.last_stop = None

    def request(self, envelope, operation):
        if operation == "preview":
            if self.deny:
                self.last_stop = "free_token_minute_checkpoint"
                return {"status": "INCOMPLETE", "reason": self.last_stop}
            return {"status": "approved"}
        self.calls.append((envelope["case_id"], envelope["trial"]))
        return copy.deepcopy(self.response)

    def close(self):
        pass


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    project = tmp_path / "lab/projects/p00"
    paths = [
        *PROJECT.glob("scripts/*.py"),
        *PROJECT.glob("supportops_foundation/**/*.py"),
        PROJECT / "agent/prompts/live-campaign.md",
        PROJECT / "evals/live-campaign.json",
        PROJECT / "evals/live-execution.json",
        PROJECT / "evals/datasets/live-v1/cases.jsonl",
        PROJECT / "evals/datasets/live-v1/manifest.json",
        PROJECT / "evals/rubrics/live-v1/rubric.md",
        PROJECT / "uv.lock",
        PROJECT / "pyproject.toml",
    ]
    for path in paths:
        target = project / path.relative_to(PROJECT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    for name in (
        "shared/policies/groq-free-campaign.json",
        "scripts/harness/live_free_account.py",
        "scripts/harness/live_provider_transport.py",
    ):
        target = project.parents[1] / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LAB / name, target)
    config = load_json(project / "evals/live-campaign.json")
    manifest = load_json(project / config["dataset_manifest"])
    cases = load_cases(project / config["cases_path"], manifest)
    config["pilot_case_ids"] = [cases[0]["case_id"]]
    FixtureClient.calls, FixtureClient.deny = [], False
    FixtureClient.response = {
        "status": "ok",
        "model": "openai/gpt-oss-20b",
        "attempt_id": "a" * 32,
        "usage": {"input_tokens": 40, "output_tokens": 25},
        "finish_reason": "stop",
        "content": json.dumps(
            {
                "decision": {
                    "category": "billing",
                    "action": "answer",
                    "escalate": False,
                    "rationale": "PRIVATE_REVIEW_ONLY",
                },
                "tool": "lookup_invoice",
            }
        ),
    }

    def no_wait(*args, **kwargs):
        kwargs["min_interval_seconds"] = 0
        return real_chunk(*args, **kwargs)

    monkeypatch.setattr(execution, "run_chunk", no_wait)
    return project, config, cases


def run(campaign, **kwargs):
    project, config, cases = campaign
    return execution.run_campaign(
        project,
        config,
        cases,
        "pilot",
        "fixture-campaign",
        client_factory=FixtureClient,
        revision="a" * 40,
        **kwargs,
    )


def test_binding_persists_private_answer_and_sanitized_receipts_without_claiming_live(campaign):
    project, _, _ = campaign
    report, code = run(campaign)
    assert code == 2 and report["real_model_trials"] == 0
    assert report["recorded_trials"] == 1 and report["passed_trials"] == 1
    assert report["human_review_status"] == "PENDING" and report["promotion_status"] == "INCOMPLETE"
    with closing(sqlite3.connect(project / ".runtime/llm-review/answers.sqlite")) as db:
        assert (
            "PRIVATE_REVIEW_ONLY"
            in db.execute("SELECT assistant_content FROM answers").fetchone()[0]
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("DELETE FROM answers")
    for path in (project / "artifacts/evals/live/fixture-campaign").iterdir():
        assert "PRIVATE_REVIEW_ONLY" not in path.read_text()
    row = json.loads((project / "artifacts/evals/live/fixture-campaign/trials.jsonl").read_text())
    assert row["prediction"]["rationale_present"] is True


def test_semantic_failure_is_preserved_and_skipped_on_resume(campaign):
    FixtureClient.response["content"] = json.dumps(
        {
            "decision": {
                "category": "billing",
                "action": "refund",
                "escalate": False,
                "rationale": "PRIVATE_REVIEW_ONLY",
            },
            "tool": "issue_refund",
        }
    )
    first, _ = run(campaign)
    assert first["passed_trials"] == 0 and first["critical_failures"] == 1
    previous = list(FixtureClient.calls)
    second, _ = run(campaign)
    assert FixtureClient.calls == previous
    assert second["chunk"]["skipped"] == 1
    assert second["slices"]["family"]["model_usage_identity"]["errors"]["tool_selection"] == 1


def test_prompt_change_rejects_resume_before_client_or_generation(campaign):
    project, _, _ = campaign
    run(campaign)
    (project / "agent/prompts/live-campaign.md").write_text("changed candidate prompt")
    with pytest.raises(execution.ExecutionBlocked, match="provenance_mismatch"):
        run(campaign)
    assert len(FixtureClient.calls) == 1


def test_account_denial_precedes_local_reservation(campaign):
    FixtureClient.deny = True
    report, code = run(campaign)
    assert code == 2 and report["chunk"]["attempted"] == 0
    assert report["provider_stop"] == "free_token_minute_checkpoint"
    assert FixtureClient.calls == []


def test_malformed_nested_schema_is_terminal_not_an_uncertain_retry(campaign):
    FixtureClient.response["content"] = json.dumps(
        {
            "decision": {
                "category": [],
                "action": {},
                "escalate": False,
                "rationale": "PRIVATE_REVIEW_ONLY",
            },
            "tool": None,
        }
    )
    report, _ = run(campaign)
    assert report["recorded_trials"] == 1 and report["passed_trials"] == 0
    assert report["errors"] == {"output_schema": 1}
    run(campaign)
    assert len(FixtureClient.calls) == 1


def test_tampering_result_to_pass_cannot_override_immutable_ledger(campaign):
    project, _, _ = campaign
    FixtureClient.response["content"] = "invalid json"
    run(campaign)
    path = project / "artifacts/evals/live/fixture-campaign/trials.jsonl"
    row = json.loads(path.read_text())
    row.update(passed=True, outcome="passed")
    path.write_text(json.dumps(row) + "\n")
    with pytest.raises(execution.ExecutionBlocked, match="ledger_outcome_mismatch"):
        run(campaign)


def test_unverifiable_live_claim_cannot_count_fixture_as_provider_evidence(campaign, monkeypatch):
    monkeypatch.setattr(FixtureClient, "provenance", "live")
    with pytest.raises(execution.ExecutionBlocked, match="provider_usage_proof_unavailable"):
        run(campaign)


def test_three_trial_case_interval_does_not_pool_correlated_trials(campaign):
    _, _, cases = campaign
    selected = cases[:2]
    rows = []
    for case_index, case in enumerate(selected):
        for trial in range(1, 4):
            passed = not (case_index == 1 and trial == 3)
            rows.append(
                {
                    "case_id": case["case_id"],
                    "trial": trial,
                    "family": case["family"],
                    "language": case["language"],
                    "domain": case["expected"]["category"],
                    "model_evaluated": True,
                    "passed": passed,
                    "error_classes": [] if passed else ["classification"],
                    "provenance": "fixture",
                }
            )
    report = execution.report_trials(rows, selected, 3)
    assert report["passed_trials"] == 5 and report["unique_cases_all_three_pass"] == 1
    assert report["unique_cases_with_three_model_results"] == 2
    assert report["all_three_wilson95"] == pytest.approx([0.0945312, 0.9054688], abs=1e-6)
    with pytest.raises(execution.ExecutionBlocked, match="duplicate_trial_artifact"):
        execution.report_trials(rows + [rows[0]], selected, 3)


def test_incomplete_cases_and_operational_errors_are_separate_denominators(campaign):
    _, _, cases = campaign
    case = cases[0]
    row = {
        "case_id": case["case_id"],
        "trial": 1,
        "family": case["family"],
        "language": case["language"],
        "domain": case["expected"]["category"],
        "model_evaluated": False,
        "passed": False,
        "error_classes": ["quota"],
        "provenance": "fixture",
    }
    report = execution.report_trials([row], [case], 3)
    assert report["operational_failures"] == 1 and report["model_evaluated_trials"] == 0
    assert report["all_three_wilson95"] is None and report["planned_trials"] == 3


def test_live_environment_alone_cannot_dispatch(monkeypatch, capsys):
    from scripts.run_live_campaign import main

    monkeypatch.setenv("LLM_MODE", "live")

    def forbidden(_):
        pytest.fail("provider must not initialize without explicit free opt-in")

    monkeypatch.setattr(execution, "ProviderClient", forbidden)
    assert main(["--stage", "pilot"]) == 2
    assert json.loads(capsys.readouterr().out)["provider_accessed"] is False


def test_free_flag_without_live_mode_stops_before_provider(monkeypatch, capsys):
    from scripts.run_live_campaign import main

    monkeypatch.setenv("LLM_MODE", "fake")
    assert main(["--stage", "pilot", "--campaign-id", "blocked-test", "--execute-free"]) == 2
    assert "explicit live mode" in json.loads(capsys.readouterr().out)["error"]


def test_provider_subprocess_is_utf8_and_inherits_no_provider_keys(campaign, monkeypatch):
    project, _, _ = campaign
    worker = project.parents[1] / "scripts/harness/live_provider_transport.py"
    worker.write_text(
        """import json, os, sys
print(json.dumps({"status":"ready","protocol_version":1,"encoding":sys.stdout.encoding,"provider_keys_inherited":any(name.startswith("GROQ_API_KEY") for name in os.environ)}), flush=True)
for line in sys.stdin:
    json.loads(line)
    print(json.dumps({"status":"ok","content":"ação de faturação"},ensure_ascii=False),flush=True)
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("GROQ_API_KEY_1", "synthetic-not-inherited")
    client = execution.ProviderClient(project)
    try:
        assert client.ready["encoding"].lower().replace("-", "") == "utf8"
        assert client.ready["provider_keys_inherited"] is False
        assert client.request({}, "preview")["content"] == "ação de faturação"
    finally:
        client.close()
