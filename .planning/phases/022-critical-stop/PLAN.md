# Plan

1. Add a regression that proves a critical first result prevents a second dispatch, while preserving the finalized first result and ordinary semantic failure behavior.
2. Implement and verify the explicit critical stop in the real campaign binding and batch controller; save sanitized command output and update verification.
3. Repair the full-gate allocation regression so it checks accounting invariants against the current read-only ledger rather than assuming the earlier sixteen-call snapshot; preserve the failed gate evidence.

allowed_write_paths: `.planning/phases/022-critical-stop/**`, `scripts/campaign_batch.py`, `scripts/campaign_execution.py`, `tests/llm/test_campaign_batch.py`, `tests/llm/test_campaign_execution.py`, `tests/test_live_campaign_preparation.py`, `artifacts/evidence/funded-candidate-continuation/critical-stop-022/**`, `docs/harness/progress.md`, `docs/harness/feature_list.json`.

forbidden_changes: campaign manifests, historical results, runtime ledgers, prompts, datasets, rubrics, budgets, policy, other projects, credentials, provider execution, holdout, promotion.

llm_mode: fake; budget: zero provider calls and USD 0. Validation: locked focused tests, fast check and full offline gate; preserve pre-existing untracked files. Stop on unexpected historical changes, external access, or failed gate. Source scripts are fingerprinted: changes create a new candidate and invalidate C2 resume; historical C2 remains immutable. A new 36-trial campaign plus 84 holdout requires 120 calls against 107 primary remaining, a deficit of 13; no generation is authorized by this plan. Confirmation 60 remains protected.

Plan-check: self-assessment; independent review PENDING. Two tasks and owned paths are explicit. This phase fixes one local stop condition; it does not solve account attribution or approve a new campaign.
