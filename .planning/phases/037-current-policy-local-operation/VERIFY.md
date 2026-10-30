# Verification

Plan self-check PASS (`plan-check.md` and amendment self-check).

## Current facts and attempted work

- The applied root policy is SHA `f8428a8da06fd551e6a41d3d009db69d1d31c620eda68ef21a02ff1dbcc32cdf`; P00's existing ten-call operation allocation is unchanged. Provider-free dry-run reports 4/10 used and 6 remaining, P00 holdout 84 and confirmation 60 protected, paid USD 0, and no provider access. Current dry-run fingerprint is `75c6b1889bf6c03f7d3e9b5e3ffb5d62d67b73ef14314da39b1aeee1672c012a`; it differs from the last successful current-036 smoke binding `6021179839d958d4fc548a54063f384cd7237ae6b2fafb67c0836131eb49fbc9`.
- Root `.env` variable-presence audit found all five authorized Groq variable names populated; process environment does not export them. No values were emitted or copied into evidence. Official current Groq model/structured-output and rate-limit pages were checked; the model remains `openai/gpt-oss-20b`, JSON Schema Mode is listed, and the displayed base rate limits are not authenticated account quota.
- Updated the local-operation config policy binding and added a stale-policy fail-closed regression. These implementation edits are not committed because the required full fake gate is INCOMPLETE.
- Focused local-operation tests: PASS, 9 tests. Fast gate: PASS. Evidence: `focused.json`, `check-fast.json`.

## Full gate attempts (max_tries 3 exhausted)

1. Initial full gate failed because pytest's isolated basetemp parent did not exist: 93 setup errors; 64 passed and one further assertion failure was secondary to fixture setup. Evidence: `check-full.json`.
2. After creating a fresh parent and scratch directory, full gate ran: 157 passed, one failed. The applied-allocation test exposed stale expectations from the pre-migration P01/P04 policy. Evidence: `check-full-attempt2.json`.
3. A second correction aligned the P01/P04 operation counters and global totals to the current provider-free account snapshot. Full gate still had 157 passed and one failed: the same allocation test retains stale hard-coded P01/P04 primary remaining values (`744/558`, current observed `760/567`). Evidence: `check-full-attempt3.json` and `current-allocation.json`.

No fourth full-gate execution is allowed under this phase's three-attempt limit. The remaining test assertions are known to conflict with the applied root policy snapshot; no expectation was weakened. No current-037 binding was frozen and no live operation was invoked. The old current-036 smoke remains historical and does not validate this root-policy fingerprint. The exact attempted command for all full gates was `P00_PYTEST_BASETEMP=<fresh phase scratch> uv run --locked python scripts/check_full.py`; each used a distinct scratch path and saved exit/output above.

Next command only after a newly authorized repair attempt: reconcile all remaining static expectations in `tests/test_live_campaign_preparation.py` against a fresh read-only `applied_allocation` snapshot, then run the permitted owning gate if an attempt becomes available. Do not issue a provider call from this phase while the required full gate is incomplete. Human quality/dataset/rubric/independent review, holdout and promotion remain PENDING.
