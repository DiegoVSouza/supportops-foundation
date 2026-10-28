# Plan

1. Run locked fast/full gates with a fresh owned temp directory; preserve unrelated outputs.
2. Save a new committed-source offline C2 dry-run and review instructions; update progress and verification, inspect staged diff, and commit.

allowed_write_paths:
- .planning/phases/020-credential-rotation-provenance/**
- artifacts/evidence/funded-candidate-continuation/rotation-provenance/**
- docs/harness/progress.md

forbidden_changes: runtime, historical campaigns, ledgers, secrets, prompts/schema/dataset/rubric, root files, services.
llm_mode: fake/offline; zero provider calls; USD 0 paid.
validation_commands: uv run --locked python scripts/check_fast.py; uv run --locked python scripts/check_full.py; uv run --locked python scripts/run_live_campaign.py --dry-run --stage development --campaign-id free-dev-c2.
stop_condition: dirty source, failing gate, provenance mismatch or missing account verification. Generation stays INCOMPLETE.
Plan-check: PASS (self-check); two tasks, bounded paths and no budget expansion. Independent/human review PENDING.
