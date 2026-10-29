from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts import campaign_execution as execution
from scripts.campaign_batch import run_chunk as real_chunk
from scripts.campaign_runtime import CampaignBlocked, CampaignLedger
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
        PROJECT / "agent/schemas/live-decision.json",
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
        ".planning/llm-live-readiness/phases/027-free-envelope-plus13/AUTHORIZATION.json",
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
    with pytest.raises(execution.ExecutionBlocked, match="critical_failure_requires_review"):
        run(campaign)
    assert FixtureClient.calls == previous
    assert first["chunk"]["reason"] == "critical_failure"
    assert first["slices"]["family"]["model_usage_identity"]["errors"]["tool_selection"] == 1


def test_prompt_change_rejects_resume_before_client_or_generation(campaign):
    project, _, _ = campaign
    run(campaign)
    (project / "agent/prompts/live-campaign.md").write_text("changed candidate prompt")
    with pytest.raises(execution.ExecutionBlocked, match="provenance_mismatch"):
        run(campaign)
    assert len(FixtureClient.calls) == 1


def test_provider_error_blocks_resume_before_client_initialization(campaign, monkeypatch):
    FixtureClient.response = {
        "status": "INCOMPLETE",
        "reason": "transport",
        "attempt_id": "b" * 32,
    }
    report, _ = run(campaign)
    assert report["chunk"]["reason"] == "provider_error"
    assert report["resume_command"] is None
    previous = list(FixtureClient.calls)

    def denied_init(self, project):
        pytest.fail("provider must not initialize after an unreconciled operational failure")

    monkeypatch.setattr(FixtureClient, "__init__", denied_init)
    with pytest.raises(execution.ExecutionBlocked, match="provider_failure_requires_review"):
        run(campaign)
    assert FixtureClient.calls == previous


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


