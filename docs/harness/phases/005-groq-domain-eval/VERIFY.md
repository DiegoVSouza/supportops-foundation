# P00 verification

## Plan gate

- Verify plan paths are P00-local and protect `.env`, historical artifacts, and the kit.
- Confirm the previous OpenRouter result is not reused as Groq evidence.
- Confirm model, token, timeout, request, retry, and USD 0.05 limits are explicit.

## Offline gate

- Run the new mocked tests and P00 full gate with `LLM_MODE=fake`; confirm no network request.
- Save command, exit code, and output to `artifacts/evidence/phase-005-groq-offline.txt`.

## Live gate

- Load root `.env` without printing values; query Groq's authenticated model list and require `openai/gpt-oss-20b`.
- Send one synthetic ticket case through P00's `LiveClient` with budget enforcement and evaluate the required tool/decision assertion.
- Save sanitized run JSON and command output under `artifacts/evidence/phase-005-groq-live.*`.
- Inspect artifact and diff for secret leakage and provider fallback.

## Completion gate

- Fake and replay remain offline/deterministic; full gate passes or the result is explicitly `INCOMPLETE`.
- Metrics are based on the real call only; cost is `PENDING` if usage or authoritative rate is unavailable.
- Run `git diff --check`, review staged paths, and commit locally without pushing.

## Recorded result — 2026-10-26

- Plan recheck passed after the first stdlib model-list request failed before completion. The official SDK preflight then confirmed the model across the four numbered credentials.
- Offline: focused LLM + Groq transport tests passed (28); full P00 gate passed (40 tests, lint, format, compile, dataset contract, compose config).
- Live: `LLM_MODE=live uv run --extra live python scripts/smoke_groq.py`; exit 0. Actual model `openai/gpt-oss-20b`; 147 input / 177 output tokens; estimated cost USD 0.000064125; latency 844 ms; 1 attempt; decision/tool/escalation assertions all passed.
- Diagnosed and retained earlier attempts: stdlib preflight network failure; invalid JSON at the old 128-token limit; and SDK `tool_calls: null` causing a parser TypeError. The live adapter now uses the SDK and normalizes that field locally; the output cap is 256 under the same USD 0.05 budget.
- Evidence: timestamped `phase-005-groq-live-*.json/.txt`, `phase-005-groq-live-attempt-001.*`, and `check-full.txt`. The old OpenRouter artifact was not reused or overwritten.
