# Live checkpoint and private review

Candidate 7099cc5d0f4d576d14f28f7dab4648b074b59740; fingerprint 56bef263770d396fe69d915bc8aea1bdc9a9109e83584d08e28377adbb01af6b. Model openai/gpt-oss-20b. User attests authorized keys 1..4 belong to distinct Free accounts; the API does not verify billing. Official reference: https://console.groq.com/docs/rate-limits (checked 2026-10-27); configured 30 RPM/1000 RPD/8000 TPM/200000 TPD, conservative aggregate enforcement retained.

Batch 1: 10 new trials, CHUNK_COMPLETE, CLI exit 2 because overall campaign remains incomplete. Batch 2: 3 new trials then free_token_minute_checkpoint, CLI exit 2. STOP preserved; no replay or key bypass. C2: 13/36 trials passed grader, zero critical/operational failures, four complete three-trial cases plus one partial case. 23 trials remain. No old candidate results transfer. Holdout untouched.

Total cumulative calls 29. Known actual usage 9995 input/2999 output. Unknown historical pilot reserve remains 1475/256 transport and 2048/256 logical. Provider ledger charged bound 11470/3255, estimated economic USD 0.001836750; logical bound 12043/3255, USD 0.001879725. These represent the same consumption; never add them. Actual amount billed UNKNOWN; paid authorization USD 0. C2 known usage 4759/1349. Remaining primary 107 calls = 23 C2 + 84 future holdout. Confirmation 60 calls/122880 input/15360 output protected. No extras funded.

Review queue now includes thirteen C2 responses alongside sixteen historical records. Start privately from projects/p00:

```powershell
uv run --locked python scripts/review_ui.py --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765/login using the session token from the private terminal. Responses remain protected; annotations append-only. Actual human/independent/dataset/rubric reviews remain PENDING. No quality/generalization/promotion approval.

After the minute window resets, with unchanged fingerprint, no uncertain new work and unchanged user-attested Free accounts, the bounded resume command is:

```powershell
$env:LLM_MODE='live'
uv run --locked python scripts/run_live_campaign.py --resume free-dev-c2 --execute-free --max-trials 10
Remove-Item Env:LLM_MODE
```

Do not resume old free-dev-c1. Reconcile after each chunk and stop on quota/provider error/guard/provenance/critical or uncertain work. Account topology is not provider-verified and no per-account quota multiplier is implemented.

Private UI verification: PASS for all 29 records with thirty-second request timeout; first five-second probe timeout preserved in private-review-command.json. Answer/history hashes unchanged, zero annotations and zero provider requests. This is navigation verification only.
