# Phase 016 offline candidate evidence

All commands ran from `projects/p00` with the locked `uv` environment. No credentials or provider endpoints were accessed by these checks.

| Command | Exit | Result |
|---|---:|---|
| `uv run --locked pytest tests/llm/test_campaign_execution.py -q --basetemp artifacts/evidence/development-correction-one/tmp/pytest-focused` | 0 | 17 passed |
| `uv run --locked python scripts/check_fast.py` | 0 | `check-fast: OK` |
| `uv run --locked python scripts/check_full.py` | 0 | 116 passed; lint, format, compile, dataset and Compose checks passed; optional service E2E remains incomplete |
| `uv run --locked python scripts/run_live_campaign.py --help` | 0 | Existing execute/resume flags confirmed |
| `uv run --locked python scripts/run_live_campaign.py --stage development --dry-run` | 0 | 12 cases, 36 trials, no credentials/provider access |
| Offline payload-bound command over all development cases | 0 | 12 payloads, 1,512–1,611 UTF-8 bytes including schema; max 2,048 |
| Offline usage snapshot from `provider-usage.sqlite` | 0 | 4 prior attempts; unknown usage retains full reservation |
| `git diff --check` | 0 | No whitespace errors |

An initial pytest attempt using the Windows global temporary directory exited 1 because pytest could not enumerate `pytest-of-dvsdi`. A rerun with the phase-owned `--basetemp` initially exited 1 because its parent had not yet been created. The phase-owned scratch directory was then created, and the focused command above passed. The unrelated pre-existing `artifacts/tmp-pytest/` was preserved.

## Frozen source checks

The working diff contains no changes to the dataset, split manifest, rubric, grader, thresholds, pilot artifacts, or holdout. Their current SHA-256 values are:

| File | SHA-256 |
|---|---|
| `evals/datasets/live-v1/cases.jsonl` | `b1e3f779acf7948b2da17aee937f57f6fd643c7b0b0bb78294d09d6bf0326849` |
| `evals/datasets/live-v1/manifest.json` | `86b056d2a516ef180a901af77b0953c4252b0932b6344517bda0820557959766` |
| `evals/rubrics/live-v1/rubric.md` | `5d9b1b9803eff41f92bc9fe789c9deb757d36f7a859ee53f7b8c01a1f15fe1e9` |
| `scripts/run_live_campaign.py` | `2b9facbe5e941b244243266bd34eb29b7e003a9d71b2ef5abbf83615d758eac2` |
| `agent/schemas/live-decision.json` | `e2fdc1f0a0c8a0cda002d6ac24b0bee46ecaf255ecacab6947df60111f24a829` |

Dataset, rubric, and human review remain `PENDING`. This evidence is offline engineering evidence only and makes no live-quality or approval claim.
