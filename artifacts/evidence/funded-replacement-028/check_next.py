"""Read-only prerequisite check for the next never-executed scheduled trial."""
import hashlib
import json
from pathlib import Path
import sys

project = Path(__file__).resolve().parents[3]
lab = project.parents[1]
sys.path.insert(0, str(project))
sys.path.insert(0, str(lab / 'scripts/harness'))
from scripts.campaign_execution import fingerprint, require_committed_sources, verify_applied_policy_binding
from live_free_account import AccountBlocked, SharedAccount

policy_path = lab / 'shared/policies/groq-free-campaign.json'
policy = json.loads(policy_path.read_text())
directory = project / 'artifacts/evals/live/free-dev-c2r1'
manifest = json.loads((directory / 'manifest.json').read_text())
files = fingerprint(project, policy_path)
require_committed_sources(project, files)
assert files == manifest['files_sha256']
verify_applied_policy_binding(lab, policy)
trials = [json.loads(line) for line in (directory / 'trials.jsonl').read_text().splitlines()]
assert not any(t.get('critical_failure') or t['outcome'] == 'provider_error' for t in trials)
done = {(t['case_id'], t['trial']) for t in trials}
next_trial = next(((case, trial) for case in manifest['sampling_order'] for trial in (1, 2, 3) if (case, trial) not in done), None)
report = {'provider_accessed': False, 'credentials_read': False, 'recorded_trials': len(trials), 'source_fingerprint_sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}
try:
    if next_trial:
        approval = SharedAccount(lab, policy).preview('p00', 'free-dev-c2r1', *next_trial, 1, 2048, 256)
        report.update(status='PASS_NEXT_TRIAL_GUARD', next_trial=list(next_trial), approval=approval)
    else:
        report.update(status='COMPLETE_NO_MORE_TRIALS')
except AccountBlocked as error:
    report.update(status='INCOMPLETE', reason=str(error))
print(json.dumps(report, indent=2))
sys.exit(2 if report['status'] == 'INCOMPLETE' else 0)
