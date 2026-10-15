.PHONY: verify test fast demo doctor

fast:
	uv run --locked python scripts/check_fast.py

test:
	uv run --locked python -c "from pathlib import Path; Path('artifacts/tmp').mkdir(parents=True, exist_ok=True)"
	uv run --locked pytest -q --basetemp=artifacts/tmp/pytest

verify:
	uv run --locked python scripts/check_full.py

demo:
	uv run --locked python demo/foundation_demo.py

doctor:
	uv run --locked python scripts/doctor.py
