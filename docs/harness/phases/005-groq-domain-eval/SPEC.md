# P00 Groq SupportOps live evaluation

## Status

Implemented and verified. SDK-backed evaluation passed after diagnosing urllib preflight connectivity and nullable `tool_calls` serialization from the official SDK.

## Goal and selection

Verify P00's provider-neutral `LiveClient` and Groq transport with one synthetic SupportOps case and a domain assertion. P00 is the foundation library, so the evaluation must exercise its explicit live client, token usage, budget reservation, response parsing, and offline fake/replay contracts.

## Existing finding

The prior `groq-live-smoke.json` says `PASS`, but records provider `openrouter-free` and model `openrouter/free` after all configured Groq credentials were rejected. It is not Groq evidence and demonstrates that the current smoke's provider fallback can mislabel the intended test. Preserve that historical artifact; this phase will write a separate Groq-only report and will never fall back.

## Requirements and limits

- Use the P00 live adapter with Groq `openai/gpt-oss-20b`; verify the model list before completion. No alternate provider/model fallback.
- Load lab-root `.env` silently, use only `GROQ_API_KEY_1` through `_4`, and never print or persist credentials or identifiers derived from them.
- Require `LLM_MODE=live` and the existing `LAB_MAX_USD` budget gate. Keep the P00 per-run cap at USD 0.05; cap completion at 256 tokens and timeout at 15 seconds.
- One synthetic delayed-parcel tracking question; structured assessment must choose `search_kb`, answer, and not escalate. Assert the returned assessment, not transport success alone.
- Retry only bounded transient failures and 429 with bounded `Retry-After`; never rotate on auth/model/validation errors. Stop at budget/quota exhaustion. Preserve fake/replay offline behavior.
- Store command, exit code, timestamps, model, usage, attempts, assertion outcome, estimated cost from verified published rates, and sanitized error class/status in a new phase artifact.

## Acceptance

1. Offline tests prove no fallback, bounded rotation/retry behavior, budget rejection, and domain assertion parsing.
2. A tiny Groq run succeeds or records a sanitized precise failure; its artifact clearly says provider `groq` and the actual returned model.
3. Full offline P00 verification remains green; old OpenRouter evidence remains unchanged.
4. No secret values occur in output or artifacts, and all metrics come from the real run or are `PENDING`.

## Scope

P00 only. Do not change `harness-kit`, other projects, the root `.env`, datasets, or historical artifacts. Existing P00 `LiveClient` and budget contract remain the implementation boundary.

## Verified references

- Model, published rate, capabilities: [Groq GPT-OSS 20B](https://console.groq.com/docs/model/openai/gpt-oss-20b).
- Free-plan limits and retry guidance: [Groq rate limits](https://console.groq.com/docs/rate-limits).
- Official SDK release used by selected Groq-integrated projects: [groq-python 1.7.0](https://github.com/groq/groq-python/releases/tag/v1.7.0).
