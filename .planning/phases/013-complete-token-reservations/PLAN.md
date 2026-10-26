# Plan — Complete P00 token reservation dry-run

## Execution controls

- `llm_mode`: `fake`; no provider/network/Docker.
- `allowed_write_paths`:
  - `.planning/phases/013-complete-token-reservations/**`
  - `scripts/run_live_campaign.py`
  - `tests/test_live_campaign_preparation.py`
  - `docs/harness/progress.md`
  - `artifacts/evidence/live-token-reservations/**`
- `forbidden_changes`: root/project `.env`, campaign budgets/approvals, dataset/rubric, runtime/provider code, history, sibling repositories, harness-kit, or product behavior.
- Budget: paid USD 0. Token counts are ceilings only, not authorization to spend account quota.
- Validation: focused preparation tests, `-S` dry-run for stages, project fast/full fake gate. Restore any historical check output overwritten by existing check scripts.
- Stop condition: no provider call; unresolved quota/review remains `INCOMPLETE`.

## Tasks

1. Test expected confirmation token ceilings from the frozen reserve and per-case caps.
2. Add the fields to the CLI reservation summary without changing the caps or authorization blockers.
3. Run offline gates, save evidence, review staged paths, and commit.

## Plan review

The change only fills a missing dry-run reporting field found by the account-wide aggregation. It preserves the existing 20 fresh cases × 3 trials and current per-case token caps, and cannot enable generation. Accepted on 2026-10-26.
