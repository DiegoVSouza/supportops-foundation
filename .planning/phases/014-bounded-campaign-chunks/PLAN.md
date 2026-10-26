# Plan

- allowed_write_paths: `.planning/phases/014-bounded-campaign-chunks/**`, `scripts/campaign_batch.py`, `tests/llm/test_campaign_batch.py`, `artifacts/evidence/live-campaign-batches/**`, `docs/harness/progress.md`, `docs/knowledge/live-campaign-batches.md`.
- llm_mode: fake; no provider/credential access. Fake callbacks are explicit local test doubles.
- forbidden_changes: campaign CLI enabling, config/budget/approval changes, existing ledger schemas, datasets/graders/prompts, packages, Docker services, kit, sibling repos and unrelated `artifacts/tmp-pytest/`.
- Validation: focused fault/resume/controller tests, fast and full locked offline gates; store commands/exits and sanitized output. Docker limited to read-only Compose validation already present in the full gate.
- Stop condition: implementing real dispatch requires account-wide enforcement or pending authorization; retain the public CLI denial and document that gap.

1. Add meaningful synthetic tests for bounded chunks, resume of failures, uncertain dispatch, resource denial, deadlines/pacing, malformed outcomes and usage overruns.
2. Implement the controller using the existing ledger/lease, a required account guard and injected single-attempt callback. Save checkpoints before dispatch and after outcomes.
3. Execute regressions, record phase limitations and knowledge, review staged paths and commit locally.

Plan review: accepted. No production endpoint, adapter or retry behavior changes. A required account guard prevents implicit omission from the future integration contract; a callback is not evidence of a working whole-lab guard. The current CLI remains fail-closed. Independent clean-context review remains pending.
