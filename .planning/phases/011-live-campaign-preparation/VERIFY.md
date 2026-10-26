# Verify — Live campaign preparation

The verifier must use the repository artifacts and commands, not implementation-chat claims. Save command, exit code, and sanitized output under `artifacts/evidence/live-campaign-preparation/`.

- [x] Dataset has exactly 40 unique semantic cases with 12 development and 28 sealed holdout; all seven families have at least three cases and language counts are 24 English / 16 Portuguese. Manifest hash is recorded.
- [x] Source-group validation prevents related cases from crossing splits. Independent review provenance remains `PENDING` and blocks generation.
- [x] Code-first tests reject deliberately wrong decisions, tool choices, malformed types/enums, extra fields, and truncated JSON. Grounding and required-fact rubric review remains `PENDING`.
- [x] Config shows finite per-case caps and explicitly labels unresolved cumulative requests/tokens/spend, quota, timing, pacing, confirmation and approval as `PENDING`; paid budget remains zero.
- [x] Pilot dry-run reports 6 calls; the primary campaign reports 120 calls (36 development + 84 holdout); fresh confirmation reserves 60 planned calls. Python `-S` dry-run reports no provider access, credential reads, or Docker mutation.
- [x] Generation exits incomplete while the runner is preparation-only or any authorization/cap is unresolved; no provider client or fallback is constructed.
- [ ] Resume/chunk reservation model does not reset cumulative caps; this preparation phase does not claim durable real-trial accounting is implemented unless separately evidenced.
- [x] P00 fake-mode fast and full checks pass: 60 tests, no skips; command, exit code, and sanitized result are saved.
- [x] No provider request occurred; no quality, cost, or latency result is inferred from fixtures or dry-run output.
- [ ] Durable resume/cumulative accounting is not implemented in this preparation phase and remains a gate for the bounded runner phase.
- [ ] Clean-context verification of the staged implementation remains required before phase gate acceptance.
