# Bounded P00 chunks

Offline controller result: PASS. Live campaign/promotion: INCOMPLETE.

- `uv run --locked python -m pytest tests/llm/test_campaign_batch.py -q --basetemp=artifacts/tmp/campaign-batches-014`: exit 0, 30 passed.
- `uv run --locked python scripts/check_full.py`: exit 0, 99 tests passed; fast, lint, format, compile, deterministic dataset and Compose configuration checks passed. Optional service E2E remains separately INCOMPLETE.
- `python -S scripts/run_live_campaign.py --stage pilot --dry-run`: exit 0.
- `python -S scripts/run_live_campaign.py --stage pilot`: exit 2, generation disabled before credentials/provider access.

Fault evidence covers process death during execution and before outcome persistence, lock recovery, uncertain reservation retention, result persistence followed by export failure, quota response, account rejection, accounting overrun and cumulative cap exhaustion. Completed semantic failures are retained and skipped on resume. Ten is the maximum new attempt count per chunk; P00 performs no retries.

The initial missing-module red run, default-temp permission failure and first lint failure are preserved separately. Focused tests use an isolated ignored scratch directory instead of changing the inaccessible system temp directory. Saved output has line endings/trailing whitespace normalized.

The controller requires a caller-supplied shared lease path and whole-account guard. Tests supply synthetic guards; these are not implemented account enforcement. The real launcher must still validate frozen dataset/candidate provenance, authorization, account-wide quotas/caps, model catalog and bounded request timeouts before using the controller. No current command invokes it against Groq. Human review, campaign trials and canary/rollback remain pending. No provider usage is claimed.
