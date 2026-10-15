# ADR-001: Freeze the SupportOps domain contract

- Status: Accepted for implementation; release freeze occurs with P00 v1.0.0.
- Date: 2026-10-15.
- Context: P01–P04 need a shared vocabulary, but their repositories and Git histories remain independent. Relative sibling imports would couple builds and violate reproducibility.
- Decision: expose Pydantic v2 models from `supportops_foundation.domain`: `Customer`, `Ticket`, `TicketCategory`, `Priority`, `Invoice`, `KBArticle`, `ToolCall`, `ToolResult`, `AgentRun`, and `TriageDecision`. Enum values are lowercase strings. Models reject unknown fields. Ticket timestamps must include timezone; invoice amounts are positive decimals; tool result success/error fields are consistent.
- Versioning: during P00 implementation the package is `0.1.0`. After all P00 phases and tests pass, freeze the schema as `1.0.0`. Any incompatible field/type/enum change requires a new ADR, semver major version, and explicit consumer upgrades.
- Consequences: other projects can use local contract doubles while P00 is unfinished. Real P00 integration requires a locally built versioned wheel; record version, source commit, and wheel SHA-256 in the consumer. Never import a sibling source directory or publish the package externally.
- Alternatives considered: shared monorepo source paths (rejected because projects have independent Git repositories); duplicating contracts without a consumer contract (rejected because schemas would silently drift).
