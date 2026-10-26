# Phase 011 — Live campaign preparation

## Goal

Prepare P00's owned evaluation inputs and a no-provider dry-run reservation for the broad live-readiness campaign. This phase does not authorize provider calls or change the public package/runtime contract.

## Current evidence and constraints

- Revalidated repository HEAD: `d5cda0e7394c9b4817a308b276e53d88b2944cd2` (`test(llm): verify Groq live client acceptance`).
- P00 has an unrelated untracked `artifacts/tmp-pytest/` directory; preserve it.
- The profile's `max_usd_per_task` is zero. The prior P00 phase decision records a separate bounded free-tier smoke, but no expanded campaign reservation is approved here.
- Existing smoke/evaluation artifacts do not establish the 40-case, three-trial quality gates in `.planning/llm-live-readiness/SPEC.md`.
- This phase must not read or expose credentials, instantiate an SDK, call a provider, modify Docker, or use a paid fallback.

## Acceptance criteria

1. A versioned P00 dataset contains 40 distinct semantic synthetic cases: 12 development and 28 sealed holdout, with reviewed expected behavior, rubric IDs, criticality, language/family metadata, and case/task call and token caps.
2. Split assignment avoids scenario-family/source leakage; duplicate detection and rubric contract checks include deliberate invalid predictions and fail graders appropriately.
3. Campaign configuration records the requested model and all required finite caps, but every unapproved expanded campaign ceiling remains `PENDING`; the free-tier exception and zero paid budget are reconciled in project decisions before any real call.
4. A dry-run reports case/trial/call counts, reservations, unresolved approvals and configuration gaps without SDK construction, network access, or Docker mutation. Generation is impossible when required limits or approval are unresolved.
5. Deterministic checks and artifacts record command, exit code, and sanitized output. No real evaluation result is claimed by this phase.

## Out of scope

Provider execution, local live promotion, changes to `supportops_foundation` public APIs, kit changes, cross-project imports, production deployment, key inspection, paid usage, or changing existing campaign history.
