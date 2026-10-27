"""Reject historical resume through the real runner before any provider can initialize."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
LAB = PROJECT.parents[1]
sys.path.insert(0, str(PROJECT))
from scripts.campaign_execution import ExecutionBlocked, fingerprint, run_campaign
from scripts.run_live_campaign import load_cases, load_json


class DenyProvider:
    provenance = "live"
    initialized = 0

    def __init__(self, *args, **kwargs):
        type(self).initialized += 1
        raise AssertionError("Offline probe forbids provider initialization")


paths = [
    PROJECT / "artifacts/evals/live/ledger.sqlite",
    PROJECT / "artifacts/evals/live/provider-usage.sqlite",
    PROJECT / ".runtime/llm-review/answers.sqlite",
    LAB / ".runtime/llm-live-readiness/ledger-references.json",
]
for campaign in ("free-pilot-v1", "free-dev-c1"):
    paths.extend((PROJECT / "artifacts/evals/live" / campaign).glob("*"))


def snapshot():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


before = snapshot()
config = load_json(PROJECT / "evals/live-campaign.json")
cases = load_cases(PROJECT / config["cases_path"], load_json(PROJECT / config["dataset_manifest"]))
try:
    run_campaign(PROJECT, config, cases, "development", "free-dev-c1", client_factory=DenyProvider)
except ExecutionBlocked as error:
    reason = str(error)
else:
    raise AssertionError("Historical resume was accepted")
assert reason == "immutable_campaign_provenance_mismatch", reason
assert DenyProvider.initialized == 0
assert before == snapshot()
current = fingerprint(PROJECT, LAB / "shared/policies/groq-free-campaign.json")
historical = load_json(PROJECT / "artifacts/evals/live/free-dev-c1/manifest.json")
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT, text=True).strip()
print(json.dumps({
    "corrected_implementation_commit": revision,
    "historical_candidate_commit": historical["candidate_commit"],
    "reason": reason,
    "historical_resume_accepted": False,
    "provider_initializations": DenyProvider.initialized,
    "provider_accessed": False,
    "credentials_read": False,
    "immutable_files_and_ledgers_unchanged": True,
    "current_public_source_sha256": current,
    "changed_or_new_source_paths": sorted(k for k, v in current.items() if historical["files_sha256"].get(k) != v),
    "new_live_campaign_created": False,
    "candidate_quality_evidence": "PENDING_NEW_ALLOCATION_AND_FREEZE",
}, indent=2))
