# Plan

1. Reconcile the applied policy binding and project/global capacity report without treating P01 operation capacity as evaluation funding.
2. Run locked fake regressions and provider-free ledger reconciliation; record sanitized evidence and preserve historical fingerprints.

allowed_write_paths: `.planning/phases/033-p01-envelope-reconciliation/**`, `evals/local-live-operation.json`, `scripts/run_live_campaign.py`, `tests/test_live_campaign_preparation.py`, `artifacts/evidence/p01-envelope-reconciliation-033/**`, `artifacts/evidence/funded-candidate-continuation/p01-envelope-reconciliation-033/**` (scratch).

forbidden_changes: historical results/ledgers, policy, P00 allocations, live calls, credentials, paid use, customer data, test weakening, Docker lifecycle and external effects. Fake mode; zero provider calls / USD 0. max_tries: 3 per failure; no live replay. Plan-check is implementer self-assessment.
