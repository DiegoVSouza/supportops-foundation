# Plan

1. Inspect the current uncommitted source/tests and ledger/migration dependencies; prepare a fresh isolated lab snapshot including committed WAL state, with an explicitly created test scratch parent.
2. Run exactly one newly authorized full fake gate with a durable 1/1 attempt marker. Record command, cwd, exit, sanitized output and preserve all historical failures and user changes.
3. If PASS, review and commit the candidate source and reconcile the current fingerprint; if FAIL, preserve evidence, stop this gate and continue independent work. Do not dispatch live until all bindings and authorization conditions hold.

allowed_write_paths: `.planning/phases/039-additional-validation/**`, `artifacts/evidence/additional-validation-039/**`, `scripts/run_live_campaign.py`, `scripts/campaign_execution.py`, `tests/test_live_campaign_preparation.py`, `evals/local-live-operation.json`, `tests/llm/test_local_live.py`, `docs/harness/progress.md`.

forbidden_changes: historical ledgers, results, reservations, prior reports, holdout84/confirmation60, unknown reservations, sibling product sources, provider fallback, paid usage, Terraform apply, external effects or human-review claims. Fake mode, gate max1, paid USD0; no provider calls in validation. Stop on incomplete snapshot, source ambiguity or gate failure. Plan-check is implementer self-assessment.
