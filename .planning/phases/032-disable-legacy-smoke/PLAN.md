# Plan

1. Block the legacy entry before sensitive operations and add a fake regression.
2. Run locked focused and full fake checks; capture command, cwd, exit and sanitized output and reconcile the changed operation fingerprint without replaying a live call.

allowed_write_paths: `.planning/phases/032-disable-legacy-smoke/**`, `scripts/smoke_groq.py`, `tests/test_smoke_groq.py`, `artifacts/evidence/disable-legacy-smoke-032/**`, `artifacts/evidence/funded-candidate-continuation/disable-legacy-smoke-032/**` (test scratch).

forbidden_changes: historical evidence and ledgers, budgets, provider calls, credentials, existing assertions, Docker lifecycle, paid use, customer data and external effects. Budget zero calls and USD 0. max_tries: 3 per failure; no live replay. Plan-check is implementer self-assessment; stop on unexpected provider access.
