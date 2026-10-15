# Plan — Package and infrastructure

## allowed_write_paths
- `pyproject.toml`, `uv.lock`, `Makefile`
- `.github/workflows/**`, `docker-compose.base.yml`, `.env.example`
- `scripts/**`, `tests/**`, `README.md`, `README.pt-BR.md`
- `shared/**`, `docs/**`, `artifacts/**`

## forbidden_changes
- External deployment, publish, or live provider call.
- Editing kit or lab root outside this project.
- Claiming services are available unless commands confirm it.

## Tasks (plan review)
1. Package the library and pin dependencies; add fast/full validation commands.
2. Add fake-mode CI and optional Compose service definitions.
3. Implement doctor checks for Docker, Compose, ports, and Python/package versions.
4. Finish bilingual README, knowledge doc, evidence, and final contract gate.

## Validation
`LLM_MODE=fake uv run make verify`; `make doctor` reports environment state. Compose validation runs only if Docker is installed.

## Stop condition
If Docker or external dependencies are unavailable, record INCOMPLETE for the relevant integration gate and continue offline checks.
