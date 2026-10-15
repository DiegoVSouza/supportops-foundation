# Verify — LLM modes

- [ ] Fake script ordering, tool calls, structured output, and exhaustion are tested.
- [ ] Replay success, missing call, mismatch, and malformed JSONL are tested.
- [ ] Live missing key, missing/zero budget, over-budget preflight, timeout, provider error, and structured parse failure are tested with a fake transport.
- [ ] Fake/replay tests pass offline and no test reports model-quality metrics.
- [ ] Command, exit code, and output are saved under `artifacts/evidence/`.
