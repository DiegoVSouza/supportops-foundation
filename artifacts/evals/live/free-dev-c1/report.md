# P00 development campaign

Status: `INCOMPLETE`. Human review: `PENDING`. Promotion: `INCOMPLETE`.

Recorded trials: 12/36; real model trials: 12; passed: 12.

Stop: `free_token_minute_checkpoint`.

Resume (no completed/uncertain replay):

```powershell
$env:LLM_MODE="live"; uv run --locked python scripts/run_live_campaign.py --resume free-dev-c1 --execute-free
```

Per-domain/family/language/errors and unique-case all-three Wilson intervals: see `report.json`. Raw synthetic answers are only in the private local review database. Provider accounting is authoritative in `../provider-usage.sqlite`; the logical trial ledger is not summed again.
