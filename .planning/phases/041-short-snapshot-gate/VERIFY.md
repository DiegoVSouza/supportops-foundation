# Verification plan

FAIL: the single phase041 gate was marked consumed, but the runner supplied `tmp-pytest-041`, which the project rejects because it is outside an owned evidence directory. `check_full.py` exited2 before tests; no provider access. Evidence: `artifacts/evidence/short-snapshot-gate-041/attempt.json` and `gate-result.json`. The runner path was corrected offline after the failure; no replay was executed. Prior history3/3 plus phase038, phase039, phase040 and phase041 exceptions remain consumed.

The owned snapshot was relocated intact from `.runtime/p00-gate-041` to `artifacts/evidence/short-snapshot-gate-041/.git/p00-gate-041` after the root link checker traversed the isolated incomplete copy and reported 29 false broken links. Root `python scripts/harness/check.py --root .` then passed, exit0. The original command/cwd remains historical in `gate-result.json`.
