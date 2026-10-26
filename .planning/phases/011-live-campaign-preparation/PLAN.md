# Plan — Live campaign preparation

## Execution controls

- `llm_mode`: `fake`; preparation and dry-run must run without provider access.
- `allowed_write_paths`:
  - `.planning/phases/011-live-campaign-preparation/**`
  - `evals/datasets/live-v1/**`
  - `evals/rubrics/live-v1/**`
  - `evals/live-campaign.json`
  - `scripts/run_live_campaign.py`
  - `tests/**` (focused campaign preparation tests only)
  - `docs/harness/decisions.md`
  - `artifacts/evidence/live-campaign-preparation/**`
- `forbidden_changes`: product runtime/package code, public APIs, other project repositories, harness-kit, root `.env`, credentials, existing live-docker artifacts, network/provider calls, Docker mutation, paid usage, publishing, push, or relaxing any campaign threshold.
- Budget source: P00 profile currently authorizes USD 0 per task. Existing phase decisions record a bounded free-tier smoke only. Expanded limits, free-tier quota/capacity and campaign reservation are `PENDING` and must be reconciled explicitly before generation; keys are not quota units.
- Validation: project fast/full checks in fake mode, campaign dry-run, dataset/grader contract checks, and offline runner safety tests. Save command, exit code and sanitized output under the evidence path above.
- Stop condition: stop before provider access if any budget approval, free-tier quota, model access, dataset review, rubric review, cap, or credential preflight is missing; retain a resumable preparation state and classify the campaign `INCOMPLETE`.

## Tasks

1. **Freeze cases and rubrics for review** — inspect P00 public contracts and current fixtures; author 40 unique synthetic semantic cases with the fixed 12/28 split, risk-family coverage, 60/40 English/Portuguese composition, expected decisions, allowed tools, forbidden behavior, rubric and finite per-case caps. Record review status as `PENDING` until an independent reviewer signs off; hash only public/synthetic content.
2. **Build guarded dry-run and reservation manifest** — add a project-local campaign config and CLI that validates --help/stage/config and reports planned cases, trials, maximum calls, reservations and unresolved fields without SDK/network/Docker access. Make actual generation fail closed on every `PENDING` ceiling or absent approval; preserve cumulative accounting design for later execution phase.
3. **Prove preparation contracts and record evidence** — test duplicate/split/family/language validation and graders with deliberate bad outputs; prove dry-run does not instantiate provider clients and incomplete budget blocks generation. Run applicable fake checks, save sanitized outputs, review the staged diff and update project progress only with observed results.

## Plan review

Coordinator review completed against the live-readiness spec, P00 client contract, and campaign arithmetic. The phase paths are product-local and the generation path remains blocked by zero paid budget and pending free-tier/review limits. Accepted for preparation execution on 2026-10-26. A clean-context verifier is still required for the finished phase gates.
