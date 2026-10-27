# Phase 019 offline validation

All commands ran in the locked P00 environment. Provider access and credential reads: none.

| Command | Exit | Result |
| --- | ---: | --- |
| `uv run --locked ruff check scripts/campaign_execution.py scripts/check_full.py tests/llm/test_campaign_execution.py` | 0 | All checks passed. |
| `uv run --locked ruff format --check scripts/campaign_execution.py scripts/check_full.py tests/llm/test_campaign_execution.py` | 0 | All files formatted. |
| `uv run --locked python scripts/check_fast.py` | 0 | `check-fast: OK`. |
| `uv run --locked pytest tests/llm/test_campaign_execution.py -q --basetemp artifacts/evidence/funded-candidate-continuation/tmp-focused` | 0 | 34 passed. Full output: `focused.out.txt`. |
| `$env:P00_PYTEST_BASETEMP='artifacts/evidence/funded-candidate-continuation/tmp-full'; uv run --locked python scripts/check_full.py` | 0 | 142 tests passed; lint, format, compile, deterministic dataset contract and quiet Compose config passed. Optional service E2E remains INCOMPLETE. Full output: `check-full.txt`. |
| `uv run --locked python scripts/run_live_campaign.py --help` | 0 | Existing CLI flags verified before any live command. |
| `$env:LLM_MODE='live'; uv run --locked python scripts/run_live_campaign.py --resume free-dev-c1 --execute-free --max-trials 10` | 2 (expected denial) | `INCOMPLETE / immutable_campaign_provenance_mismatch`; no client/provider was initialized and no campaign files were changed. Output: `old-resume-rejection.txt`. |

The full-gate pytest basetemp is owned by phase 019. The earlier `artifacts/tmp-pytest/` tree remains untouched. The root-phase failed P00 run is recorded separately and was caused by a stale assertion expecting the previous 126-call primary ceiling; it ran no live client or provider.
