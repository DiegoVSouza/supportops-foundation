# Plan

- allowed_write_paths: `.planning/phases/016-development-correction-one/**`, `agent/prompts/live-campaign.md`, `agent/schemas/live-decision.json`, `scripts/campaign_execution.py`, `tests/llm/test_campaign_execution.py`, `artifacts/evidence/development-correction-one/**`, `artifacts/evals/live/free-dev-c1/**`, `artifacts/evals/live/ledger.sqlite*` and `provider-usage.sqlite*` (untracked runtime logs through existing guard), `.runtime/llm-review/**` (untracked private review app), `docs/harness/progress.md`, `docs/harness/failures.md`, `docs/knowledge/free-campaign-execution.md`.
- llm_mode: fake for tests; explicit free-only live for the declared new development candidate after commit. USD 0 paid, same model/output limits and shared policy. Root transport/registry/common lease are used through the established subprocess contract; no sibling source imports or project initialization.
- forbidden_changes: original baseline artifacts, dataset/split/rubric/grader/thresholds, holdout execution, package dependencies/kit, existing services, credentials, budget expansion or public/external effects.
- Validation: contract/error/provenance/confirmation-reserve tests, full locked offline gate, rendered complete-payload bound; candidate commit before bounded development chunks. Save commands/exits/usage/error reports and exact resume command, with no raw answer/headers in artifacts.
- Stop condition: source/provenance mismatch, uncertain work, any resource/provider error, or more than the declared 36 development attempts. No undeclared correction round, semantic rerun or holdout-guided fix.

1. Clarify generic lookup/clarification semantics and freeze the strict existing output contract; retain categorical provider diagnostics and protect confirmation capacity.
2. Add regressions for hidden expected-field leakage, finite input bounds/schema provenance, error metadata redaction and confirmation budget; run full checks and commit candidate.
3. Execute the new candidate on the predeclared development cases/trials in chunks, record all results/checkpoints and update learning/evidence. Do not run holdout or promote in this phase.

Plan review: accepted. Development cases may guide correction under the original protocol; prior failures stay immutable. [Official structured-output documentation](https://console.groq.com/docs/structured-outputs) confirms strict support for the fixed model; schema decoding does not establish semantic correctness. Human/independent review remain pending.
