# Plan

## Tasks

1. Reconcile policy totals, provider usage, and P01/P04 reservation events; define fixture-backed allocation expectations. (Self plan-check: PASS; scope and ownership align with the user-authorized P00 correction.)
2. Replace capacity-equality reserve inference with verified applied-migration allocation accounting. Reconcile ledger-backed retained reservations separately and add meaningful tests for migrated capacity not yet reserved, historical reservations, and unknown usage.
3. Validate in fake mode, capture command/cwd/exit/output under phase 038 evidence, and preserve the historical phase 037 gate result. Prepare a clean snapshot for exactly one separately authorized full gate.

## allowed_write_paths

- `scripts/run_live_campaign.py`
- `tests/test_live_campaign_preparation.py`
- `.planning/phases/038-live-allocation-reconciliation/**`
- `artifacts/evidence/live-allocation-reconciliation-038/**`

## Validation and budget

- Offline fake mode only during implementation; no provider credentials or network dispatch.
- One full fake gate only, on a new isolated snapshot, using the user's explicit additional-gate authorization. Historic phase 037 remains 3/3.
- Stop on ledger ambiguity, any mutation outside owned paths, or full-gate failure. Preserve failure output; no second gate.

## Forbidden changes

Do not modify existing phase 037 files, root policy/ledgers, other project files, reservations, operation IDs, holdout84, confirmation60, generated results, or unrelated untracked evidence.
