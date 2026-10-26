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
