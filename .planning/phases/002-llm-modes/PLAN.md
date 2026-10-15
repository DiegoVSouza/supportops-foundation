# Plan — LLM modes

## allowed_write_paths
- `supportops_foundation/llm/**`
- `tests/llm/**`
- `artifacts/**`
- `docs/decisions/**`
- `pyproject.toml`, `uv.lock`, `.env.example`

## forbidden_changes
- No live provider calls or paid requests.
- No domain schema changes without ADR and version update.
- No sibling repository imports.

## Tasks (plan review)
1. Specify message/tool/usage/response types and the client protocol.
2. Implement scripted fake and ordered JSONL replay with negative tests.
3. Implement configurable HTTP live adapter with budget preflight and explicit failures.
4. Add cassette tooling, environment example, evidence, and regression tests.

## Validation
`uv run pytest -q tests/llm`; all provider tests use fake transports, never network.

## Stop condition
Stop if provider pricing cannot be verified or budget can only be enforced after a paid request; mark live integration incomplete.
