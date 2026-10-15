# Phase 001 — Domain and testkit evidence

## Dependency resolution
- Command: `uv lock`
- Exit code: `0`
- Output: `Resolved 13 packages in 14ms; Added setuptools v84.0.0`.
- Pinned direct versions: Python `3.13.12` (local executable), Pydantic `2.14.1`, pytest `9.1.1`, setuptools `84.0.0`; complete transitive pins and hashes are in `uv.lock`.

## First test run
- Command: `uv run --locked pytest -q tests/domain tests/testkit`
- Exit code: `1`
- Output: `1 failed, 9 passed`; `test_tool_result_requires_error_only_for_failure` showed a Pydantic field validator did not run when the optional `error` defaulted to `None`.
- Root cause: validation depended on a field validator that did not validate the default value.
- Fix: replaced it with an after-model invariant requiring failures to have an error and successes to have none.

## Re-run
- Command: `uv run --locked pytest -q tests/domain tests/testkit`
- Exit code: `0`
- Output: `10 passed in 0.05s`.
- Coverage: required model fields, unknown-field rejection, timezone boundaries, positive invoice amount, tool-result consistency, escalation consistency, dataset cardinalities, 10 boundary cases, stable canonical hash for equal seeds, different hash for different seeds, and synthetic email domain.
- LLM mode: not exercised in this phase; no provider call occurred.
