"""Regression for the 2026-11-06 owner contract decisions (phase 045)."""
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
V2 = PROJECT / "evals/datasets/live-v2"


def _cases():
    return {json.loads(l)["case_id"]: json.loads(l) for l in (V2 / "cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}


def test_v2_manifest_hash_matches_cases():
    manifest = json.loads((V2 / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["content_sha256"] == hashlib.sha256((V2 / "cases.jsonl").read_bytes()).hexdigest()
    assert manifest["dataset_version"] == "p00-live-v2"
    assert all(c["dataset_version"] == "p00-live-v2" for c in _cases().values())


def test_no_identifier_means_no_lookup():
    cases = _cases()
    for cid in ("p00-live-026", "p00-live-037"):
        assert cases[cid]["expected"]["action"] == "request_info"
        assert cases[cid]["expected"]["tool"] is None
        assert cases[cid]["allowed_tools"] == []
    assert cases["p00-live-025"]["expected"]["category"] == "billing"


def test_v2_differs_from_v1_only_in_case_037():
    v1 = [json.loads(l) for l in (PROJECT / "evals/datasets/live-v1/cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    v2 = _cases()
    changed = []
    for old in v1:
        new = dict(v2[old["case_id"]])
        new["dataset_version"] = old["dataset_version"]
        if new != old:
            changed.append(old["case_id"])
    assert changed == ["p00-live-037"]


def test_prompt_states_identifier_rule_and_billing_scope():
    prompt = (PROJECT / "agent/prompts/live-campaign.md").read_text(encoding="utf-8")
    assert "has an explicit identifier" in prompt
    assert "select no tool" in prompt
    assert "renewal" in prompt and "billing" in prompt
