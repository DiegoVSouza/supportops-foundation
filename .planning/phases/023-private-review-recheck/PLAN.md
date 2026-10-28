# Plan

1. Inspect current review UI, tests and instructions for storage, escaping, provenance, append-only authorship, correction, sampling and independent-review support.
2. Run locked focused tests with a phase-owned temporary directory; record commands and sanitized results, and document unresolved limits.

allowed_write_paths: `.planning/phases/023-private-review-recheck/**`, `artifacts/evidence/funded-candidate-continuation/private-review-recheck-023/**`. forbidden_changes: private answer/annotation databases, campaign artifacts and ledgers, prompts, datasets, provider access, external services and human approvals. LLM mode fake; budget USD 0 and zero provider calls. Stop if tests attempt to write actual review records or access a provider. Plan-check is self-assessment; independent review remains PENDING.
