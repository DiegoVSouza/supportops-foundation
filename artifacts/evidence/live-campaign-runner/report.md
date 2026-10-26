# Phase 012 — P00 bounded runner foundation

## Status

**INCOMPLETE.** This commit implements offline reservation, lease and resume-inspection primitives. The Groq catalog preflight, live dispatcher, cross-project accounting/lease integration and campaign execution are not implemented. Dataset/rubric review, quota and cumulative limits remain PENDING. No provider request was made.

## Implemented

- Append-only SQLite campaign events with durable reservations before results. Update/delete triggers preserve historical attempts. Unknown usage retains the full request/token/estimated-cost reservation.
- `BEGIN IMMEDIATE` serializes cumulative totals and reservations so concurrent launchers cannot both claim remaining request capacity. One P00 ledger is reused across campaign IDs so project caps cannot reset. A crash-surviving reservation is classified uncertain; a case/trial already reserved or completed cannot be reserved again.
- A cross-process OS lease primitive writes only PID, hostname, campaign ID and timestamp. A separate process is blocked while held; normal exit releases it. The lease has not yet been connected to the CLI dispatcher or all projects.
- Resume inspection opens the ledger read-only and reports trial status/usage without credentials or provider access.
- Python `-S` dry-run uses standard library only. Execution exits 2 while approvals/limits remain pending.

## Evidence

| Command | Exit | Result |
|---|---:|---|
| `ruff check` and `ruff format --check` for the four changed Python files (exact argv in `focused-checks.txt`) | 0 | lint and formatting passed. |
| `uv run --locked pytest tests/llm/test_campaign_ledger.py tests/test_live_campaign_preparation.py -q --basetemp artifacts/evidence/live-campaign-runner/focused-final-3` | 0 | 29 focused tests passed, including interprocess lease, concurrent caps, append-only journal, unknown usage and read-only resume. |
| `uv run --locked python scripts/check_full.py` | 0 | 69 project tests; fast, lint, format, compile, deterministic dataset and Compose-config gates passed. Optional service E2E remains incomplete; P00 is a library/CLI, with no service route in scope. |
| `uv run --locked python -S scripts/run_live_campaign.py --stage pilot --dry-run` | 0 | six-case pilot; all unresolved gates visible; no credentials/provider/Docker. |
| `uv run --locked python -S scripts/run_live_campaign.py --stage pilot` | 2 | blocked as expected while generation/limits/reviews are unresolved. |

The first pytest attempt could not enumerate the Windows global temp directory (`PermissionError`). Re-running with the project-owned basetemp passed. The pre-existing `artifacts/tmp-pytest/` directory was preserved.

## Remaining work before phase completion

1. Define and implement the common machine ledger/lease contract consumed by all six project launchers; per-project accounting alone cannot enforce account-wide quota.
2. Implement Groq-only numbered-key catalog preflight and one-call-per-trial dispatch, behind explicit resolved authorization, finite free quota, requests/tokens/estimated-cost caps and pacing. Never treat four keys as four quotas.
3. Test process termination before/after dispatch, uncertain outcomes, ledger recovery and no repeated call; connect stage resume to only never-attempted trials.
4. Complete independent semantic/rubric review and freeze candidate, model, source, latency/queue targets and human review capacity.
5. Finish clean-context review, then run only an explicitly authorized bounded pilot.

No paid budget was raised. P00 paid cap remains USD 0; free-tier quota and all new cumulative reservations are unresolved. Broad evaluation and local-live promotion remain PENDING.
