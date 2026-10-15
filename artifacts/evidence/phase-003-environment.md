# Phase 003 environment evidence

- `uv lock --check` — exit code **0**; output `Resolved 14 packages in 0.61ms`.
- `uv sync --locked` — exit code **0**; output `Checked 14 packages in 1ms`.
- `uv run --locked python scripts/check_full.py` — exit code **0**. Full command/output is in `check-full.txt`: Ruff lint, format, compile, 28 tests, deterministic dataset contract, and Docker Compose config all passed.
- `docker compose -f docker-compose.base.yml config` — exit code **0**, executed by the full check. Postgres/Redis/LocalStack containers were not started; port availability and doctor result are in `doctor.md`.
- `uv run --locked make verify` — exit code **2**; `error: Failed to spawn: make` on this Windows environment. The cross-platform Python gate above is used instead. The Makefile target remains available where GNU Make is installed.
- Remote CI workflow execution — **INCOMPLETE**; no push or hosted workflow dispatch was authorized.
- Real service integration/E2E — **INCOMPLETE**; Compose syntax passed but runtime ports were unavailable and containers were not started.
