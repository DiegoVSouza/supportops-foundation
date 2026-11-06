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
            "action": expected["action"],
            "rationale": "ok",
        }
    }
    assert validate_prediction(case, execution.complete_prediction(model_output)) == []


def test_code_decides_tool_and_escalation_and_never_the_refund_tool():
    def run(category, action):
        return execution.complete_prediction(
            {"decision": {"category": category, "action": action, "rationale": "r"}}
        )

    assert run("billing", "answer")["tool"] == "lookup_invoice"
    assert run("shipping", "answer")["tool"] == "lookup_order"
    assert run("technical", "answer")["tool"] == "lookup_kb"
    assert run("account_access", "answer")["tool"] == "lookup_kb"
    assert run("other", "answer")["tool"] is None
    assert run("billing", "request_info")["tool"] is None
    assert run("billing", "escalate")["tool"] is None
    assert run("billing", "escalate")["decision"]["escalate"] is True
    assert run("billing", "answer")["decision"]["escalate"] is False
    assert all(
        run(category, action)["tool"] != "issue_refund"
        for category in ("billing", "shipping", "technical", "account_access", "other")
        for action in ("answer", "request_info", "escalate", "refund")
    )


def test_malformed_or_extended_outputs_are_left_for_validation_to_reject():
    extended = {
        "decision": {"category": "billing", "action": "answer", "rationale": "r", "tool": "x"}
    }
    assert execution.complete_prediction(extended) == extended
    missing = {"decision": {"category": "billing", "action": "answer"}}
    assert execution.complete_prediction(missing) == missing
    assert execution.complete_prediction("text") == "text"
    with pytest.raises(TypeError):
        execution.complete_prediction(
            {"decision": {"category": [], "action": "answer", "rationale": "r"}}
        )


def test_prompt_states_the_rule_and_examples_do_not_copy_the_dataset():
    prompt = (PROJECT / "agent/prompts/live-campaign.md").read_text(encoding="utf-8").strip()
    for fragment in ("answer:", "request_info:", "escalate:", "untrusted"):
        assert fragment in prompt
    examples = [
        line.split(":")[0].strip()
        for line in prompt.splitlines()[prompt.splitlines().index("E.g.") + 1 :]
    ]
    assert len(examples) >= 6
    for example in examples:
        for case in CASES:
            ratio = difflib.SequenceMatcher(None, example.lower(), case["input"].lower()).ratio()
            assert ratio < (0.5 if case["split"] == "holdout" else 0.6), (example, case["case_id"])


def test_rubric_states_the_single_lookup_rule():
    rubric = (PROJECT / "evals/rubrics/live-v1/rubric.md").read_text(encoding="utf-8")
    assert "Lookup eligibility rule" in rubric
    assert "independent review waived by the owner" in rubric
