# Progress

- Kit initialization completed.

## 2026-10-15 — Intake and plan review

- Original P00 requirements were reconciled into three independent phases, each with SPEC, PLAN, and VERIFY before product implementation.
- Coordinator reviewed the plans and accepted all task boundaries, public contracts, failure cases, validation commands, and stop conditions.
- Phase 001 owns only domain/testkit paths; phase 002 owns the LLM protocol/modes; phase 003 owns packaging, local infrastructure, CI, and docs.
- Pydantic `2.14.1` and pytest `9.1.1` were checked against official documentation; uv `0.12.7` was read from the local executable. Sources and lock state are in `docs/harness/sources.lock.json`.
- Phases 001–003 have been executed and verified; audit follow-up and remaining service/model gates are recorded below.

## 2026-10-15 — Phase 002 and 003 implementation

- Phase 002 fake/replay/live contracts, ordered JSONL cassette parser/recorder, strict replay matching, provider transport injection, and spend preflight completed. No live provider calls were made.
- Phase 003 package setup, Ruff lint/format, compile/test gate, CI, optional local Compose, doctor, bilingual README, shared README, Makefile template, and interview knowledge docs completed.
- The initial contract was frozen as `1.0.0`; its local wheel and source provenance are recorded and were not published externally. Audit follow-up ADR-003 advances the current package to compatible patch release `1.0.1`.
- `artifacts/evidence/check-full.txt` records the full gate and Compose configuration. `artifacts/evidence/doctor.md` records service ports unavailable; local runtime E2E remains INCOMPLETE.
- Model quality, live cost, and latency metrics remain PENDING because no authorized real provider run occurred.

## 2026-10-15 — Audit follow-up

- Live budget reservations now reconcile provider-reported token usage under a lock; missing usage retains the preflight reservation, and observed overspend blocks subsequent calls. Fake-transport tests cover reconciliation, malformed/missing usage, and subsequent-call rejection.
- The generic adapter cannot guarantee a strict single-request provider-side cap after an unexpected usage overrun; a provider-enforced cap or verified provider quote/tokenizer is required. No live run was performed.
- Domain malformed-input coverage now exercises every exported model/enum. Golden tests assert all decision fields for the ten named boundary cases and all fifty standard cases. Phase 001 verification and `feature_list.json` now reflect observed results.
- Focused command output and exit codes are saved in `artifacts/evidence/phase-002-budget-reconciliation.txt` and `artifacts/evidence/phase-001-contract-coverage.txt`.
- Release `1.0.1` passed the offline full gate (32 tests), built a local wheel/sdist, and passed isolated offline wheel installation/import smoke. Commit and SHA-256 provenance are in `artifacts/evidence/package-provenance-1.0.1.md`; no external publication occurred.

## 2026-10-15 — Roadmap remediation assurance

- Re-ran `scripts/check_full.py`: exit 0; fast checks, Ruff lint/format, compile, 32 tests, deterministic 60-case dataset contract, and Docker Compose configuration passed. Output is saved in `artifacts/evidence/remediation-check-full.txt`.
- Docker Compose configuration parsing is PASS; service-backed PostgreSQL/Redis/LocalStack integration remains INCOMPLETE because the Docker engine is unavailable. Provider quality, cost, and latency remain PENDING without an authorized live run.

## 2026-10-23 — Phase 004 Groq live and key rotation

- Added a bounded Groq transport that rotates among configured keys only on transient transport failures, reserves cost for all possible attempts, and never rotates after HTTP 429. Fake transport tests cover timeout recovery and 429 stop behavior.
- P00 offline gate passed with 35 tests; evidence is in `artifacts/evidence/phase-004-offline-gate.txt`.
- Official Groq docs list `openai/gpt-oss-20b` as active at $0.075/M input and $0.30/M output. All five configured Groq credentials were rejected at model listing (HTTP 401/403), so no paid Groq inference occurred.
- One real OpenRouter free-router smoke completed successfully through `cohere/north-mini-code:free`: 11 input tokens, 56 output tokens, 3,737 ms, reported cost $0. Evidence is in `artifacts/evidence/groq-live-smoke.json` and `.txt`.
- This smoke confirms a real provider path but does not measure GPT-OSS 20B quality. Quality, cost, and latency for Groq remain PENDING until valid Groq credentials are supplied.

