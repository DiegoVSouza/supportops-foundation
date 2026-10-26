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
