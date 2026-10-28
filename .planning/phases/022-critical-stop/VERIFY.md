# Verification

PASS for local fake control: focused suite 65 tests, exit 0; locked full gate 146 tests, fast, lint, format, compile, dataset contract and Compose configuration pass, exit 0. Optional service E2E remains INCOMPLETE. Command, directory, exit and output are in `artifacts/evidence/funded-candidate-continuation/critical-stop-022/`.

The initial focused run could not create the default Windows pytest temporary directory; it did not establish a behavioral red test. The isolated retry passed. The first full gate failed because an existing assertion assumed the prior 16-call ledger snapshot; that failure is preserved in `full.txt`. The subsequent formatting failure is preserved in `full-retry.txt`. The updated assertion checks current provider/logical accounting and fixed allocation arithmetic; it does not modify the ledgers. Final gate output is `full-final.txt`.

The changed fingerprint prevents C2 resume on this candidate; the historical candidate, manifest and results remain immutable. Attribution, funding, independent verification, human reviews, holdout and promotion remain INCOMPLETE/PENDING. No provider or credential access was used.
