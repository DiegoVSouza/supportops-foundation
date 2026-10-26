# `free-dev-c1` safe checkpoint

Status: `INCOMPLETE`; keep this candidate and ledger frozen for resume.

- Candidate commit: `b42a198246274db5f7feb17a247ef1fe90e662e6`.
- Scope: 12 development cases × 3 trials = 36 maximum; no holdout or promotion.
- Chunk 1: 10/10 attempts completed and passed, exit 2 because 26 remained.
- Chunk 2: 2 additional attempts completed and passed; account guard then denied more dispatch with `free_token_minute_checkpoint`, exit 2. No provider semantic or operational failures occurred; the denial happened before reservation/dispatch. Do not rerun any completed trial.
- Exact bounded commands and exits: `LLM_MODE=live uv run --locked python scripts/run_live_campaign.py --stage development --campaign-id free-dev-c1 --execute-free --max-trials 10` → exit 2 (`chunk_limit`, 10 attempted); `LLM_MODE=live uv run --locked python scripts/run_live_campaign.py --resume free-dev-c1 --execute-free --max-trials 10` → exit 2 (`free_token_minute_checkpoint`, 2 attempted). Safe output files: `chunk-1.txt` and `chunk-2.txt`.
- Current campaign: 12/36 real evaluated trials, 12 passed, 0 failed, 0 operational failures, 24 pending. Four complete cases each have three passing trials; other cases remain incomplete.
- Provider receipt usage for this campaign: 4,392 input / 1,402 output tokens, estimated USD 0.000750000. Account billing tier and exact daily token remainder remain `PENDING`.
- P00 pilot + development provider-account receipts: 16 calls, 6,711 charged input / 1,906 output tokens, estimated USD 0.001075125, one unknown-usage pilot attempt retained at its provider reservation. The P00 logical campaign ledger is more conservative: 7,284 input / 1,906 output, USD 0.001118100, because that same unknown pilot attempt retains its full 2,048-token project reservation rather than the provider transport's 1,475-token reservation. Both remain charged in their owning ledgers; do not sum them together.
- Last sanitized rate feedback: 1,000 request/day limit with 988 remaining at observation; 8,000 token/minute limit with 7,213 remaining and a 5.902-second reset at observation. These headers do not establish account tier or remaining daily tokens.
- Human, dataset, and rubric review remain `PENDING`; output is provisional. The earlier `free-pilot-v1` remains failed and untouched.

Read-only checkpoint validation: `uv run --locked python scripts/run_live_campaign.py --resume free-dev-c1 --dry-run` exited 0 with `provider_accessed=false`, `credentials_read=false`, 16 P00 ledger requests, and 12 completed `free-dev-c1` attempts. See `resume-dry-run.json` and `checkpoint-accounting.json`.

Safe resume after the account guard approves capacity again, with the same source and candidate:

```powershell
$env:LLM_MODE = 'live'
uv run --locked python scripts/run_live_campaign.py --resume free-dev-c1 --execute-free --max-trials 10
```

The command is capped at ten new trials; the runner must pass the shared account guard before each reservation. Stop and checkpoint again on any quota, resource, provider, provenance, or uncertainty result. No holdout, promotion, or new correction round is authorized here.
