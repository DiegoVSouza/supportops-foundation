# VERIFY — Groq live smoke and transient key rotation

- `python scripts/check_full.py`: must pass offline with fake mode.
- Focused LLM contract tests: must prove retries are bounded, 429 is not retried, and uncertain attempts remain reserved.
- Live run: one synthetic prompt against the listed model, USD 0.05 local cap, sanitized output saved with exit code. If credentials/provider access fail, record `INCOMPLETE` and the sanitized error.
- Review the staged diff for keys, generated files, and unrelated changes before the local commit.

## Execution results — 2026-10-23

- Offline gate: `uv run --locked python scripts/check_full.py` — exit 0; 35 tests passed, lint/format/compile and dataset contract passed. Output: `artifacts/evidence/phase-004-offline-gate.txt`.
- Groq model is listed as active in the official catalog. All five configured Groq credentials were rejected by the authenticated model-list endpoint (HTTP 401/403); no Groq completion was sent.
- Free fallback: `uv run --locked python scripts/smoke_groq.py` — exit 0; OpenRouter routed one synthetic request to `cohere/north-mini-code:free`, 11 input tokens, 56 output tokens, 3,737 ms, reported cost USD 0. Output: `artifacts/evidence/groq-live-smoke.json` and `.txt`.
- This is a live connectivity smoke only; it does not measure GPT-OSS 20B quality.
