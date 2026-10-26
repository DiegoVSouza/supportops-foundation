# Plan check — P00 phase 005 (recheck after preflight failure)

- Selected P00 because its purpose is a provider-neutral LLM client and it already has a Groq transport smoke.
- The prior live artifact proves only an OpenRouter fallback call, so the new run will use a separate Groq-only artifact.
- The plan reuses P00 `LiveClient` budget accounting, caps one case to 128 output tokens and USD 0.05, and keeps offline fake/replay behavior intact.
- Write ownership is P00-local; credentials, the kit, other projects, historical evidence, and datasets are forbidden.
- First live attempt stopped during stdlib model preflight with a sanitized network failure before completion. Evidence from the P01 SDK-backed preflight showed the official Groq SDK reaches the same model catalog, so the revised plan adds an optional pinned SDK extra and uses a local adapter to retain LiveClient budget accounting.
- SDK retries will be disabled internally; P00 key rotation remains bounded and retries only transient failures, with Retry-After capped at two seconds. Fake/replay remain SDK-independent.
- The revised ownership explicitly includes the optional dependency lock. This remains P00-local and excludes the kit, secrets, and prior evidence.
- The SDK-backed preflight succeeded for all configured credentials, but the first SDK-backed completion failed Pydantic JSON parsing at the prior 128-token output cap. The plan now raises the cap to 256 while retaining the USD 0.05 preflight budget and one-ticket limit; output is still parsed and asserted locally.
- A later completion exposed an SDK serialization mismatch: `tool_calls: null` reached a LiveClient parser that expects a list. The implementation will normalize that nullable field inside the local SDK transport and test it offline; this keeps the shared runtime contract unchanged.
- Validation remains offline-first; a live call occurs only after authenticated model availability and budget checks.

**Plan recheck: PASS.** SDK use is optional to live execution, bounded by the existing client budget, and does not change the fake/replay contract. The output-cap increase remains well inside the configured spend ceiling.

**Plan check: PASS.** The implementation may begin after this review.
