"""Freeze source and resource prerequisites without provider or credential access."""
import hashlib
import json
from pathlib import Path
import sys

project = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project))
lab = project.parents[1]
sys.path.insert(0, str(lab / 'scripts/harness'))
from scripts.campaign_execution import fingerprint, require_committed_sources, verify_applied_policy_binding, private_directory
from scripts.run_live_campaign import applied_allocation
from live_free_account import SharedAccount

policy_path = lab / 'shared/policies/groq-free-campaign.json'
policy = json.loads(policy_path.read_text())
files = fingerprint(project, policy_path)
revision = require_committed_sources(project, files)
source_fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
assert source_fingerprint == '7b1e79cae5ef397c45be36dac5860489e7ad858fb6e6817a88f3b46896763dc9'
identity = verify_applied_policy_binding(lab, policy)
allocation = applied_allocation(project)
assert allocation['remaining_capacity_by_project']['p00']['primary_remaining'] == 120
assert allocation['p00_confirmation_protected']['requests'] == 60
assert not (project / 'artifacts/evals/live/free-dev-c2r1/manifest.json').exists()
private_directory(project / '.runtime/llm-review', project, verify_only=True)
preview = SharedAccount(lab, policy).preview('p00', 'free-dev-c2r1', 'p00-live-001', 1, 1, 2048, 256)
assert preview['status'] == 'approved'
print(json.dumps({
    'status': 'FROZEN_LOCAL_PREREQUISITES_PASS',
    'campaign_id': 'free-dev-c2r1', 'stage': 'development',
    'source_fingerprint_sha256': source_fingerprint, 'files_sha256': files,
    'source_implementation_commit': '77f128992d262184a1384dac8f712aa9ce999bf1',
    'inspection_evidence_head': revision,
    'dispatch_candidate_commit': 'RECORDED_BY_NEW_IMMUTABLE_MANIFEST_AT_CREATION',
    'policy_sha256': allocation['policy_sha256'], 'provider_ledger_uuid': identity,
    'primary_remaining': 120, 'replacement_calls': 36, 'holdout_protected': 84,
    'confirmation_protected': 60, 'preview': preview,
    'private_storage_acl_verified': True,
    'provider_accessed': False, 'credentials_read': False,
    'human_dataset_rubric_independent_review': 'PENDING',
    'promotion': 'INCOMPLETE',
}, indent=2, sort_keys=True))
