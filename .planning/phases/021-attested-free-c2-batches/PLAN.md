# Plan

1. Preserve committed candidate e56fd1f and fingerprint 56bef263770d396fe69d915bc8aea1bdc9a9109e83584d08e28377adbb01af6b; validate offline report and official model/free limits, then sanitized authenticated catalog preflight.
2. Execute at most ten fresh attempts per batch through the owning runner; reconcile after each and stop on provider error, checkpoint, uncertain work, critical failure, provenance drift or 36 trials. Save sanitized evidence and commit.

allowed_write_paths:
- .planning/phases/021-attested-free-c2-batches/**
- artifacts/evidence/funded-candidate-continuation/rotation-live/**
- artifacts/evals/live/free-dev-c2/**
- artifacts/evals/live/ledger.sqlite* (runtime only, never stage)
- artifacts/evals/live/provider-usage.sqlite* (runtime only, never stage)
- .runtime/llm-review/answers.sqlite* (private runtime only, never stage)
- docs/harness/progress.md
forbidden_changes: candidate sources, historical campaigns, policy/budgets, dataset/rubric/schema/prompts/graders, holdout, service lifecycle, credentials, fallback/retries, promotion.
llm_mode: explicit live, free only, USD 0 paid. Funded 36 development plus 84 future holdout; 60 confirmation protected; no extras.
validation_commands: existing locked full gate PASS (145); offline dry-run; root catalog preflight; LLM_MODE=live uv run --locked python scripts/run_live_campaign.py --stage development --campaign-id free-dev-c2 --execute-free --max-trials 10.
Plan-check: PASS (self-check). No human/independent approval inferred. Resume only same fingerprint with no uncertain work; never rerun semantic failures.
