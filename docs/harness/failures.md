# Failures

Record recurring builder or product failures here before fixing them.

## 2026-10-26 — Campaign reservation race and uncertain retries

The initial ledger prototype checked cumulative totals before SQLite had taken a write lock, allowing two concurrent launchers to both observe remaining capacity. It now acquires `BEGIN IMMEDIATE` before reading totals and reserving; a two-launcher test proves one reservation is rejected at the cap. A reservation is durable before dispatch, survives process restart as uncertain, and cannot be reused. Missing usage keeps the full reservation. Actual provider dispatch/crash reconciliation is not yet implemented, so the campaign stays disabled. Evidence: `artifacts/evidence/live-campaign-runner/`.
