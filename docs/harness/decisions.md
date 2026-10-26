# Intake decisions — P00 Foundation

- Product: a versioned Python library providing SupportOps domain contracts, deterministic synthetic fixtures, and provider-neutral fake/replay/live LLM interfaces.
- Measurable success: `make verify` passes offline in fake mode; dataset hashes are stable for equal seeds; replay misses and live calls without an explicit budget/provider fail closed.
- Pattern: library and deterministic workflow, not a user-facing agent. No agent runtime or provider is selected.
- Profile: `workflow-automation` because the deliverable is a Python package for deterministic task workflows and test infrastructure; no agent, RAG, MCP, or production sampling modules are needed.
- Stack: Python 3.13, Pydantic v2, pytest. Exact versions are pinned in `uv.lock` and recorded in `sources.lock.json`.
- Runtime: none. `LLMClient` is an application protocol; fake and replay implementations run without network access. Live is an opt-in OpenAI-compatible HTTP adapter and must enforce `LAB_MAX_USD` before a request.
- Risk: generated data is synthetic; untrusted ticket text is modeled as data. Live mode sends prompts to an external provider, so it is disabled by default and requires an explicit positive budget and credentials. No paid calls are part of verification.
- Budget: fake/replay only in tests and CI; live budget is `0` unless explicitly supplied by the caller.
- Contract: public package `supportops_foundation` began at `0.1.0`; its first consumer-facing release was `1.0.0`. Audit follow-up ADR-003 releases compatible live-budget accounting as `1.0.1`. Incompatible changes require an ADR, semver bump, and consumer updates.
- Integration: P01–P04 may use local doubles during parallel implementation. P05 must consume approved, versioned local package artifacts; no sibling source imports or external publishing.
- Phase 005 decision (2026-10-26): evaluate one synthetic SupportOps ticket with Groq GPT-OSS 20B through the existing live client, under LAB_MAX_USD=0.05. Remove the prior OpenRouter fallback from this evaluation; the historical fallback run is not Groq evidence. Fake/replay remain default and offline.

## 2026-10-26 — Live Docker acceptance

Use opt-in Groq live mode with numbered credentials and authenticated model preflight. Preserve deterministic fake defaults and fail closed on provider/contract failures. Only local synthetic acceptance and the designated free allowance are authorized; billed cost remains PENDING. Evidence: artifacts/evidence/live-docker/.

## 2026-10-26 — Broad live campaign preparation

Phase 011 freezes a 40-case synthetic dataset (12 development / 28 holdout; 24 English / 16 Portuguese) and a no-provider dry-run contract. The P00 profile continues to authorize USD 0 per task; the prior single-case free-tier exception does not authorize the broad campaign or its 20-case confirmation reserve. All new quota, request, token, latency, and spend ceilings remain `PENDING`. Dataset/rubric review is `PENDING`; generation is disabled. No provider call was made.

## 2026-10-26 — Phase 012 bounded runner foundation

Added an append-only SQLite reservation ledger, conservative accounting for unknown usage, immutable trial events, cross-process OS lease primitive, and read-only resume inspection. Offline dry-run stays standard-library-only. The P00 profile remains USD 0 paid spend; free quota, cumulative caps and reviewer approval remain pending. The provider dispatcher, shared six-project ledger/lease integration and campaign execution are not implemented, so generation remains blocked and this phase is incomplete. No provider call was made.

## 2026-10-26 — Free-only campaign authorization and deferred review

The user now authorizes remaining synthetic evaluation within Groq's free plan and will review results after technical preparation. Bind P00 to the sourced shared policy and finite existing additive reservations, retaining USD 0 paid authorization and original 2,048/256 input/output caps. Explicit live mode plus `--execute-free` are required; fake/replay defaults and the established grader remain unchanged. Pending dataset/rubric/human review now blocks promotion/generalization rather than provisional engineering collection under this specific authorization.

Provider attempts and account limits are authoritative in `provider-usage.sqlite`; logical trial outcomes remain in `ledger.sqlite` and are not summed again as provider usage. Every model trial must reference a matching completed provider receipt. Candidate hashes cover only public sources/configuration/data, never credentials. Windows subprocess streams explicitly use UTF-8.

For the requested deferred review, store authorized synthetic assistant answers in an owner-only local review-application database outside artifacts/Git. Do not retain reasoning fields, secret-bearing logs or raw live cassettes. Human review and rollout/canary/rollback approval remain pending. The root authorization is `.planning/llm-live-readiness/AUTHORIZATION.md`; the policy is `shared/policies/groq-free-campaign.json` in the lab repository.
