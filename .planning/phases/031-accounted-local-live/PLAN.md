# Plan

1. Implement a project-local synthetic live command bound to the existing root accounted transport and exclusive campaign lease; verify separate allocation, cumulative P00 ceiling, caller request ID and committed input before provider initialization.
2. Add injected fake regressions for disabled/unfunded operation, duplicate and uncertain work, finite budget, one-attempt failures and no fake fallback. Run locked full fake gate with dedicated scratch and record evidence.
3. Once an owning root migration creates the separate approved free-only operational envelope, bind its exact policy and run a bounded local smoke. Do not consume holdout/confirmation.

allowed_write_paths: `.planning/phases/031-accounted-local-live/**`, `scripts/local_live.py`, `tests/llm/test_local_live.py`, `evals/local-live-operation.json`, `artifacts/evidence/local-live-operation-031/**`, `artifacts/evidence/funded-candidate-continuation/local-live-operation-031/**` (scratch), `docs/harness/progress.md`.
forbidden_changes: historical campaigns/results, datasets, rubrics, expected outcomes, policy/registry, existing ledgers except normal future accounted dispatch, customer data, provider calls during fake validation, paid use and human approvals. Fake tests, USD 0. max_tries: 3 persisted. Plan-check self-assessment; independent review pending. Stop if allocation/identity/uncertain work or provider failure blocks dispatch.
