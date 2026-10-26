# Live campaign preparation — planning checks

No provider calls or Docker mutations were made. The full gate ran with `LLM_MODE=fake` (set by `scripts/check_full.py`).

| Command | Exit | Result |
|---|---:|---|
| `uv run --project projects/p00 --locked python projects/p00/scripts/check_fast.py` | 0 | `check-fast: OK` |
| `uv run --project projects/p00 --locked python projects/p00/scripts/check_full.py` | 0 | Ruff check passed; 22 files formatted; compile passed; 40 tests passed; deterministic fixture contract passed at package 1.0.1 with digest `8d1a2cd8823a108d450010952ec8abf5717d3c0bec2a878603418867c78b3e76`; Docker Compose config parsed. |

The full gate reports `PRODUCT_CHECK=PASS`; optional service E2E remains `INCOMPLETE`. The output contained no provider credentials or expanded secret-bearing configuration. The separate pre-existing untracked `artifacts/tmp-pytest/` directory was left untouched; the check script used its own `artifacts/tmp/pytest` directory.
