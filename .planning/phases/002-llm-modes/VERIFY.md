# Verify — LLM modes

- [x] Fake script ordering, tool calls, structured output, and exhaustion are tested.
- [x] Replay success, missing call, mismatch, and malformed JSONL are tested.
- [x] Live missing key, missing/zero budget, over-budget preflight, timeout, provider error, and structured parse failure are tested with a fake transport.
- [x] Fake/replay tests pass offline and no test reports model-quality metrics.
- [x] Successful live responses reconcile provider-reported usage; missing usage retains the estimate, and observed over-cap totals fail and block the next request. Fake transport evidence: 21 tests passed in `artifacts/evidence/phase-002-budget-reconciliation.txt`.
- [x] Generic-provider limitations are explicit: without provider-enforced spending caps or verified provider token quotes, a single call can exceed the configured limit before observed usage is available. No live call or provider metric is claimed.
- [x] Command, exit code, and output are saved under `artifacts/evidence/`.
