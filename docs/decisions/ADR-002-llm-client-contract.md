# ADR-002: Freeze the provider-neutral LLM client contract

- Status: Accepted; contract frozen in P00 v1.0.0.
- Date: 2026-10-15.
- Context: independently built projects need deterministic clients and explicit live spend gates without tying the shared API to a provider SDK.
- Decision: expose `LLMClient.complete(messages, *, schema=None, tools=None, model=None)` and `LLMResponse` with text, parsed value, tool calls, token usage, estimated cost, latency, and model/provider metadata. `get_llm()` selects `fake`, `replay`, or `live` from an explicit argument or `LLM_MODE`; missing replay/live configuration fails closed. Fake is the default. Replay requires a validated JSONL cassette and exact ordered requests. Live requires endpoint, credential, explicit model, caller-verified token rates, and positive `LAB_MAX_USD`; reserve a worst-case estimate before transport. Tests use injected transport and never make network requests.
- Recording: `CassetteRecorder` writes one JSON object per line. Callers must review and redact sensitive prompts before retaining cassettes.
- Versioning: incompatible client/response changes require a new ADR, major semantic version, and explicit consumer upgrades.
- Consequences: fake/replay fixtures are regression tools and are not model-quality measurements. Provider-specific endpoint compatibility and real cost/latency remain pending until authorized runs exist.
- Alternatives considered: silently fallback to fake on missing live configuration (rejected because it hides failed production configuration); one provider SDK in the public library (rejected because it couples all consumers to one vendor and complicates offline tests).
