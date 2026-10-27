# Plan — candidate continuity and allocation

## Tasks

1. Reconcile immutable pilot/development manifests, trial ledgers, provider receipts, audit evidence, current project HEAD/status, and cumulative allocation. Do not read credentials. Preserve unrelated `artifacts/tmp-pytest/` and all private runtime state.
2. Record a no-provider dry-run with exact candidate separation, arithmetic, pending reviews, protected confirmation, unknown reservations, and the explicit ten-call deficit. State the safe next action as blocked pending an allocation source; do not write or alter campaign manifests.
3. Validate the arithmetic and artifact schema offline, update only this phase's verification evidence, inspect the staged diff, and commit this planning/dry-run task locally if all checks pass.

## Ownership

allowed_write_paths:
- `.planning/phases/017-candidate-continuity-allocation/SPEC.md`
- `.planning/phases/017-candidate-continuity-allocation/PLAN.md`
- `.planning/phases/017-candidate-continuity-allocation/VERIFY.md`
- `artifacts/evidence/candidate-continuity-allocation/**`

forbidden_changes: product/runtime code, prompts, schemas, dataset, rubric, graders, thresholds, campaign manifests/trials/ledgers/receipts, shared policy/registry, confirmation reserve, root `.env`, private review storage, Docker services, sibling projects, lab kit, and all unrelated user changes.

llm_mode: offline only; no provider, no credential reads, no network.

budget: provider calls 0; paid USD 0. Existing financial estimate and request/token ceilings are read-only. No reallocation is authorized by this phase.

## Validation

- Recheck status and HEAD in the P00 Git and verify no unrelated changes are staged.
- Reconcile the immutable campaign manifests and existing ledgers without modifying them; compare logical ledger and provider usage separately.
- Validate exact arithmetic: 126 primary − 16 consumed = 110 available; fresh candidate development 36 + holdout 84 = 120; deficit 10; confirmation remains 60 calls / 122,880 input / 15,360 output.
- Confirm the original candidate's remaining 24 attempts are not available to the corrected candidate and no review status is represented as approval.
- Save each validation command, exit code and sanitized output under `artifacts/evidence/candidate-continuity-allocation/`.

## Stop condition

No generation or holdout unless a later owning-project allocation phase demonstrates a valid source for the ten-call deficit without reducing or underfunding any original project/stage commitment. Do not change IDs or migrate history to bypass this condition. The known `free-dev-c1` resume command is invalid for provenance and must not be used. Safe next command is an offline allocation dry-run only; no provider command is valid yet.
