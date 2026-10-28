# Private review and safe inspection

The completed development candidate failed provisionally (27/36). Review p00-live-025, p00-live-026 and p00-live-037 across all three trials; preserve the original expectations and candidate provenance while deciding whether the prompt/contract needs correction. These are reviewed by actual humans, never by generated annotations. Inspect all critical/suspected failures; the critical p00-live-037 still requires semantic inspection even though the implemented deterministic critical flag was false.

From the P00 directory, safe offline commands:

```powershell
uv run --locked python scripts/run_live_campaign.py --resume free-dev-c2r1 --dry-run
uv run --locked python scripts/review_ui.py --host 127.0.0.1 --port 8765
```

Use the one-session access token printed locally by the launcher; do not copy it into tracked evidence. The UI reads protected synthetic answers and immutable candidate/dataset/prompt/schema/rubric provenance. Annotations are separate, append-only, authored and UTC-dated; corrections reference previous annotation IDs. Independent role/identity is self-declared and must be fulfilled by a genuinely separate reviewer. Navigation is provider-free and scripts are disabled. Stop the server with Ctrl+C.

Dataset/rubric review, primary semantic review, independent review/disagreement resolution and approval remain pending. No holdout exists for this candidate. Future holdout requires the original sealing and approval protocol, including the stratified 20% unique-case sample and double review of at least 20% of that sample, plus all critical/suspected cases. Current development navigation is not held-out acceptance.

Do not execute live resume: all 36 planned trials are already complete and immutable, development failed and only the protected 84 holdout/60 confirmation calls remain. No corrected-candidate or canary budget is available. Contract resolution and fresh explicitly funded development are required before evaluating a corrected candidate; do not borrow reservations or rename a campaign to bypass this result.
