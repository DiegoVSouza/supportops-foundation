"""live-v3 dataset, the code-decided fields and the prompt contract."""

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


def model_output(category, action):
    return {"decision": {"category": category, "action": action, "rationale": "r"}}


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["case_id"])
def test_a_perfect_model_passes_every_case_through_the_director(case):
    expected = case["expected"]
    output = model_output(expected["category"], expected["action"])
    prediction = execution.complete_prediction(output, case["input"])
    assert validate_prediction(case, prediction) == []


def test_code_derives_escalation_and_tool_from_the_action_and_category():
    run = execution.complete_prediction
    assert run(model_output("billing", "answer"))["tool"] == "lookup_invoice"
    assert run(model_output("shipping", "answer"))["tool"] == "lookup_order"
    assert run(model_output("technical", "answer"))["tool"] == "lookup_kb"
    assert run(model_output("account_access", "answer"))["tool"] == "lookup_kb"
    assert run(model_output("other", "answer"))["tool"] is None
    assert run(model_output("billing", "request_info"))["tool"] is None
    escalated = run(model_output("billing", "escalate"))
    assert escalated["tool"] is None and escalated["decision"]["escalate"] is True
    assert run(model_output("billing", "answer"))["decision"]["escalate"] is False


def test_the_feature_report_shape_is_still_supported():
    features = {
        "decision": {"category": "billing", "specific": True, "risky": False, "rationale": "r"}
    }
    out = execution.complete_prediction(features)
    assert out["decision"]["action"] == "answer" and out["tool"] == "lookup_invoice"
    risky = {"decision": {"category": "billing", "specific": True, "risky": True, "rationale": "r"}}
    assert execution.complete_prediction(risky)["decision"]["action"] == "escalate"


def test_the_director_corrects_a_bare_reference_and_an_own_money_demand():
    run = execution.complete_prediction
    asked = run(model_output("billing", "answer"), "I need that charge looked at.")
    assert asked["decision"]["action"] == "request_info" and asked["tool"] is None
    escalated = run(model_output("billing", "answer"), "I demand a full refund right now.")
    assert escalated["decision"]["action"] == "escalate" and escalated["tool"] is None
    kept = run(model_output("billing", "answer"), "My invoice INV-SYN-310 shows a late fee.")
    assert kept["decision"]["action"] == "answer" and kept["tool"] == "lookup_invoice"
    # An escalation chosen by the model is never lowered by the director.
    held = run(model_output("other", "escalate"), "Can you check on it for me?")
    assert held["decision"]["action"] == "escalate"


def test_an_invalid_action_is_left_for_validation_to_reject():
    out = execution.complete_prediction(model_output("billing", "refund"), "Fix that please.")
    assert out["decision"]["action"] == "refund"


def test_malformed_or_extended_outputs_are_left_for_validation_to_reject():
    bad_type = {
        "decision": {"category": "billing", "specific": "yes", "risky": False, "rationale": "r"}
    }
    assert execution.complete_prediction(bad_type) == bad_type
    extra = {"decision": {**model_output("billing", "answer")["decision"], "tool": "x"}}
    assert execution.complete_prediction(extra) == extra
    missing = {"decision": {"category": "billing", "action": "answer"}}
    assert execution.complete_prediction(missing) == missing
    assert execution.complete_prediction("text") == "text"
    with pytest.raises(TypeError):
        execution.complete_prediction(model_output([], "answer"))


def test_prompt_and_schema_describe_the_model_contract_and_fit_the_input_bound():
    prompt = (PROJECT / "agent/prompts/live-campaign.md").read_text(encoding="utf-8").strip()
    for fragment in ("answer:", "request_info:", "escalate:", "untrusted"):
        assert fragment in prompt
    schema = json.loads((PROJECT / "agent/schemas/live-decision.json").read_text(encoding="utf-8"))
    decision = schema["properties"]["decision"]
    assert set(decision["required"]) == {"category", "action", "rationale"}
    assert set(decision["properties"]["action"]["enum"]) == {"answer", "request_info", "escalate"}
    config = json.loads((PROJECT / "evals/live-campaign.json").read_text(encoding="utf-8"))
    longest = max(CASES, key=lambda case: len(case["input"].encode()))["input"]
    payload = execution.build_payload(PROJECT, prompt, longest, config)
    assert execution.payload_input_bound(payload) <= 2048


def test_replaying_the_recorded_c6_trials_through_the_director_gives_182_of_192():
    import json as _json

    rows = [
        _json.loads(line)
        for line in (PROJECT / "artifacts/evals/live/free-dev-c6/trials.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    by_id = {case["case_id"]: case for case in CASES}
    recorded = replayed = 0
    for row in rows:
        case = by_id[row["case_id"]]
        raw = model_output(row["prediction"]["category"], row["prediction"]["action"])
        prediction = execution.complete_prediction(raw, case["input"])
        recorded += row["passed"]
        replayed += not validate_prediction(case, prediction)
    assert (recorded, replayed, len(rows)) == (157, 182, 192)


def test_rubric_states_the_single_lookup_rule():
    rubric = (PROJECT / "evals/rubrics/live-v1/rubric.md").read_text(encoding="utf-8")
    assert "Lookup eligibility rule" in rubric
    assert "independent review waived by the owner" in rubric
