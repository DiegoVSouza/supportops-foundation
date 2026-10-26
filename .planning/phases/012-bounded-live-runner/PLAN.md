# Plan — bounded P00 campaign runner

## Controls

- `llm_mode`: fake for validation; no provider call in this phase.
- `allowed_write_paths`: `.planning/phases/012-bounded-live-runner/**`, `scripts/run_live_campaign.py`, `scripts/campaign_runtime.py`, `supportops_foundation/llm/**` (only if required to add a no-fallback bounded adapter), `tests/test_live_campaign_preparation.py`, `tests/llm/**` (relevant runner contracts only), `evals/live-campaign.json` (schema/defaults only; all unresolved values stay PENDING), `docs/harness/decisions.md`, `docs/harness/failures.md`, `docs/harness/progress.md`, `artifacts/evidence/live-campaign-runner/**`, `docs/knowledge/live-campaign-runner.md`.
- `forbidden_changes`: dataset cases/manifest/rubric, review states, roots `.env`, credentials, historical evidence, sibling projects, harness-kit, provider/network access, Docker, public APIs, thresholds, budget/quota increases, publishing, push.
- Budget: profile paid cap USD 0; finite free quota and expanded request/token/estimated-cost reservations are PENDING. This phase has zero provider calls.
- Stop condition: any implementation path that could contact Groq during offline validation, unresolved write ownership, or pending values being treated as unlimited.

## Tasks

1. Implement and test CLI stages, durable append-only attempt ledger, cap reservations, safe resume and uncertain-dispatch stop behavior. Keep dispatch unreachable while any current campaign prerequisite is PENDING.
2. Implement one shared configured machine-local lease, fail-closed contention/stale-lock recovery, no-secret metadata, Groq-only numbered-key preflight and explicit no-fallback adapter wiring behind resolved approval gates. Prove all behavior with injected offline transports.
3. Run P00 fast/full checks and offline isolation/crash/cap/lease regressions; save command, exit code and sanitized output. Update decisions/failures/progress/knowledge, inspect the staged diff, and commit the implementation atomically.

Plan review: accepted for planning commit on 2026-10-26. Write paths are P00-owned. This implementation phase does not authorize provider calls; dataset and budget gates remain pending. A clean-context phase verifier remains required before claiming the project phase gate complete.
