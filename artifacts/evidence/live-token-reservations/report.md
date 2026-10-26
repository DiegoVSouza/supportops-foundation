# Phase 013 — P00 confirmation token ceilings

Status: `INCOMPLETE` for live adoption. Dry-run now exposes token ceilings for the fresh confirmation reserve; account quota and approvals remain pending.

## Evidence

| Command | Exit | Result |
|---|---:|---|
| `uv run --locked pytest tests/test_live_campaign_preparation.py -q --basetemp artifacts/evidence/live-token-reservations/pytest-temp` | 0 | Focused preparation tests passed. |
| `uv run --locked python scripts/check_fast.py` | 0 | Fast gate passed. |
| `uv run --locked python scripts/check_full.py` | 0 | Full fake project gate passed with 69 tests. Historical `artifacts/evidence/check-full.txt` was restored after capturing this phase's output. |
| `uv run --locked python -S scripts/run_live_campaign.py --stage {pilot,development,holdout} --dry-run` | 0 each | Each stage reports confirmation maxima of 122,880 input and 15,360 output tokens. |

The ceilings are computed from 20 fresh cases × 3 trials × the existing per-case caps (2,048 input / 256 output tokens). They do not change quota, spend authorization, or generation state.