def test_strict_payload_is_deterministic_and_fits_full_serialized_bound(campaign):
    project, *_ = campaign
    config = {"model": "openai/gpt-oss-20b"}
    prompt = (project / "agent/prompts/live-campaign.md").read_text(encoding="utf-8")
    first = execution.build_payload(project, prompt, "My concrete order has not arrived.", config)
    second = execution.build_payload(project, prompt, "My concrete order has not arrived.", config)
    assert first == second
    assert first["response_format"]["type"] == "json_schema"
    strict = first["response_format"]["json_schema"]
    assert strict["strict"] is True
    assert strict["schema"]["additionalProperties"] is False
    assert strict["schema"]["properties"]["decision"]["additionalProperties"] is False
    assert len(json.dumps(first, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) <= 2048


def test_payload_full_bound_rejects_oversized_serialized_messages(campaign):
    project, *_ = campaign
    with pytest.raises(execution.ExecutionBlocked, match="serialized_input_exceeds_reserved_bound"):
        execution.build_payload(
            project,
            (project / "agent/prompts/live-campaign.md").read_text(encoding="utf-8"),
            "x" * 3000,
            {"model": "openai/gpt-oss-20b"},
        )


def test_schema_change_is_part_of_frozen_fingerprint(campaign):
    project, *_ = campaign
    policy = project.parents[1] / "shared/policies/groq-free-campaign.json"
    before = execution.fingerprint(project, policy)
    schema_path = project / "agent/schemas/live-decision.json"
    schema_path.write_text(schema_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    after = execution.fingerprint(project, policy)
    schema_key = "projects/p00/agent/schemas/live-decision.json"
    assert before[schema_key] != after[schema_key]


def test_provider_diagnostics_are_typed_and_sanitized():
    result = execution.sanitized_diagnostic(
        {
            "http_status": 400,
            "provider_error_code": "invalid_request_error",
            "reason": "request_schema",
            "error_message": "secret raw provider content",
            "headers": {"authorization": "never-log-this"},
        },
        evaluated=False,
    )
    assert result == {
        "http_status": 400,
        "provider_error_code": "invalid_request_error",
        "diagnostic_class": "request_schema",
    }
    assert "secret" not in json.dumps(result)
    assert "authorization" not in json.dumps(result)


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
    monkeypatch.setattr(execution, "verify_applied_policy_binding", lambda *_: "a" * 32)
    with pytest.raises(execution.ExecutionBlocked, match="provider_usage_proof_unavailable"):
        project, config, cases = campaign
        execution.run_campaign(
            project,
            config,
            cases,
            "development",
            "free-dev-c2r1",
            client_factory=FixtureClient,
            revision="a" * 40,
            max_trials=1,
        )


@pytest.mark.parametrize(
    "stage,name",
    [
        ("development", "free-dev-c1"),
        ("development", "free-dev-c2"),
        ("development", "renamed-campaign"),
        ("pilot", "free-dev-c1"),
        ("holdout", "free-dev-c2r1"),
    ],
)
def test_live_scope_rejects_new_ids_and_stages_before_side_effects(tmp_path, stage, name):
    reason = (
        "immutable_campaign_provenance_mismatch"
        if stage == "development" and name in {"free-dev-c1", "free-dev-c2"}
        else "phase_028_live_scope_not_allocated"
    )
    with pytest.raises(execution.ExecutionBlocked, match=reason):
        execution.run_campaign(tmp_path, {}, [], stage, name)
    assert list(tmp_path.iterdir()) == []


def test_development_cannot_exceed_36_attempts_across_chunks_and_resume(campaign):
    project, config, cases = campaign
    for _ in range(5):
        execution.run_campaign(
            project,
            config,
            cases,
            "development",
            "free-dev-c2r1",
            client_factory=FixtureClient,
            revision="a" * 40,
            max_trials=10,
        )
    assert len(FixtureClient.calls) == len(set(FixtureClient.calls)) == 36


def test_primary_ceiling_counts_historical_pilot_once_and_protects_confirmation(tmp_path):
    path = tmp_path / "ledger.sqlite"
    caps = vars(execution.PRIMARY_CAPS)
    for campaign_id, count in (("pilot", 4), ("primary", 145)):
        ledger = CampaignLedger(path, project="p00", campaign_id=campaign_id)
        for index in range(count):
            ledger.reserve(
                case_id=str(index),
                trial=1,
                input_tokens=1,
                output_tokens=1,
                estimated_cost_usd=Decimal(0),
                caps=caps,
            )
    assert ledger.totals()["requests"] == 149
    assert caps["requests"] == 149
    assert caps["input_tokens"] == 305152
    assert caps["output_tokens"] == 38144
    assert caps["estimated_cost_usd"] == Decimal("0.0343296")
    with pytest.raises(CampaignBlocked, match="cumulative reservation cap"):
        ledger.reserve(
            case_id="extra",
            trial=1,
            input_tokens=1,
            output_tokens=1,
            estimated_cost_usd=Decimal(0),
            caps=caps,
        )
    policy = load_json(LAB / "shared/policies/groq-free-campaign.json")["projects"]["p00"]
    assert policy["requests"] - caps["requests"] - 10 == 60
    assert policy["input_tokens"] - caps["input_tokens"] - 20480 == 122880
    assert policy["output_tokens"] - caps["output_tokens"] - 2560 == 15360
    assert Decimal(policy["estimated_cost_usd"]) - caps["estimated_cost_usd"] - Decimal(
        "0.002304"
    ) == Decimal("0.013824")


def test_applied_policy_binding_checks_policy_registry_and_provider_uuid(tmp_path):
    lab = tmp_path / "lab"
    runtime = lab / ".runtime/llm-live-readiness"
    provider = lab / "projects/p00/artifacts/evals/live/provider-usage.sqlite"
    runtime.mkdir(parents=True)
    provider.parent.mkdir(parents=True)
    policy = load_json(LAB / "shared/policies/groq-free-campaign.json")
    identity = "a" * 32
    registry = {"policy_sha256": "old-policy", "projects": {"p00": identity}}
    (runtime / "ledger-references.json").write_text(json.dumps(registry))
    with closing(sqlite3.connect(provider)) as db:
        db.execute("CREATE TABLE identity(identity TEXT PRIMARY KEY)")
        db.execute("INSERT INTO identity VALUES(?)", (identity,))
        db.commit()
    with pytest.raises(execution.ExecutionBlocked, match="applied_policy_registry_mismatch"):
        execution.verify_applied_policy_binding(lab, policy)
    registry["policy_sha256"] = hashlib.sha256(
        json.dumps(policy, sort_keys=True).encode()
    ).hexdigest()
    (runtime / "ledger-references.json").write_text(json.dumps(registry))
    with closing(sqlite3.connect(provider)) as db:
        db.execute("UPDATE identity SET identity=?", ("b" * 32,))
        db.commit()
    with pytest.raises(execution.ExecutionBlocked, match="p00_provider_ledger_identity_mismatch"):
        execution.verify_applied_policy_binding(lab, policy)
    with closing(sqlite3.connect(provider)) as db:
        db.execute("UPDATE identity SET identity=?", (identity,))
        db.commit()
    assert execution.verify_applied_policy_binding(lab, policy) == identity
    (runtime / "policy-migration.pending").write_text("{}")
    with pytest.raises(execution.ExecutionBlocked, match="policy_migration_pending"):
        execution.verify_applied_policy_binding(lab, policy)


def test_pending_migration_preflight_denies_before_live_client_or_campaign_files(campaign):
    project, config, cases = campaign

    class LiveProbe(FixtureClient):
        provenance = "live"
        initialized = 0

        def __init__(self, project):
            type(self).initialized += 1
            super().__init__(project)

    with pytest.raises(execution.ExecutionBlocked, match="root_account_binding_unavailable"):
        execution.run_campaign(
            project,
            config,
            cases,
            "development",
            "free-dev-c2r1",
            client_factory=LiveProbe,
            revision="a" * 40,
            max_trials=1,
        )
    assert LiveProbe.initialized == 0
    assert not (project / "artifacts/evals/live/free-dev-c2r1").exists()
    assert FixtureClient.calls == []


@pytest.mark.parametrize(
    "change", ["dirty", "staged", "untracked_schema", "untracked_script", "root_dirty"]
)
def test_candidate_requires_committed_schema_and_all_fingerprinted_sources(tmp_path, change):
    lab = tmp_path / "lab"
    project = lab / "projects/p00"
    schema = project / "agent/schemas/live-decision.json"
    root_source = lab / "guard.py"
    schema.parent.mkdir(parents=True)
    root_source.write_text("guard", encoding="utf-8")
    schema.write_text("{}", encoding="utf-8")

    def git(owner, *args):
        return subprocess.run(
            ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", *args],
            cwd=owner,
            check=True,
            capture_output=True,
            text=True,
        )

    for owner, path in ((lab, "guard.py"), (project, "agent/schemas/live-decision.json")):
        git(owner, "init")
        git(owner, "add", path)
        git(owner, "commit", "-m", "test(fixture): freeze sources")
    sources = {"projects/p00/agent/schemas/live-decision.json": "", "guard.py": ""}
    assert (
        execution.require_committed_sources(project, sources)
        == git(project, "rev-parse", "HEAD").stdout.strip()
    )
    if change in {"dirty", "staged"}:
        schema.write_text("changed", encoding="utf-8")
        if change == "staged":
            git(project, "add", "agent/schemas/live-decision.json")
    elif change == "untracked_schema":
        git(project, "rm", "--cached", "agent/schemas/live-decision.json")
        git(project, "commit", "-m", "test(fixture): remove tracked schema")
    elif change == "untracked_script":
        extra = project / "scripts/new.py"
        extra.parent.mkdir()
        extra.write_text("pass", encoding="utf-8")
        sources["projects/p00/scripts/new.py"] = ""
    else:
        root_source.write_text("changed guard", encoding="utf-8")
    with pytest.raises(execution.ExecutionBlocked, match="uncommitted_source"):
        execution.require_committed_sources(project, sources)


def test_schema_change_rejects_resume_without_reexecuting(campaign):
    project, _, _ = campaign
    run(campaign)
    schema = project / "agent/schemas/live-decision.json"
    schema.write_text(schema.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(execution.ExecutionBlocked, match="provenance_mismatch"):
        run(campaign)
    assert len(FixtureClient.calls) == 1


def test_explicit_revision_cannot_bypass_live_source_check(campaign, monkeypatch):
    project, config, cases = campaign

    def reject(*args):
        raise execution.ExecutionBlocked("candidate_has_uncommitted_source_changes")

    monkeypatch.setattr(execution, "require_committed_sources", reject)
    with pytest.raises(execution.ExecutionBlocked, match="uncommitted_source"):
        execution.run_campaign(
            project,
            config,
            cases,
            "development",
            "free-dev-c2r1",
            revision="a" * 40,
        )


def test_builder_rejects_payload_that_only_fits_without_transport_framing(campaign):
    project, _, _ = campaign
    with pytest.raises(execution.ExecutionBlocked, match="serialized_input_exceeds"):
        execution.build_payload(project, "policy", "x" * 1000, {"model": "openai/gpt-oss-20b"})


def test_complete_input_bounds_match_actual_transport_for_development_cases(campaign):
    project, config, cases = campaign
    prompt = (project / "agent/prompts/live-campaign.md").read_text(encoding="utf-8").strip()
    selected = [case for case in cases if case["split"] == "development"]
    payloads = [
        execution.build_payload(project, prompt, case["input"], config) for case in selected
    ]
    script = (
        "import sys,json; sys.path.insert(0,sys.argv[1]); "
        "from live_provider_transport import encode_payload; "
        "caps=dict(input_tokens_per_call=2048,output_tokens_per_call=256); "
        "print(json.dumps([encode_payload(p,caps)[1] for p in json.load(sys.stdin)]))"
    )
    result = subprocess.run(
        [sys.executable, "-S", "-c", script, str(LAB / "scripts/harness")],
        input=json.dumps(payloads),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        env={k: v for k, v in os.environ.items() if not k.startswith("GROQ_API_KEY")},
    )
    bounds = json.loads(result.stdout)
    assert len(bounds) == 12
    assert max(bounds) <= 2048
    assert bounds == [execution.payload_input_bound(payload) for payload in payloads]


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


@pytest.mark.skipif(os.name != "nt", reason="Windows DACL regression")
def test_private_review_removes_existing_explicit_grants(campaign):
    project, _, _ = campaign
    store = execution.ReviewStore(project)
    for path, grant in (
        (store.path.parent, "*S-1-5-32-545:(OI)(CI)R"),
        (store.path, "*S-1-5-32-545:R"),
    ):
        result = subprocess.run(
            ["icacls", str(path), "/grant", grant], capture_output=True, check=False
        )
        assert result.returncode == 0
    with pytest.raises(execution.ExecutionBlocked, match="private_review_acl_unavailable"):
        execution.private_directory(store.path.parent, project, verify_only=True)
    execution.private_directory(store.path.parent, project)
    execution.private_directory(store.path.parent, project, verify_only=True)
