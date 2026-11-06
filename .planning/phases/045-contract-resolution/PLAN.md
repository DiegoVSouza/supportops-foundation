# Plan

1. Record the owner decisions in `docs/harness/decisions.md` (done in this phase).
2. Impact check (read-only): list every artifact binding `content_sha256` b1e3f779... (free-dev-c1/c2/c2r1, free-pilot-v1, current-034/035/036 bindings) and confirm how holdout/confirmation protection depends on the dataset hash.
3. Only if the check shows a changed dataset cannot be reconciled with protected holdout/confirmation reservations without bypassing a gate: stop and ask the owner. Otherwise create a new dataset version (`p00-live-v2`, copy not in-place edit) with the 037 change, a new manifest hash, and a dataset-review note.
4. Reconcile the generic prompt with the "no identifier, no lookup" rule in a separate prompt phase with regression tests.
5. Any new development campaign needs separate explicit budget authorization; holdout (84 primary) and confirmation (60) reservations stay untouched.

allowed_write_paths: `.planning/phases/045-contract-resolution/**`, `docs/harness/decisions.md`.

forbidden_changes: `evals/datasets/live-v1/**` in place, prompts, graders, campaign ledgers, allocations, provider requests.

llm_mode: fake; budget: USD 0.
