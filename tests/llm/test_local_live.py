import contextlib
import hashlib
import json

import pytest

local_live = pytest.importorskip(
    "scripts.local_live",
    reason=(
        "lab integration test: scripts/local_live.py imports live_free_account from the ai-engineer-lab "
        "scripts/harness directory, which is absent outside the lab"
    ),
    exc_type=ImportError,
)
LocalLiveBlocked, run_operation = local_live.LocalLiveBlocked, local_live.run_operation


@pytest.fixture
def operation(tmp_path, monkeypatch):
    project = tmp_path / "lab/projects/p00"
    lab = project.parents[1]
    for folder in (
        project / "evals",
        project / "agent/prompts",
        lab / "shared/policies",
        lab / ".runtime/llm-live-readiness",
    ):
        folder.mkdir(parents=True, exist_ok=True)
    policy = {
        "projects": {"p00": {"requests": 219}},
        "authorized_paid_spend_usd": "0.00",
        "model": "fixture",
    }
    digest = hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest()
    (lab / "shared/policies/groq-free-campaign.json").write_text(json.dumps(policy))
    (lab / ".runtime/llm-live-readiness/ledger-references.json").write_text(
        json.dumps({"policy_sha256": digest})
    )
    config = {
        "enabled": True,
        "synthetic_only": True,
        "authorized_paid_spend_usd": "0.00",
        "campaign_id": "local-live-operation-v1",
        "max_calls": 10,
        "preexisting_p00_calls": 65,
        "protected_holdout_calls": 84,
        "protected_confirmation_calls": 60,
        "policy_sha256": digest,
    }
    (project / "evals/local-live-operation.json").write_text(json.dumps(config))
    (project / "agent/prompts/live-campaign.md").write_text("fixture")
    monkeypatch.setattr(local_live, "build_payload", lambda *args: {"fixture": True})
    monkeypatch.setattr(local_live, "fingerprint", lambda *args: {})
    monkeypatch.setattr(local_live, "require_committed_sources", lambda *args: "fixture")
    monkeypatch.setattr(local_live, "require_committed_operation_config", lambda *args: None)
    state = {
        "rows": [
            {
                "project": "p00",
                "campaign": "historical",
                "case_id": str(i),
                "event": "completed",
                "status": "ok",
            }
            for i in range(65)
        ],
        "calls": [],
        "response": {"status": "ok"},
    }

    class Account:
        def __init__(self, *args):
            pass

        def _history(self):
            return state["rows"]

        def preview(self, *args):
            return {"status": "approved"}

    class Client:
        def __init__(self, project):
            pass

        def request(self, envelope, operation):
            state["calls"].append((envelope, operation))
            return state["response"]

        def close(self):
            pass

    return (
        project,
        state,
        {
            "account_factory": Account,
            "client_factory": Client,
            "lease_factory": lambda _: contextlib.nullcontext(),
            "mode": "live",
        },
    )


def test_one_accounted_dispatch_has_fixed_identity_and_no_retry(operation):
    project, state, options = operation
    assert run_operation(project, "request-1", "synthetic", **options)["status"] == "ok"
    assert len(state["calls"]) == 1
    envelope, name = state["calls"][0]
    assert (name, envelope["campaign_id"], envelope["case_id"], envelope["trial"]) == (
        "complete",
        "local-live-operation-v1",
        "request-1",
        1,
    )


@pytest.mark.parametrize("condition", ["exhausted", "duplicate", "uncertain", "prior_error"])
def test_existing_work_and_protected_capacity_stop_before_provider(operation, condition):
    project, state, options = operation
    row = {
        "project": "p00",
        "campaign": "local-live-operation-v1",
        "case_id": "request-1",
        "event": "completed",
        "status": "ok",
    }
    if condition == "exhausted":
        state["rows"].extend([{**row, "case_id": str(i)} for i in range(10)])
    if condition == "duplicate":
        state["rows"].append(row)
    if condition == "uncertain":
        state["rows"].append({**row, "event": "reserved"})
    if condition == "prior_error":
        state["rows"].append({**row, "status": "provider_error"})
    with pytest.raises(LocalLiveBlocked):
        run_operation(project, "request-1", "synthetic", **options)
    assert state["calls"] == []


def test_stale_policy_binding_denies_before_provider(operation):
    project, state, options = operation
    config_path = project / "evals/local-live-operation.json"
    config = json.loads(config_path.read_text())
    config["policy_sha256"] = "stale-policy"
    config_path.write_text(json.dumps(config))
    with pytest.raises(LocalLiveBlocked, match="operational_allocation_not_applied"):
        run_operation(project, "request-1", "synthetic", **options)
    assert state["calls"] == []


def test_provider_failure_returns_no_fallback_or_replay(operation):
    project, state, options = operation
    state["response"] = {"status": "INCOMPLETE"}
    with pytest.raises(LocalLiveBlocked, match="no_replay"):
        run_operation(project, "request-1", "synthetic", **options)
    assert len(state["calls"]) == 1


def test_disabled_operation_denies_before_provider(tmp_path):
    project = tmp_path / "lab/projects/p00"
    (project / "evals").mkdir(parents=True)
    (project / "evals/local-live-operation.json").write_text('{"enabled": false}')
    with pytest.raises(LocalLiveBlocked):
        run_operation(
            project,
            "request-1",
            "synthetic",
            mode="live",
            client_factory=lambda _: pytest.fail("provider accessed"),
        )


def test_fake_mode_and_invalid_id_deny_before_provider(tmp_path):
    project = tmp_path / "lab/projects/p00"
    with pytest.raises(LocalLiveBlocked, match="explicit_live"):
        run_operation(project, "request-1", "synthetic", mode="fake")
    with pytest.raises(LocalLiveBlocked, match="stable_request"):
        run_operation(project, "bad id", "synthetic", mode="live")
