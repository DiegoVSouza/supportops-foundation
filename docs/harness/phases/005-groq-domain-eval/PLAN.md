# P00 execution plan

## Task 1 — Add offline regressions

Add mocked tests for Groq-only model preflight, fail-closed provider behavior, response/domain assertion, budget limits, key rotation, and retry classification. No tests may use the network.

## Task 2 — Correct the Groq live evaluation path

Update `scripts/smoke_groq.py` to remove OpenRouter fallback, default to the verified Groq model, evaluate one synthetic SupportOps case through `LiveClient`, and write a separate sanitized phase-005 artifact. Keep the existing adapter and fake/replay contracts intact.

## Task 3 — Verify and record

Run focused tests and the documented full P00 gate, then run one live case if the authenticated model check and existing USD 0.05 budget allow it. Save commands, exit codes, and sanitized output.

## Ownership

`allowed_write_paths`: `docs/harness/phases/005-groq-domain-eval/**`, `scripts/smoke_groq.py`, `tests/test_smoke_groq.py`, `pyproject.toml`, `uv.lock`, `README.md`, `docs/harness/decisions.md`, `docs/harness/progress.md`, and `artifacts/evidence/phase-005-groq-*`.

`forbidden_changes`: `harness-kit/**`, `.env`, other projects, `supportops_foundation/llm/**` unless tests demonstrate an adapter defect, previous evidence, datasets, and unrelated changes.

## Runtime, budget, and stop conditions

- Explicit `LLM_MODE=live`; Groq only; one ticket; max completion 256; timeout 15s; USD 0.05 cap enforced by P00 `Budget` before requests.
- Model listing is a separate no-generation preflight. At most one bounded key pass per request; 429 uses bounded provider guidance; auth, invalid model, malformed request, or budget/quota errors stop immediately.
- Use the official Groq SDK in the live script through a local HTTPTransport adapter so the existing LiveClient budget/schema accounting and injected offline transports remain intact. Pin the SDK only in the optional `live` extra; fake/replay imports must not require it.
- Normalize the SDK's nullable `tool_calls` field to an empty list in that local adapter; the first completed provider response showed the existing LiveClient contract expects an iterable field. Do not change the shared runtime API for this SDK serialization detail.
- Do not make a completion if model availability, explicit live configuration, credentials, or budget is missing. No fallback to OpenRouter or fake.

## Validation

Use the P00 documented offline gate and focused test file. Store exact command, exit code, and sanitized output in phase-005 evidence. Live output must not contain prompt text, headers, or key material.
