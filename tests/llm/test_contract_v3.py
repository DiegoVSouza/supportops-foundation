"""live-v3 dataset, the code-decided fields and the prompt contract."""

import difflib
import hashlib
import json
from pathlib import Path

import pytest

from scripts import campaign_execution as execution
from scripts.run_live_campaign import load_cases, validate_prediction

PROJECT = Path(__file__).resolve().parents[2]
V3 = PROJECT / "evals/datasets/live-v3"
MANIFEST = json.loads((V3 / "manifest.json").read_text(encoding="utf-8"))
CASES = load_cases(V3 / "cases.jsonl", MANIFEST)


def test_manifest_matches_the_bytes_and_the_split_sizes():
    assert (
        MANIFEST["content_sha256"] == hashlib.sha256((V3 / "cases.jsonl").read_bytes()).hexdigest()
    )
    assert MANIFEST["split_counts"] == {"development": 64, "holdout": 20}
    # The final split is 20 cases x 3 trials = the 60 protected confirmation calls.
    assert sum(c["split"] == "holdout" for c in CASES) * 3 == 60


def test_labels_follow_one_rule_for_every_case():
    for case in CASES:
        expected = case["expected"]
        tool = None
        if expected["action"] == "answer":
            tool = execution.TOOL_FOR_CATEGORY[expected["category"]]
        assert expected["tool"] == tool, case["case_id"]
        assert expected["escalate"] == (expected["action"] == "escalate"), case["case_id"]
        assert case["allowed_tools"] == ([tool] if tool else [])
        if expected["action"] == "answer":
            assert expected["category"] != "other", case["case_id"]


def test_dataset_covers_every_domain_action_and_language():
    for split in ("development", "holdout"):
        rows = [c for c in CASES if c["split"] == split]
        assert {c["expected"]["category"] for c in rows} == {
            "billing",
            "shipping",
            "technical",
            "account_access",
            "other",
        }
        assert {c["expected"]["action"] for c in rows} == {"answer", "request_info", "escalate"}
        assert {c["language"] for c in rows} == {"en", "pt-BR"}
    answers = {
        c["expected"]["category"]
        for c in CASES
        if c["split"] == "holdout" and c["expected"]["action"] == "answer"
    }
    assert answers == {"billing", "shipping", "technical", "account_access"}


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["case_id"])
def test_a_perfect_model_passes_every_case(case):
    expected = case["expected"]
    model_output = {
        "decision": {
            "category": expected["category"],
            "specific": expected["action"] == "answer",
            "risky": expected["action"] == "escalate",
            "rationale": "ok",
        }
    }
    assert validate_prediction(case, execution.complete_prediction(model_output)) == []


def features(category, specific, risky):
    return {
        "decision": {
            "category": category,
            "specific": specific,
            "risky": risky,
            "rationale": "r",
        }
    }


def test_code_derives_action_tool_and_escalation_from_the_reported_features():
    run = execution.complete_prediction
    assert run(features("billing", True, False))["decision"]["action"] == "answer"
    assert run(features("billing", True, False))["tool"] == "lookup_invoice"
    assert run(features("shipping", True, False))["tool"] == "lookup_order"
    assert run(features("technical", True, False))["tool"] == "lookup_kb"
    assert run(features("account_access", True, False))["tool"] == "lookup_kb"
    assert run(features("other", True, False))["tool"] is None
    assert run(features("billing", False, False))["decision"]["action"] == "request_info"
    assert run(features("billing", False, False))["tool"] is None
    # A risky goal wins over a specific request and never runs a tool.
    escalated = run(features("billing", True, True))
    assert escalated["decision"]["action"] == "escalate"
    assert escalated["decision"]["escalate"] is True
    assert escalated["tool"] is None
    assert run(features("billing", True, False))["decision"]["escalate"] is False


def test_action_policy_covers_every_combination_and_never_derives_the_refund_tool():
    for risky in (True, False):
        for specific in (True, False):
            action = execution.decide_action(risky, specific)
            assert action == ("escalate" if risky else ("answer" if specific else "request_info"))
    assert all(
        execution.complete_prediction(features(category, specific, risky))["tool"] != "issue_refund"
        for category in ("billing", "shipping", "technical", "account_access", "other")
        for specific in (True, False)
        for risky in (True, False)
    )


def test_the_category_and_action_shape_is_still_completed():
    out = execution.complete_prediction(
        {"decision": {"category": "billing", "action": "escalate", "rationale": "r"}}
    )
    assert out["decision"]["escalate"] is True and out["tool"] is None


def test_malformed_or_extended_outputs_are_left_for_validation_to_reject():
    bad_type = features("billing", "yes", False)
    assert execution.complete_prediction(bad_type) == bad_type
    extra = {"decision": {**features("billing", True, False)["decision"], "tool": "x"}}
    assert execution.complete_prediction(extra) == extra
    missing = {"decision": {"category": "billing", "specific": True}}
    assert execution.complete_prediction(missing) == missing
    assert execution.complete_prediction("text") == "text"
    with pytest.raises(TypeError):
        execution.complete_prediction(features([], True, False))


def test_prompt_names_every_reported_feature_and_stays_within_the_input_bound():
    prompt = (PROJECT / "agent/prompts/live-campaign.md").read_text(encoding="utf-8").strip()
    for fragment in ("category:", "specific:", "risky:", "untrusted"):
        assert fragment in prompt
    schema = json.loads((PROJECT / "agent/schemas/live-decision.json").read_text(encoding="utf-8"))
    assert set(schema["properties"]["decision"]["required"]) == {
        "category",
        "specific",
        "risky",
        "rationale",
    }
    longest = max(CASES, key=lambda case: len(case["input"].encode()))["input"]
    payload = execution.build_payload(
        PROJECT,
        prompt,
        longest,
        json.loads((PROJECT / "evals/live-campaign.json").read_text(encoding="utf-8")),
    )
    assert execution.payload_input_bound(payload) <= 2048


def test_rubric_states_the_single_lookup_rule():
    rubric = (PROJECT / "evals/rubrics/live-v1/rubric.md").read_text(encoding="utf-8")
    assert "Lookup eligibility rule" in rubric
    assert "independent review waived by the owner" in rubric
