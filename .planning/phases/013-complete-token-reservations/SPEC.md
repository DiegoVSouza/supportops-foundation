# Phase 013 — Complete P00 token reservation dry-run

## Goal

Expose conservative input/output token maxima for P00's fresh confirmation reserve in the existing offline campaign dry-run, so the account-wide inventory can report complete planned token ceilings without reading project config from outside its CLI.

## Constraints

- Campaign generation remains disabled. Paid budget is USD 0; account quota, cumulative caps, and human review remain `PENDING`.
- Do not change cases, expectations, rubrics, provider adapter, runtime, approval fields, or historical reports.
- Token estimates use frozen per-case caps as upper bounds; this adds no authorization.

## Acceptance criteria

1. Pilot/development/holdout dry-run JSON includes `confirmation_max_input_tokens` and `confirmation_max_output_tokens` calculated from fresh case count × trials × existing per-case maximum.
2. The dry-run remains Python `-S` compatible and provider/credential/network/Docker isolated.
3. A deterministic test proves the formula and zero paid spend/pending gates remain unchanged.
4. Fast/full fake tests pass; evidence is saved and the phase remains `INCOMPLETE` for live adoption.

## Out of scope

Changing caps/budget, live calls, ledger/dispatch behavior, datasets/rubrics, or sibling projects.
