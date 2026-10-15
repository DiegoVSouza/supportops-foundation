# Phase 001 — Domain contracts and testkit

## Goal
Deliver the immutable P00 domain contract and deterministic synthetic SupportOps fixtures in the independent P00 repository.

## Acceptance criteria
- Export Pydantic v2 models `Customer`, `Ticket`, `TicketCategory`, `Priority`, `Invoice`, `KBArticle`, `ToolCall`, `ToolResult`, `AgentRun`, and `TriageDecision` from `supportops_foundation.domain`.
- Generate 40 customers, 200 tickets, 30 KB articles, and 80 invoices from a seed, with stable canonical JSON and SHA-256 for equal seeds.
- Provide a 60-case golden set with expected category, priority, action, and escalation decision; include at least 10 explicit boundary/adversarial cases.
- Provide pytest fixtures and tests for validation, references, determinism, and boundary cases.
- Freeze the first consumer-facing schema in `docs/decisions/ADR-001-domain-contract.md`; package version starts at 1.0.0.

## Scope
The original P00 brief is adapted to this project root. No agent behavior, HTTP API, observability, or deployment is included.
