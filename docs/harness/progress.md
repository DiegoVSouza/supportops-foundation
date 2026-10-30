# Progress

## 2026-10-28 — Phase 031 provisional local-live boundary

- Added an explicit synthetic local-live command using the accounted provider subprocess, stable caller request IDs, one attempt, no fallback and conservative stop on duplicate, uncertain or previously failed work. Eight injected cases and the locked full fake gate passed (156 tests). Initial lint failure and intermediate gate are preserved under artifacts/evidence/local-live-operation-031/.
- The command is disabled pending a separate root migration and shared guard that reserve a finite operational envelope without consuming the 84 holdout or 60 confirmation calls. No provider request occurred. Quality/human evaluation is deferred as requested; no approval is fabricated.

## 2026-10-28 — Phase 030 provisional local-live preparation

- Updated the generic prompt to ask for a missing non-sensitive record reference before selecting a lookup. Initial locked fake gate failed 12 tests because the expanded prompt exceeded the existing request bound; the shortened version passed the complete fake gate with 148 tests. Failure and correction evidence: artifacts/evidence/local-live-preparation-030/.
- This is a new unevaluated source candidate. Historical failed development results remain attached to their original immutable candidate. Human evaluation is deferred per user instruction; no live acceptance, provider call or operational budget is implied. An accounted operational allocation and actual runtime integration remain pending.

## 2026-10-28 — Current phase 028 outcome

- Root +13 free-only migration is explicitly authorized/applied, with registry UUID and all historical prefixes/unknown reserves preserved. Full local fake gate passed 148 tests. Operational provider failures now block resume before client construction; live reports publish no executable resume suggestion.
- Replacement `free-dev-c2r1` completed 36 planned trials on candidate `43737f7c75475579d8bae099f9ec01b47feb0e88`, source fingerprint `7b1e79cae5ef397c45be36dac5860489e7ad858fb6e6817a88f3b46896763dc9`: 27 passes, nine semantic failures across three cases, no operational failures or deterministic critical flags. Final gate is FAIL_PROVISIONAL/exit 1, not live approved. Historical C2 remains immutable at 13/36.
- All 65 cumulative receipts/reservations reconcile. Primary remaining is exactly 84 protected holdout calls; confirmation 60 remains protected, with no corrected-development/judge/canary spare. Billed amount is UNKNOWN, paid authorization USD 0. Slots 0–4 are user-attested Free; historical key/organization attribution remains unknown.
- Private navigation passed for all 65 records with zero annotations/provider access and unchanged protected hashes. Actual human/dataset/rubric/independent review, contract resolution, fresh correction funding, holdout, generalization and promotion remain pending. Review the three failed cases using `artifacts/evidence/funded-replacement-028/REVIEW.md`; do not execute historical live commands below.
- Evidence commit `09d8c1e` preserves campaign results, batch commands/exits, final reconciliation and cause-level analysis. Documentation-only updates do not change the evaluated source fingerprint.

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
## 2026-10-26 — Phase 014 bounded campaign chunks

- Added the deterministic single-attempt controller with at most ten new trials per chunk, required account guard under the caller-configured shared lease, pre-dispatch reservation/checkpoint, pacing/deadline checks and immutable semantic failures on resume.
- Thirty focused tests and the full locked offline gate (99 tests, lint/format/compile/dataset/Compose checks) passed. Process-death tests prove uncertainty survives execution/outcome-persistence interruption and the OS lease can be recovered; export failure after persisted completion does not cause replay. Quota, account denial, malformed usage, cap exhaustion and accounting overrun stop safely.
- The public CLI remains denied (exit 2); the dry-run still exits 0 under Python `-S`. Synthetic callbacks do not implement the whole-account guard, real provider timeout/catalog/approval boundary or six-project launcher integration. Campaign, independent review, quality and promotion remain INCOMPLETE. No provider request or Docker service mutation occurred. Evidence: `artifacts/evidence/live-campaign-batches/`.

## 2026-10-26 — Phase 015 free-only campaign binding (offline candidate)

