# Phase 002 evidence: fake, replay, and budget-gated live contract

Date: 2026-10-15. No provider was called and no paid request was made.

## Commands

1. `uv run --locked pytest -q tests/llm` — exit code **1**. Initial collection failed because `FakeReply` was not exported from the public module.
2. `uv run --locked pytest -q tests/llm` — exit code **1**. Six tests passed and three fixture setups failed because this environment denies access to the global pytest temp directory (`PermissionError: C:\Users\dvsdi\AppData\Local\Temp\pytest-of-dvsdi`).
3. `uv run --locked pytest -q --basetemp=.pytest-tmp tests/llm` — exit code **0**; output: `......... [100%]` and `9 passed in 0.09s`.

## Coverage

- Fake scripted response ordering, structured parsing, tool calls, usage and exhaustion.
- `get_llm()` defaults to fake and fails explicitly when replay lacks cassette configuration; no silent mode fallback.
- Cassette recording round-trips to exact ordered replay.
- Replay cassette order, exact request match, mismatch without consuming a record, exhaustion and malformed JSONL.
- Live missing endpoint/key, spend-cap preflight before transport, timeout reservation, structured parsing path and tool-call decoding through an injected transport.
- `LLM_MODE=fake` example defaults; API shape inspected against official documentation. The endpoint is generic OpenAI-compatible and requires per-provider compatibility verification.

The live transport is not exercised against a network. Provider-specific conformance, live latency, cost and quality metrics remain **PENDING**.

## Regression commands

- `uv run --locked pytest -q --basetemp=.pytest-tmp` — exit code **0**; output: `19 passed in 0.14s`.
- `uv run --locked python scripts/check_fast.py` — exit code **0**; output: `check-fast: OK`.
- `uv run --locked pytest -q --basetemp=artifacts/tmp/pytest tests/llm` — exit code **0**; output: `18 passed in 0.09s`.
