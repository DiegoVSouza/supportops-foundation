# Verification

PASS for local fake control: focused suite 65 tests, exit 0; locked full gate 146 tests, fast, lint, format, compile, dataset contract and Compose configuration pass, exit 0. Optional service E2E remains INCOMPLETE. Command, directory, exit and output are in `artifacts/evidence/funded-candidate-continuation/critical-stop-022/`.

The initial focused run could not create the default Windows pytest temporary directory; it did not establish a behavioral red test. The isolated retry passed. The first full gate failed because an existing assertion assumed the prior 16-call ledger snapshot; that failure is preserved in `full.txt`. The subsequent formatting failure is preserved in `full-retry.txt`. The updated assertion checks current provider/logical accounting and fixed allocation arithmetic; it does not modify the ledgers. Final gate output is `full-final.txt`.

The changed fingerprint prevents C2 resume on this candidate; the historical candidate, manifest and results remain immutable. Attribution, funding, independent verification, human reviews, holdout and promotion remain INCOMPLETE/PENDING. No provider or credential access was used.

Post-commit dry-run: candidate `d37382d3c56bec02564134fb09115620169a5584`, fingerprint `4bca851b4c01a275a909f394028db232b6deb86fac64c83f69e85b49ccf9a000`, exit 0, provider and credentials untouched. Its automatically printed live resume command is not safe for historical C2 because the fingerprint differs; do not use it. The dry-run reports 107 primary calls remaining and 60 P00 confirmation calls protected. See `dry-run.txt`.
