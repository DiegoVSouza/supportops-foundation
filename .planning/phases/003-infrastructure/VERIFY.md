# Verify — Package and infrastructure

- [x] Clean install from lockfile succeeds.
- [x] `LLM_MODE=fake uv run python scripts/check_full.py` runs lint, format, compile, contract checks, and all tests successfully.
- [x] CI workflow defines pinned uv sync, Ruff lint/format, and full fake-mode checks; the remote workflow run is **INCOMPLETE** because it requires a push, which was not authorized.
- [x] Compose config validates with Docker Compose. Runtime services were not started; service E2E remains INCOMPLETE.
- [x] Doctor output reflects actual versions and unavailable service ports.
- [x] README English and Portuguese, knowledge docs, and evidence are complete; metrics remain PENDING absent real model runs.
