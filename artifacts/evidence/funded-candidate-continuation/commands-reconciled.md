# Phase 019 applied-allocation reconciliation commands

All commands below ran offline. None read credentials or accessed a provider.

- `uv run --locked ruff check scripts/campaign_execution.py scripts/run_live_campaign.py tests/llm/test_campaign_execution.py tests/test_live_campaign_preparation.py` — exit 0, `All checks passed!`.
- `uv run --locked ruff format --check scripts/campaign_execution.py scripts/run_live_campaign.py tests/llm/test_campaign_execution.py tests/test_live_campaign_preparation.py` — exit 0, four files already formatted.
- `uv run --locked pytest tests/test_live_campaign_preparation.py tests/llm/test_campaign_execution.py -q --basetemp artifacts/evidence/funded-candidate-continuation/tmp-final-focused` — exit 0, 57 passed. Output: `focused-reconciled-final.txt`.
- `$env:P00_PYTEST_BASETEMP=''artifacts/evidence/funded-candidate-continuation/tmp-final-locked''; uv run --locked python scripts/check_full.py` — exit 0, 144 passed; check-fast, lint, format, compile, dataset contract and Compose config passed. Optional service E2E remains INCOMPLETE. Full output: `check-full-locked.txt`.
- `uv run --locked python scripts/run_live_campaign.py --help` — exit 0; output: `cli-help-reconciled.txt`.
- Earlier full-gate attempt `check-full-reconciled.txt` stopped at format check (exit 1) because two lines in the amended `campaign_execution.py` had noncanonical wrapping. `ruff format` applied formatting only; the complete rerun above passed. No tests or gates were weakened.
- `pre-reconciliation-cli-dry-run.json` is retained as a stale-config diagnostic: it exposed the historical 186/380928/47616 values and is not allocation evidence. The authoritative final dry-run is generated after the candidate source commit.