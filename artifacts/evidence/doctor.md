# Local environment doctor

Command: `uv run --locked python scripts/doctor.py`

Exit code: **1**. Actual output:

```text
python=3.13.12
uv=uv 0.12.7 (61291a8ca 2026-08-27 x86_64-pc-windows-msvc)
docker=Docker version 29.1.3, build f52814d
docker_compose=5.0.1
supportops_foundation=0.1.0
postgres_127.0.0.1:5432=UNAVAILABLE
redis_127.0.0.1:6379=UNAVAILABLE
localstack_127.0.0.1:4566=UNAVAILABLE
compose_file=PRESENT
services are observed only; doctor does not start containers
```

Docker Compose configuration itself validates with exit code 0 as part of `artifacts/evidence/check-full.txt`. The Docker daemon-backed service E2E remains **INCOMPLETE**; the doctor intentionally does not start containers.
