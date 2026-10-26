# Verify

- [x] Chunks/resume preserve failed and uncertain trials without semantic reruns.
- [x] Missing/invalid limits and account rejection prevent dispatch.
- [x] Reservation and durable checkpoint precede execution; interruptions remain charged. Subprocess death during execution and before outcome persistence releases the OS lock and retains uncertainty.
- [x] Deadline/pacing, cap exhaustion, invalid outcomes and excess usage stop safely; export failure after result persistence cannot trigger reexecution.
- [x] Focused tests pass (30); full locked offline gate passes (99 tests, lint/format/compile/dataset/Compose checks), exit 0.
- [x] `python -S` pilot dry-run exits 0 and execution still exits 2; provider and shared account integration remain INCOMPLETE.
- [x] Progress/knowledge and reviewed local implementation paths recorded.
- [ ] Independent clean-context verification remains pending.

Initial red import, an inaccessible default Windows pytest temp directory and first lint failures were retained; use the phase-specific ignored `--basetemp` documented in the focused evidence. All later checks passed without changing expected assertions or production caps. No provider request or service mutation occurred. The full gate still labels optional service E2E INCOMPLETE; this phase validates a CLI controller only.

Evidence: `artifacts/evidence/live-campaign-batches/`.
