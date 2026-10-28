"""Prepare an unapplied policy proposal from verified current allocation."""
import copy
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import sys

project = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project))
from scripts.run_live_campaign import applied_allocation

current = applied_allocation(project)
lab = project.parents[1]
policy = json.loads((lab / 'shared/policies/groq-free-campaign.json').read_text())
remaining = current['remaining_capacity_by_project']['p00']['primary_remaining']
required = 36 + 84
delta = required - remaining
assert remaining == 107 and delta == 13
proposed = copy.deepcopy(policy)
input_delta, output_delta = delta * 2048, delta * 256
estimate = (input_delta * Decimal(policy['pricing_per_million']['input_usd']) + output_delta * Decimal(policy['pricing_per_million']['output_usd'])) / 1000000
for caps in (proposed['projects']['p00'], proposed['campaign_caps']):
    caps['requests'] += delta
    caps['input_tokens'] += input_delta
    caps['output_tokens'] += output_delta
    caps['estimated_cost_usd'] = str(Decimal(caps['estimated_cost_usd']) + estimate)
assert all(policy['projects'][p] == proposed['projects'][p] for p in policy['projects'] if p != 'p00')
assert proposed['authorized_paid_spend_usd'] == policy['authorized_paid_spend_usd']
report = {
    'status': 'PROPOSAL_ONLY_NOT_AUTHORIZED_NOT_APPLIED',
    'authorization_id': 'PENDING_EXPLICIT_USER_DECISION',
    'provider_accessed': False, 'credentials_read': False,
    'expected_current_policy_sha256': current['policy_sha256'],
    'expected_registered_provider_ledger_uuids': current['registered_provider_ledger_uuids'],
    'candidate_commit': current['candidate_commit'],
    'candidate_fingerprint_sha256': current['candidate_fingerprint_sha256'],
    'remaining_primary': remaining, 'replacement_development': 36, 'holdout_protected': 84,
    'confirmation_protected': current['p00_confirmation_protected'],
    'delta': {'requests': delta, 'input_tokens': input_delta, 'output_tokens': output_delta, 'economic_estimate_usd': str(estimate), 'authorized_paid_spend_usd': '0.00'},
    'proposed_policy': proposed,
    'proposed_policy_sha256': hashlib.sha256(json.dumps(proposed, sort_keys=True).encode()).hexdigest(),
    'application_requirements': ['explicit free-only 13-call authorization', 'separate validated migration preserving all registry UUIDs, histories and unknown reservations', 'owning candidate/scope allocation and immutable source freeze', 'credential eligibility and no unresolved uncertain work', 'all original holdout and human gates remain'],
}
print(json.dumps(report, indent=2, sort_keys=True))