- Implemented explicit live/free opt-in, finite shared account policy binding through a root subprocess, frozen source/dataset/prompt/config manifests, sanitized outcomes/slices and per-case all-three Wilson reporting. The prior broad-campaign authorization PENDING state is superseded by the user's free-only instruction; human review remains pending.
- Full locked offline gate passed 111 tests plus lint/format/compile/dataset/Compose checks. Fixture integration tests prove no synthetic callback is counted as a real provider trial, semantic failures cannot replay, artifact tampering cannot override the immutable ledger, and UTF-8 pipe transport protects Portuguese text without inheriting provider keys.
- All 40 rendered requests fit current caps; the six-case pilot reserves at most six calls and 12,288 / 1,536 input/output tokens. Private review state is outside Git/artifacts with owner-only access. No generation yet at this entry; commit the candidate before the bounded real pilot. Campaign completion, human review and promotion remain INCOMPLETE. Evidence: `artifacts/evidence/live-campaign-execution/`.

## 2026-10-26 — Free pilot baseline preserved

- Committed candidate `476fae54e239cfc7c2200831662ef1af2af52e27` then executed `free-pilot-v1` once. The run stopped with exit 2 after four requests: three real responses failed existing routing expectations (one also tool selection), and one provider error stopped the chunk. Two planned trials remain; no semantic failure was rerun and holdout remains untouched.
- Known provider usage is 844 input / 248 output; the failed request's unknown usage retains its 1,475 / 256 reservation. Aggregate charged usage is four requests / 2,319 input / 504 output, estimated economic value 0.000325125 USD; billing remains PENDING and paid authorization stays zero. Authenticated limits observed match the configured free request/day and token/minute ceilings.
- Actual private review directory/database ACL checks passed; runtime databases are ignored. The baseline exposed a diagnostic gap (transport request-schema reason lost HTTP/code detail and became configuration in trial artifacts) and a prompt-policy ambiguity about choosing a lookup versus asking for information. These need follow-up correction before more generation; do not change grader/holdout expectations. Campaign/promotion remain INCOMPLETE. Evidence: `artifacts/evals/live/free-pilot-v1/` and `artifacts/evidence/live-campaign-execution/`.
- The first post-run ACL readback failed because inheritance removal left explicit grants. Scoped owner/ACL reset/grant repair and independent readback now verify owner-only directory/database access. The added Windows fault regression injects extra explicit permissions and confirms rejection/removal; the full gate passed 112 tests after repair. No further provider call occurred during this correction, and the runtime fingerprint change deliberately blocks silent continuation of the old candidate.

## 2026-10-26 — Phase 016 development correction, checkpointed

- Candidate b42a198246274db5f7feb17a247ef1fe90e662e6 adds generic lookup-versus-clarification semantics, strict existing JSON schema decoding, a deterministic complete-payload builder/bound, schema fingerprinting and sanitized typed HTTP/error diagnostics. Dataset, manifest, rubric, grader, thresholds and pilot remain unchanged.
- Focused regressions passed (17); the locked full gate passed (116 tests, lint, format, compile, dataset and Compose checks). All 12 frozen development payloads fit the conservative 2,048-byte serialized bound. The offline dry-run reserved 36 attempts in 10/10/10/6 chunks and retained the 60-call confirmation reserve.
- free-dev-c1 ran after candidate commit. Two chunks completed 12/36 real model trials; all 12 passed, with 0 semantic/operational failures. The second chunk stopped after the account guard returned free_token_minute_checkpoint; 24 attempts remain. Safe read-only resume dry-run exited 0. Do not rerun completed trials.
- Provider accounting reports 4,392 / 1,402 input/output tokens for development. Across pilot and development, provider receipts charge 6,711 / 1,906, with one unknown prior attempt retained at its 1,475-token provider reservation; P00 logical ledger conservatively retains the attempt full 2,048-token project reservation (7,284 / 1,906). These ledgers are reconciled separately, not added together. Billing tier and exact daily remaining tokens stay PENDING.
- Status: INCOMPLETE. Human/dataset/rubric review remains PENDING; the pilot remains failed; holdout and promotion were not run. Evidence: artifacts/evidence/development-correction-one/.

## 2026-10-27 — Phases 017–018 continuity and private review

