"""Allocation table and scope gates for the 219- and 255-call P00 envelopes."""

from decimal import Decimal

import pytest

from scripts import campaign_execution as execution


def policy(requests):
    return {"projects": {"p00": {"requests": requests}}}


def test_allocation_table_matches_documented_arithmetic():
    low, high = execution.ALLOCATIONS[219], execution.ALLOCATIONS[255]
    # Primary + 60 confirmation + 10 retained operation calls equal the policy total.
    assert low["primary"].requests + 60 + 10 == 219
    assert high["primary"].requests + 60 + 10 == 255
    # The 255 envelope adds exactly 36 calls at 2,048 / 256 tokens per call.
    delta_calls = high["primary"].requests - low["primary"].requests
    assert delta_calls == 36
    assert high["primary"].input_tokens - low["primary"].input_tokens == 36 * 2048
    assert high["primary"].output_tokens - low["primary"].output_tokens == 36 * 256
    assert high["primary"].estimated_cost_usd - low["primary"].estimated_cost_usd == Decimal(
        "0.0082944"
    )
    assert high["policy"]["requests"] - low["policy"]["requests"] == 36


def test_unknown_policy_total_fails_closed():
    with pytest.raises(execution.ExecutionBlocked, match="p00_allocation_policy_mismatch"):
        execution.allocation_for(policy(300))
    with pytest.raises(execution.ExecutionBlocked, match="p00_allocation_policy_mismatch"):
        execution.allocation_for({})


@pytest.mark.parametrize(
    ("requests", "campaign", "allowed"),
    [
        (219, "free-dev-c2r1", True),
        (219, "free-dev-c3", False),
        (255, "free-dev-c3", True),
        (255, "free-dev-c2r1", False),
        (255, "free-dev-c2", False),
        (255, "free-dev-c1", False),
        (265, "free-dev-c4", True),
        (265, "free-dev-c3", False),
        (265, "free-dev-c2r1", False),
        (301, "free-dev-c5", True),
        (301, "free-dev-c4", False),
        (301, "free-dev-c3", False),
        (493, "free-dev-c6", True),
        (493, "free-dev-c5", False),
        (685, "free-dev-c7", True),
        (685, "free-dev-c6", False),
        (255, "renamed", False),
    ],
)
def test_development_scope_follows_the_applied_policy(requests, campaign, allowed):
    if allowed:
        execution.validate_live_scope("development", campaign, policy(requests))
    else:
        with pytest.raises(execution.ExecutionBlocked):
            execution.validate_live_scope("development", campaign, policy(requests))


@pytest.mark.parametrize("stage", ["pilot", "holdout"])
def test_other_stages_are_never_funded(stage):
    for requests in (219, 255, 265, 301, 493, 685):
        with pytest.raises(execution.ExecutionBlocked, match="phase_028_live_scope_not_allocated"):
            execution.validate_live_scope(stage, "free-dev-c3", policy(requests))


def test_historical_campaigns_report_immutable_provenance():
    for name in ("free-dev-c1", "free-dev-c2"):
        with pytest.raises(
            execution.ExecutionBlocked, match="immutable_campaign_provenance_mismatch"
        ):
            execution.validate_live_scope("development", name, policy(255))
    with pytest.raises(execution.ExecutionBlocked, match="immutable_campaign_provenance_mismatch"):
        execution.validate_live_scope("development", "free-dev-c2r1", policy(255))


def _full_policy(requests):
    allocation = execution.ALLOCATIONS[requests]
    return {
        "model": "openai/gpt-oss-20b",
        "authorized_paid_spend_usd": "0.00",
        "projects": {
            "p00": {
                **allocation["policy"],
                "calls_per_trial": 1,
                "input_tokens_per_call": 2048,
                "output_tokens_per_call": 256,
            }
        },
    }


@pytest.mark.parametrize("requests", [219, 255, 265, 301, 493, 685])
def test_binding_accepts_each_applied_envelope_and_rejects_drift(tmp_path, requests):
    import hashlib
    import json
    import sqlite3
    from contextlib import closing

    lab = tmp_path / "lab"
    runtime = lab / ".runtime/llm-live-readiness"
    provider = lab / "projects/p00/artifacts/evals/live/provider-usage.sqlite"
    runtime.mkdir(parents=True)
    provider.parent.mkdir(parents=True)
    identity = "c" * 32
    with closing(sqlite3.connect(provider)) as db:
        db.execute("CREATE TABLE identity(identity TEXT PRIMARY KEY)")
        db.execute("INSERT INTO identity VALUES(?)", (identity,))
        db.commit()

    def bind(value):
        sha = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
        (runtime / "ledger-references.json").write_text(
            json.dumps({"policy_sha256": sha, "projects": {"p00": identity}})
        )

    good = _full_policy(requests)
    bind(good)
    assert execution.verify_applied_policy_binding(lab, good) == identity
    drift = _full_policy(requests)
    drift["projects"]["p00"]["output_tokens"] += 256
    bind(drift)
    with pytest.raises(execution.ExecutionBlocked, match="p00_allocation_policy_mismatch"):
        execution.verify_applied_policy_binding(lab, drift)
    paid = _full_policy(requests)
    paid["authorized_paid_spend_usd"] = "5.00"
    bind(paid)
    with pytest.raises(execution.ExecutionBlocked, match="p00_allocation_policy_mismatch"):
        execution.verify_applied_policy_binding(lab, paid)


def test_replacement_envelope_adds_exactly_ten_calls_over_the_dev_envelope():
    mid, top = execution.ALLOCATIONS[255], execution.ALLOCATIONS[265]
    assert top["primary"].requests + 60 + 10 == 265
    assert top["primary"].requests - mid["primary"].requests == 10
    assert top["primary"].input_tokens - mid["primary"].input_tokens == 10 * 2048
    assert top["primary"].output_tokens - mid["primary"].output_tokens == 10 * 256
    assert top["primary"].estimated_cost_usd - mid["primary"].estimated_cost_usd == Decimal(
        "0.002304"
    )
    assert top["policy"]["input_tokens"] - mid["policy"]["input_tokens"] == 10 * 2048
    # Confirmation reserve is unchanged: policy total minus primary minus operation.
    assert top["policy"]["input_tokens"] - top["primary"].input_tokens - 20480 == 122880
    assert top["policy"]["output_tokens"] - top["primary"].output_tokens - 2560 == 15360


def test_every_envelope_keeps_the_confirmation_reserve_and_holdout_arithmetic():
    for total, entry in execution.ALLOCATIONS.items():
        primary, policy = entry["primary"], entry["policy"]
        assert policy["requests"] == total
        assert primary.requests + 60 + 10 == total
        assert policy["input_tokens"] - primary.input_tokens - 20480 == 122880
        assert policy["output_tokens"] - primary.output_tokens - 2560 == 15360
        assert Decimal(policy["estimated_cost_usd"]) - primary.estimated_cost_usd - Decimal(
            "0.002304"
        ) == Decimal("0.013824")
        assert policy["input_tokens"] == total * 2048
        assert policy["output_tokens"] == total * 256
