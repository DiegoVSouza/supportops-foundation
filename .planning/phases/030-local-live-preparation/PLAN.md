# Plan

1. Update the generic live prompt to require a non-sensitive reference before choosing a lookup when the record cannot be identified; preserve the frozen historical results and unresolved category decision.
2. Verify deterministic payload construction and run locked fake full gate with dedicated scratch; record command, exit and output. Document model quality and review as PENDING.

allowed_write_paths: `.planning/phases/030-local-live-preparation/**`, `agent/prompts/live-campaign.md`, `artifacts/evidence/local-live-preparation-030/**`, `artifacts/evidence/funded-candidate-continuation/local-live-preparation-030/**` (full-gate scratch), `docs/harness/progress.md`.
forbidden_changes: datasets, rubrics, expected outcomes, historical campaigns, usage ledgers, budget, provider calls, approvals and other projects. Mode fake; paid USD 0; zero provider calls. max_tries: 3, persisted per failure. Plan-check is implementer self-assessment; independent review pending. Stop on regression, uncertain work or missing operational allocation.