- Phase 017 preserves all old candidates, attempts, UUIDs and unknown-use reservations. Read-only SQLite reconciliation confirms sixteen attempts, known usage 5,236/1,650, transport charged total 6,711/1,906 and logical charged total 7,284/1,906. The original 24 pending trials cannot migrate to a corrected candidate. A fresh 36-trial development plus 84-trial holdout requires 120 calls; only 110 primary calls and 30,350 output tokens remain. The exact deficient dimensions are ten calls and 370 output tokens. Confirmation remains protected at 60 calls/122,880 input/15,360 output. No policy/registry migration or provider call occurred. Evidence: `artifacts/evidence/candidate-continuity-allocation/`.
- Phase 018 implements a loopback-only authenticated private review UI, escaped answer/context/history, dataset/receipt provenance checks and separate owner-only append-only annotations. It prepares candidate-specific family/language stratification and double-review selection, with OS author plus declared reviewer/role. Historical pilot schema absence is explicit; no historical manifest is rewritten.
- The private queue contains sixteen records: three failed pilot responses, one pilot operational error with no response, and twelve old-candidate development responses across four unique cases. Actual authenticated local navigation returned 200 for all sixteen; unauthorized/invalid-token access returned 401. The protected answer database and immutable campaign files were unchanged and no annotation was written. Human/independent/dataset/rubric review remains PENDING.
- Locked focused gate passed nine tests; locked full gate passed 140 tests plus lint/format/compile/dataset/quiet-Compose checks. Existing temporary output trees were preserved using a dedicated full-gate pytest path. Optional product service E2E remains INCOMPLETE; no Docker stack was changed.
- Start: `uv run --locked python scripts/review_ui.py --host 127.0.0.1 --port 8765`; reviewer instructions and evidence are in `artifacts/evidence/private-review-ui/README.md`. This source change requires a new final candidate freeze and valid allocation before any future generation. It does not transfer quality evidence or approval from historical candidates.

## 2026-10-27 — Phase 019 funded C2 implementation

- User authorization `p00-free-envelope-plus10-v1` funds exactly ten additional free-only P00 calls through root phase 005. The owning P00 controller now allows only fresh live `free-dev-c2` development and sets the primary ceiling to 136 calls / 278,528 input / 34,816 output / USD 0.0313344; the 60-call confirmation reserve remains intact.
- Before live campaign artifacts or a provider client can be initialized, P00 verifies the exact amended policy allocation, canonical policy SHA against the root registry, the registered P00 provider-ledger UUID, and absence of the durable pending-migration marker. C1 development resume is rejected with `immutable_campaign_provenance_mismatch`; other IDs/stages fail before filesystem effects.
- The focused campaign execution tests pass 34 cases. The locked full P00 gate passes 142 tests plus lint, format, compile, deterministic dataset contract and quiet Compose config. Optional local service E2E remains INCOMPLETE. Evidence is in `artifacts/evidence/funded-candidate-continuation/`.
- The source changes are committed after offline gates and staged review. The immutable C2 campaign manifest/source inventory and dry-run remain PENDING until root phase 005 is reconciled. Official/authenticated preflight and live attempts have not run. No P00 provider call occurred; old campaigns and the private review queue remain unchanged. User/independent/dataset/rubric review and promotion remain PENDING.

## 2026-10-27 — Phase 019 applied-allocation dry-run reconciliation

- Root migration `p00-free-envelope-plus10-v1` was validated and applied after its source/gate commit. The P00 provider-ledger UUID remains `384f921b0e8a4e7db7c5ae0491df3635`; provider and logical history prefixes were preserved. No usage ledger was rewritten, no UUID/receipt was replaced, and the unknown pilot attempt remains separately reserved at 1,475/256 transport and 2,048/256 logical input/output. Root migration evidence reports 16 accounted calls; actual provider billing remains UNKNOWN.
- P00 phase 019 binds dispatch to fresh `free-dev-c2` development only, caps it at twelve cases × three attempts (36), and rejects `free-dev-c1` resume, other IDs, stages and pending policy migration before provider initialization. The exact primary/confirmation split is 136/60 calls. No old-candidate quality results transfer; the 24 old C1 trials remain unexecuted and historical.
- The amended locked full gate passes 144 tests, plus check-fast, lint, format, compile, deterministic dataset contract and Compose config. Focused campaign/preparation tests pass 57. Optional service E2E is INCOMPLETE. The no-provider dry-run now reconciles the applied policy and both read-only ledgers, exposes project/stage capacity and unknown reservations, and fails closed on uncommitted candidate sources. No new provider call or candidate trial has run.
- Remaining P00 primary capacity is exactly 120 calls: 36 C2 development and 84 future holdout. Confirmation remains 60 protected. Across the account, 4,068 calls remain, split into 3,228 original primary commitments and 840 protected confirmations; no correction, judge or canary allocation exists. Dataset/rubric/human/independent review and promotion remain PENDING.

## 2026-10-27 — Root authenticated guard rebound

