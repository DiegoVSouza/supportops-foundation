# Specification

Reconcile P00's applied campaign allocation with the current shared policy and retained P01/P04 logical reservations. Preserve the phase 037 failure and all existing worktree changes. Fix reservation derivation at its source and validate the full allocation contract against policy and ledger inputs.

## Scope

- Derive operating capacity from verified applied migration allocations; reconcile retained logical reservations separately. A ledger alone cannot establish unused capacity granted by a migration.
- Keep provider usage and logical reservations as separate accounting views; never release unknown reservations.
- Retain P00 confirmation (60) and holdout (84), P01/P04 historical reservations (12/6), and all existing consumed counters.

## Forbidden changes

- No changes to provider history, root policy, migration records, prior reports, holdout/confirmation, or unrelated/untracked evidence.
- No provider invocation in this phase. One additional full fake gate is separately authorized, once, on a fresh snapshot, preserving historical 3/3.
- No push, deploy, publication, or human-review/promotion claim.
