# Plan — funded C2 continuation

## Tasks

1. Pin the authorized C2 identity/scope and amended primary-versus-confirmation arithmetic against root phase 005; preserve historical manifests/quality and all registry/ledger identities. Plan-check and commit planning separately before implementation.
2. Implement the narrow C2 scope, amended primary ceiling and applied-policy/ledger-identity preflight gate; add source/budget/old-resume/ID-stage regressions and run focused plus full locked gates. Preserve unchanged payload/schema/prompt/data/rubric/graders. Save evidence, review staged diff and commit the candidate before calls.
3. After root migration apply and official/authenticated preflight: save final no-provider dry-run, run only up to thirty-six new development trials in ≤10-attempt batches, checkpoint/reconcile and prepare the existing private review queue. Commit sanitized evidence/state separately. Do not run holdout or claim pending reviews/promotions.

allowed_write_paths:
- `.planning/phases/019-funded-candidate-continuation/**`
- `scripts/campaign_execution.py`
- `scripts/check_full.py` (extend the existing isolated pytest path allowlist to this phase's evidence subtree; preserve default and prior temp trees)
- `tests/llm/test_campaign_execution.py`
- `artifacts/evidence/funded-candidate-continuation/**`
- `artifacts/evals/live/free-dev-c2/**`
- `artifacts/evals/live/ledger.sqlite*` and `artifacts/evals/live/provider-usage.sqlite*` (existing append-only runtime state; never stage)
- `.runtime/llm-review/answers.sqlite*` (protected append-only raw answers; never stage)
- `docs/harness/decisions.md`
- `docs/harness/progress.md`
- `docs/harness/failures.md`
- `docs/knowledge/funded-candidate-continuation.md`

forbidden_changes: historical pilot/C1 artifacts, dataset/splits/rubric/graders/thresholds, prompt/schema behavior, UI source during evaluation, root policy/registry without root phase 005, other projects/kit/dependencies/services, credentials, paid use, fallback/retries, holdout, canary and promotion.

llm_mode: fake/replay for checks and dry-run; explicit free-only live only after migration/gates/candidate commit. Budget: thirty-six new development attempts maximum, unchanged 2,048/256 per-call caps and 60-call protected confirmation; 84 calls remain reserved for later holdout. Extra correction/judge/canary allocation: none. Paid authorization USD 0.

Validation commands:
- `uv run --locked pytest tests/llm/test_campaign_execution.py -q --basetemp artifacts/evidence/funded-candidate-continuation/tmp-focused`
- `uv run --locked python scripts/check_fast.py`
- `P00_PYTEST_BASETEMP=artifacts/evidence/funded-candidate-continuation/tmp-full` then `uv run --locked python scripts/check_full.py`; extend the existing explicit allowlist and preserve all pre-existing temp trees.
- Offline current-source, policy/registry/UUID and complete payload-bound dry-run; no key/provider access.
- Verify `scripts/run_live_campaign.py --help` before using existing flags. Planned execution: `LLM_MODE=live ... --stage development --campaign-id free-dev-c2 --execute-free --max-trials 10`; resume only `--resume free-dev-c2` with the same committed fingerprint and no uncertain work. Final concrete command is recorded after actual gates and allocation, not inferred from this plan.

Stop conditions: root migration not applied, dirty/untracked source/schema, identity/provenance drift, cap/quota/provider error, uncertain work, critical failure or thirty-six total C2 attempts. Never edit a manifest/ledger to bypass a stop. Pending human/independent/quality gates remain explicit.