- Root phase 006 commit `8e03565` now captures authenticated Groq rate-limit headers and applies the most restrictive RPD/TPM/remaining-capacity windows before account reservation. Offline root tests pass: account 24, transport 17, allocation migration 14; P00 locked full gate passes 144. Optional local service E2E remains INCOMPLETE.
- The C2 no-provider dry-run was rerun after the root guard commit. Current P00 source commit is `dec99d750c9ff5482ee46c73aea3a26ba944eadf`; source fingerprint is `e53a13408600aa8d3faf8dfafa59192f5ede1f052866a81b22536e926e637488`. The former `5d32a6c...` dry-run is preserved as stale historical evidence, not used for dispatch.
- Funding remains exactly closed: 120 P00 primary calls after the same sixteen historical attempts; C2 maximum 36 and future holdout 84; 60 confirmation calls protected. Logical unknown reserve 2,048/256 and transport unknown reserve 1,475/256 are reported separately. All review statuses remain PENDING. No credentials or provider requests were used by the dry-run; authenticated preflight remains pending.

## 2026-10-27 — Authenticated catalog preflight, generation blocked

- After root and P00 evidence commits and the final offline dry-run, the metadata-only catalog preflight checked four unique numbered root keys. Model access passed 4/4; `generation_calls=0`. The sanitized report contained no secret values or hashes.
- No allowlisted authenticated rate-limit headers were returned. Billing tier is not exposed by this endpoint and remains UNKNOWN; exact remaining daily tokens remain PENDING. The metadata GETs are not model completions or campaign trials, and their effect on model rate-limit accounting was not exposed.
- Paid authorization is USD 0. Therefore no generation attempt was made. C2 remains blocked until Free-tier billing can be verified; the 36 C2 calls, 84 future holdout calls and 60 protected confirmation calls remain unconsumed. Evidence: `artifacts/evidence/funded-candidate-continuation/authenticated-preflight.json`.

## 2026-10-27 — Phase 020 rotation provenance

Root transport rotation is committed; locked full product gate passes 145 tests after repairing two checkout-dependent provenance tests without weakening dirty-source rejection. Focused 24 tests and fast check pass. Optional service E2E remains INCOMPLETE. Source fingerprint is 56bef263770d396fe69d915bc8aea1bdc9a9109e83584d08e28377adbb01af6b. The user confirms all four distinct accounts are Free; API billing verification and exact daily balances remain unknown. No new model completion in this phase; historical reservations, funding and reviews are preserved.

## 2026-10-27 — Phase 021 live C2 checkpoint

User attested all four distinct accounts Free. Candidate 7099cc5d0f4d576d14f28f7dab4648b074b59740 ran 10 + 3 new attempts: 13/36 grader passes, zero critical/operational failures, then free_token_minute_checkpoint. Total historical plus C2 consumption 29 calls; 107 primary remain (23 C2 + 84 future holdout), confirmation 60 protected. Provider bound 11470/3255; logical bound 12043/3255, same history, never add. Actual billed UNKNOWN. No new unknown attempt, holdout or promotion; review remains PENDING. Evidence and safe resume in artifacts/evidence/funded-candidate-continuation/rotation-live/README.md.

## 2026-10-28 — Phase 022 critical failure stop

- The fake campaign controller now stops after recording a critical result and refuses a subsequent resume when a critical result is present. Focused tests passed 65; the locked full offline gate passed 146 tests after repairing a stale 16-call accounting assumption. Historical gate failures remain in the phase evidence. Optional service E2E and independent verification remain INCOMPLETE. This changes the candidate fingerprint; historical C2 remains immutable and no provider call was made.

## 2026-10-28 - Phase 025 safe campaign guidance

- The offline report no longer labels live C2 commands as safe while continuity and funding are unresolved. The locked fake gate passed 146 tests; no provider calls occurred. See artifacts/evidence/funded-candidate-continuation/safe-guidance-025/.

2026-10-29 phase035: final allocation arithmetic reconciled all six operating envelopes, full fake157/ focused41/private review controls PASS. One current-fingerprint synthetic smoke354/112 PASS, fingerprintf8608311104a4fb4005881b9569a94c1f29731707ac9f70247636bd63685f72d. Operating3/10, holdout84 and confirmation60 protected. Historical semantic failures/human/holdout/promotion remain pending; see phase035 VERIFY.

2026-10-29 phase036: final policy48c3237b/current fingerprint6021179839d958d4fc548a54063f384cd7237ae6b2fafb67c0836131eb49fbc9 smoke354/112PASS, full157PASS. Operating4/10, P00holdout84/confirmation60 protected. P01logical12 remains closed/retained; no quality/human/promotion approval. See phase036 VERIFY and second-diagnostic-allocation-036 evidence.
