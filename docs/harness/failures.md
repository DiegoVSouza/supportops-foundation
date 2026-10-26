# Failures

Record recurring builder or product failures here before fixing them.

## 2026-10-26 — Campaign reservation race and uncertain retries

The initial ledger prototype checked cumulative totals before SQLite had taken a write lock, allowing two concurrent launchers to both observe remaining capacity. It now acquires `BEGIN IMMEDIATE` before reading totals and reserving; a two-launcher test proves one reservation is rejected at the cap. A reservation is durable before dispatch, survives process restart as uncertain, and cannot be reused. Missing usage keeps the full reservation. Actual provider dispatch/crash reconciliation is not yet implemented, so the campaign stays disabled. Evidence: `artifacts/evidence/live-campaign-runner/`.
# 2026-10-26 — Free pilot baseline: routing and provider diagnostics

- Candidate: `476fae54e239cfc7c2200831662ef1af2af52e27`; campaign: `free-pilot-v1`.
- Three real development/pilot responses selected `request_info` instead of the existing `answer` reference; one also returned no read-only tool. Root-cause hypothesis: the global prompt does not clearly distinguish missing retrieved records from an unclear issue; it encourages asking for information before selecting an available lookup. Clarify the generic next-action policy in a declared development correction round, retain baseline failures and do not change expected outcomes.
- The fourth request returned a transport reason `request_schema`; the owning artifact reduced it to `configuration`, and exact HTTP status/provider error code were not persisted. The actual provider cause cannot be established from existing evidence. Add restricted categorical HTTP/error-code diagnostics before more generation; never persist raw error bodies or repeat a semantic failure to obtain approval.
- Outcome: INCOMPLETE (four requests, three model failures, one operational failure, two cases pending). Known usage: 844 / 248 tokens; unknown failed usage remains reserved. Human review/promotion remain pending. Evidence: `artifacts/evals/live/free-pilot-v1/report.json`.

## Private review ACL correction

Post-run readback found four access entries, including pre-existing explicit grants, despite inheritance being disabled. The previous `icacls /grant:r` plus `/inheritance:r` did not remove those explicit entries. Protected inheritance alone is insufficient evidence of owner-only storage. Repaired only the private review directory/known SQLite files using owner assignment, ACL reset, explicit owner grant and inheritance removal; readback verifies one current-user access entry and current-user ownership. A Windows regression injects extra directory/file grants and proves they are rejected until removed. No further generation occurred during repair; data in this application state is authorized synthetic output.

## 2026-10-26 — Free development campaign quota checkpoint

`free-dev-c1` stopped after 12 completed trials when the shared account guard returned `free_token_minute_checkpoint`. All 12 model trials passed; no semantic failure or operational provider error occurred. The guard stopped further reservations, so no uncertain attempt needs replay. The current campaign remains INCOMPLETE with 24 trials pending. Resume only with the recorded `--resume free-dev-c1 --execute-free --max-trials 10` command after the guard approves capacity. The latest sanitized token-minute reset value is historical feedback, not a guarantee of current quota. Do not infer daily remaining tokens or billing tier from headers. Evidence: `artifacts/evidence/development-correction-one/checkpoint-accounting.json` and `resume-dry-run.json`.

## Phase 016 audit corrections supersede the previous resume instruction

Offline review found four gaps: arbitrary campaign IDs/stages could create another development allocation; dirty or untracked schemas were omitted from the candidate Git check; the primary ceiling subtracted the pilot even though the ledger already included it; and local payload checks omitted transport normalization/framing. The corrected runner permits only the allocated live development ID, checks all fingerprinted sources in their owning repositories, applies the full 126-call ceiling to cumulative history, and matches the transport bound before any provider initialization. New regressions cover these paths; the locked full gate passed 131 tests.

These source corrections invalidate the frozen `free-dev-c1` fingerprint. The old safe-resume command above is historical and must now fail with provenance mismatch. Preserve its 12 completed trials and 24 pending trials; no manifest migration, new ID, reset, implicit retry, new correction allocation or provider call was performed. A separately declared allocation/candidate phase is required before further generation. Offline evidence: `artifacts/evidence/development-correction-one/audit-fix/`.
