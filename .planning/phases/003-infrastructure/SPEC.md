# Phase 003 — Package, CI, and local infrastructure

## Goal
Package P00 as an installable versioned library and provide reproducible checks and optional local service infrastructure.

## Acceptance criteria
- `uv.lock` pins direct and transitive dependencies; sources and versions are recorded in `docs/harness/sources.lock.json`.
- CI runs lint and full tests under `LLM_MODE=fake`.
- `make verify` runs real package checks and tests; no placeholder prints INCOMPLETE as a successful check.
- Docker Compose declares Postgres with pgvector, Redis, and LocalStack; `make doctor` reports actual versions/availability and fails meaningfully when unavailable.
- README explains fake/replay/live, cassette recording, data schema, golden-set updates, and reproducible demo.

## Scope
Local infrastructure only. Do not start external cloud services or publish artifacts.
