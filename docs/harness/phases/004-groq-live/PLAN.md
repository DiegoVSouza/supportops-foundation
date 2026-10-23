# PLAN — Groq live smoke and transient key rotation

## Allowed write paths

- `supportops_foundation/llm/live.py`
- `supportops_foundation/llm/__init__.py`
- `scripts/smoke_groq.py`
- `tests/llm/test_clients.py`
- `docs/harness/phases/004-groq-live/**`
- `docs/harness/progress.md`
- `artifacts/evidence/groq-live-smoke.json`
- `artifacts/evidence/groq-live-smoke.txt`

## Steps

1. Add a bounded Groq HTTP transport that cycles configured keys only on transient transport failures, honors a conservative backoff, and does not retry 429.
2. Make P00 live preflight reserve enough budget for each possible attempt and retain estimates for attempts with uncertain outcomes.
3. Add an opt-in smoke script that reads the lab-root `.env` without printing values, verifies Groq model availability, and uses only OpenRouter's free router if Groq credentials/model are unavailable.
4. Add fake-transport tests for key rotation, bounded attempts, 429 behavior, and budget reservations.
5. Run the P00 offline gate, then the explicitly requested live smoke under USD 0.05; save command, exit code, and sanitized result.
6. Review and commit the staged diff locally.

## Stop conditions

- Stop before sending a completion if no valid Groq credential or OpenRouter key/model listing is available.
- Never fall back to a paid OpenRouter model or paid Hugging Face inference.
- Stop on 429 without switching keys; report the provider limit.
- Stop if a completion cannot fit the local budget.