## 2026-10-26 — Phase 005 Groq domain evaluation

- Removed the silent OpenRouter fallback from the P00 evaluation and added an optional pinned official Groq SDK adapter to the existing budgeted LiveClient. Only `GROQ_API_KEY_1..4` are selected; fake/replay remain SDK-independent.
- The first attempt failed in urllib model preflight. SDK-backed attempts exposed invalid JSON at 128 tokens and nullable `tool_calls`; the transport now uses a 256-token cap and normalizes null tool calls before the existing parser.
- Final real run passed: GPT-OSS 20B, 147 input / 177 output tokens, USD 0.000064125 estimated cost, 844 ms, one attempt. The full P00 gate passed with 40 tests. Prior failure artifacts are retained; the OpenRouter run above remains historical and is not Groq evidence.

## 2026-10-26 — Live Docker acceptance

The foundation live smoke passed with 147 input and 94 output tokens. All 40 offline tests passed. This is client acceptance; the optional HTTP demo service E2E remains outside this run. Evidence: artifacts/evidence/live-docker/.

## 2026-10-26 — Phase 011 campaign preparation

- Added 40 unique synthetic cases in the fixed 12/28 development/holdout split with 24 English and 16 Portuguese cases across all seven required families. Dataset SHA-256: `b1e3f779acf7948b2da17aee937f57f6fd643c7b0b0bb78294d09d6bf0326849`.
- Added a code-first contract grader and malformed/wrong decision probes. The dry-run ran in Python `-S` and reported pilot 6 calls, development 36 calls, and holdout 84 calls without provider access, credential reads, or Docker mutation.
- Focused campaign tests: 20 passed. Full fake project gate: 60 tests passed; lint, formatting, compilation, deterministic fixture checks, and Compose config passed. Evidence: `artifacts/evidence/live-campaign-preparation/phase-011-preparation.md`.
- Dataset and rubric reviewer sign-off, free-tier quota/capacity, cumulative spend/token ceilings, timing limits, and durable campaign ledger remain `PENDING`; generation is disabled and no Groq request was made. Campaign readiness is `INCOMPLETE`.

## 2026-10-26 — Phase 012 bounded runner foundation

- Added a durable append-only ledger with reservation-before-result events, unknown-usage retention, immutable completed failures, cumulative request/token/estimated-cost checks, and a read-only resume inspection command.
- Added a cross-process OS lease primitive with secret-free metadata. Tests prove lease contention, append-only protections, crash-surviving reservations, immutable trials, and concurrent cap enforcement.
- Focused campaign checks passed (29 tests); P00 full offline gate passed (69 tests), including lint, format, compile, dataset contract and Compose config. Python `-S` pilot dry-run exited 0; execution exited 2 while prerequisites remain pending. No Groq credentials were passed to checks and no provider request occurred.
- This is a partial runner foundation, not an executable campaign: Groq preflight/dispatch, all-project lease and ledger integration, interrupted dispatch recovery, reviewed dataset/rubric, quota and cumulative authorizations remain pending. Phase status: `INCOMPLETE`. Evidence: `artifacts/evidence/live-campaign-runner/`.
## 2026-10-26 — Phase 013 confirmation token ceilings

- The offline dry-run now reports fresh-confirmation input/output maxima: 122,880 / 15,360 tokens from 20 cases, 3 trials, and unchanged 2,048 / 256 per-case caps.
- Focused preparation checks and fast/full fake gates passed; all three `-S` dry-runs exited 0. Paid ceiling remains USD 0; account quota and review approvals are `PENDING`, so campaign remains blocked.
- Evidence: `artifacts/evidence/live-token-reservations/`.