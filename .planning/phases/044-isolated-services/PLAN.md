# Plan

1. Define a dedicated Compose configuration with ephemeral loopback ports and a unique project name.
2. Run service-specific operations, capture evidence and remove only the dedicated project resources.
3. Record results and update status only when supported by saved evidence.

allowed_write_paths: `.planning/phases/044-isolated-services/**`, `artifacts/evidence/isolated-services-044/**`, `docs/harness/decisions.md`, `docs/harness/progress.md`, `docs/harness/feature_list.json`.

forbidden_changes: other Docker projects, campaign ledgers, allocations, candidates, provider requests, and preexisting artifacts.

llm_mode: fake; budget: USD 0. Acquire the exact configured images when absent; stop if acquisition fails or Docker isolation or ownership cannot be established. Record each attempt and its exit code. This amendment permits local image acquisition, not substitution of versions or model calls.
