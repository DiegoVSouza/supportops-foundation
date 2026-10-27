# Commands and exits

Working directory: `C:\estudo\Golpe\lab\projects\p00`. All Python execution used `uv run --locked`.

| Command | Exit | Evidence |
| --- | ---: | --- |
| `uv run --locked python scripts/check_fast.py` | 0 | `check-fast: OK`; also included in full gate |
| `uv run --locked pytest tests/llm/test_review_ui.py -q --basetemp artifacts/evidence/private-review-ui/tmp-run` | 0 | `focused.txt` |
| `$env:P00_PYTEST_BASETEMP='artifacts/evidence/private-review-ui/full-gate-pytest'; uv run --locked python scripts/check_full.py` | 0 | `check-full.txt`: 140 tests passed |
| `uv run --locked python artifacts/evidence/private-review-ui/verify_local.py` | 0 | `local-probe.json` |
| `uv run --locked python scripts/review_ui.py --help` | 0 | Actual CLI supports `--host` and `--port`; host is validated before binding |
| Locked Python owner-only annotation-directory verification and before/after Docker identity comparison | 0 | `privacy-check.txt`; no annotations written; identical container identities |

Inspected installed versions: Python 3.13.12, pytest 9.1.1, Ruff 0.17.0, Pydantic 2.14.1 and Groq SDK 1.7.0. No SDK or package dependency was changed. Line endings of phase-owned saved command outputs were normalized to LF before staging; substantive output is retained.

Earlier development checks exposed an import-path error, inaccessible system pytest temp storage, incorrect fixture selection, a test incorrectly reopening a read-only database in write mode, and lint/format errors. These were corrected before the passing checks. Temporary fixture stores are phase-owned and removed after validation; pre-existing `artifacts/tmp/pytest` and `artifacts/tmp-pytest` are preserved. No failed check was deleted or weakened to change a product expectation.

Plan-checks were manual reviews by the implementing agent. They are not independent verification and have no subprocess exit code. Recorded subprocess checks provide the machine evidence. Independent clean-context verification remains PENDING.
