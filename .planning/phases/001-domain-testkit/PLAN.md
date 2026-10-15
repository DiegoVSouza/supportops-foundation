# Plan — Domain contracts and testkit

## allowed_write_paths
- `supportops_foundation/domain/**`
- `supportops_foundation/testkit/**`
- `tests/**`
- `docs/decisions/ADR-001-domain-contract.md`
- `artifacts/**`
- `pyproject.toml`, `uv.lock`

## forbidden_changes
- `harness-kit/**`, lab root, or any sibling project.
- LLM runtime, provider calls, or infrastructure in this phase.
- Silent edits to published schema after freeze.

## Tasks (plan review)
1. Define and test Pydantic domain models and serialization invariants.
2. Implement seeded synthetic data generation and canonical hashing.
3. Build the 60-case golden dataset, including 10+ boundaries, and pytest fixtures.
4. Record ADR-001, lock dependencies, evidence, and update the package exports.

## Validation
`uv run pytest -q tests/domain tests/testkit`; deterministic hash comparison runs twice in one test process.

## Stop condition
Stop before implementation if domain fields conflict with the original brief or a consumer-facing name must change; record an ADR and coordinate an explicit versioned update.
