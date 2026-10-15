# Phase 002 — LLM modes

## Goal
Implement the frozen `LLMClient` contract with deterministic fake, traceable replay, and explicitly budgeted live modes.

## Acceptance criteria
- `LLMClient.complete(messages, schema=None, tools=None, model=None)` returns text, parsed value, tool calls, usage, estimated cost, latency, and model metadata.
- Fake responses are programmable and deterministic; no network calls occur in fake/replay.
- Replay consumes JSONL cassettes in order and raises a clear miss/mismatch error.
- Live fails closed without provider configuration or a positive `LAB_MAX_USD`; preflight prevents a request whose estimated/declared cost would exceed remaining budget.
- Tests cover malformed cassette, schema parse failure, budget boundary, missing credential, and provider error. No live call is executed.

## Contract
Public module `supportops_foundation.llm`; breaking changes require ADR and major version change.
