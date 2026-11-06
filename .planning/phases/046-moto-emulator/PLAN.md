# Plan

1. Verify moto S3/SQS/SNS operations against an owned container (`artifacts/evidence/moto-services-046/run.py`).
2. Swap the service in `docker-compose.base.yml`, `scripts/doctor.py`, `docs/harness/sources.lock.json`, READMEs.
3. Record result; update feature status only from saved evidence.

allowed_write_paths: `.planning/phases/046-moto-emulator/**`, `artifacts/evidence/moto-services-046/**`, `docker-compose.base.yml`, `scripts/doctor.py`, `docs/harness/**`, `README.md`, `README.pt-BR.md`.
forbidden_changes: other containers, campaign state, provider requests. llm_mode: fake; budget: USD 0.
