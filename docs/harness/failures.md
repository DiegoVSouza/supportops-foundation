# Failures

Record recurring builder or product failures here before fixing them.

## 2026-10-26 — Campaign reservation race and uncertain retries

The initial ledger prototype checked cumulative totals before SQLite had taken a write lock, allowing two concurrent launchers to both observe remaining capacity. It now acquires `BEGIN IMMEDIATE` before reading totals and reserving; a two-launcher test proves one reservation is rejected at the cap. A reservation is durable before dispatch, survives process restart as uncertain, and cannot be reused. Missing usage keeps the full reservation. Actual provider dispatch/crash reconciliation is not yet implemented, so the campaign stays disabled. Evidence: `artifacts/evidence/live-campaign-runner/`.
# 2026-10-26 — Free pilot baseline: routing and provider diagnostics

- Candidate: `476fae54e239cfc7c2200831662ef1af2af52e27`; campaign: `free-pilot-v1`.
- Three real development/pilot responses selected `request_info` instead of the existing `answer` reference; one also returned no read-only tool. Root-cause hypothesis: the global prompt does not clearly distinguish missing retrieved records from an unclear issue; it encourages asking for information before selecting an available lookup. Clarify the generic next-action policy in a declared development correction round, retain baseline failures and do not change expected outcomes.
- The fourth request returned a transport reason `request_schema`; the owning artifact reduced it to `configuration`, and exact HTTP status/provider error code were not persisted. The actual provider cause cannot be established from existing evidence. Add restricted categorical HTTP/error-code diagnostics before more generation; never persist raw error bodies or repeat a semantic failure to obtain approval.
- Outcome: INCOMPLETE (four requests, three model failures, one operational failure, two cases pending). Known usage: 844 / 248 tokens; unknown failed usage remains reserved. Human review/promotion remain pending. Evidence: `artifacts/evals/live/free-pilot-v1/report.json`.

## Private review ACL correction

Post-run readback found four access entries, including pre-existing explicit grants, despite inheritance being disabled. The previous `icacls /grant:r` plus `/inheritance:r` did not remove those explicit entries. Protected inheritance alone is insufficient evidence of owner-only storage. Repaired only the private review directory/known SQLite files using owner assignment, ACL reset, explicit owner grant and inheritance removal; readback verifies one current-user access entry and current-user ownership. A Windows regression injects extra directory/file grants and proves they are rejected until removed. No further generation occurred during repair; data in this application state is authorized synthetic output.

## 2026-10-26 — Free development campaign quota checkpoint

`free-dev-c1` stopped after 12 completed trials when the shared account guard returned `free_token_minute_checkpoint`. All 12 model trials passed; no semantic failure or operational provider error occurred. The guard stopped further reservations, so no uncertain attempt needs replay. The current campaign remains INCOMPLETE with 24 trials pending. Resume only with the recorded `--resume free-dev-c1 --execute-free --max-trials 10` command after the guard approves capacity. The latest sanitized token-minute reset value is historical feedback, not a guarantee of current quota. Do not infer daily remaining tokens or billing tier from headers. Evidence: `artifacts/evidence/development-correction-one/checkpoint-accounting.json` and `resume-dry-run.json`.

## Phase 016 audit corrections supersede the previous resume instruction

Offline review found four gaps: arbitrary campaign IDs/stages could create another development allocation; dirty or untracked schemas were omitted from the candidate Git check; the primary ceiling subtracted the pilot even though the ledger already included it; and local payload checks omitted transport normalization/framing. The corrected runner permits only the allocated live development ID, checks all fingerprinted sources in their owning repositories, applies the full 126-call ceiling to cumulative history, and matches the transport bound before any provider initialization. New regressions cover these paths; the locked full gate passed 131 tests.

These source corrections invalidate the frozen `free-dev-c1` fingerprint. The old safe-resume command above is historical and must now fail with provenance mismatch. Preserve its 12 completed trials and 24 pending trials; no manifest migration, new ID, reset, implicit retry, new correction allocation or provider call was performed. A separately declared allocation/candidate phase is required before further generation. Offline evidence: `artifacts/evidence/development-correction-one/audit-fix/`.

## 2026-10-27 — Replacement candidate allocation deficit

The corrected source cannot resume or inherit twelve quality trials from `free-dev-c1`. A complete fresh development/holdout requires 120 primary calls, against 110 remaining; full output reservations also exceed remaining primary capacity by 370 tokens. The 60-call confirmation reserve is protected. Other projects' original pilots, three-trial evaluations and confirmation exactly occupy their allocations. No valid donor is identified, and no cap, registry UUID or ledger is reset. Phase 017 records the exact reconciliation and an explicitly unapproved future ten-call uniform-envelope proposal. Generation remains INCOMPLETE pending a budget decision; no provider call occurred.

## 2026-10-27 — Phase 019 ceiling regression after explicit allocation

The first P00 full-gate run after applying the user-approved policy file failed one assertion that still expected the old 126-call primary and derived a 60-call confirmation by subtracting 126 from the P00 project total. The test exposed the intended phase-019 change: P00 primary must be 136 while confirmation remains 60. Updated the controller to 136 and rewrote the regression to model 4 historical pilot + 132 primary reservations and assert the unchanged confirmation dimensions directly. The corrected focused suite passed 34 tests and the locked full gate passed 142. No provider or credential path ran; the root registry remains old until phase 005 apply.

## 2026-10-27 — Review provenance and temporary gate files

An initial UI prototype filtered out the historical pilot because its manifest predates the separate strict-schema file. Read-only inspection confirmed all three pilot responses remain in the protected database. The interface now marks schema provenance as NOT_APPLICABLE_LEGACY_NO_SCHEMA only for that exact historical candidate and requires complete hashes for newer candidates. Missing/mismatched dataset or receipt provenance fails closed. The pilot's operational error remains a record without a response; missing HTTP status/code are not reconstructed.

The full gate's fixed pytest basetemp would clear an existing `artifacts/tmp/pytest` tree. A scoped optional `P00_PYTEST_BASETEMP` override now permits a phase-owned evidence subtree, preserving pre-existing outputs. The standard default is retained. Final focused and full locked checks passed; development failures and the actual successful command outputs are described in `artifacts/evidence/private-review-ui/commands.md`.

## 2026-10-27 — C2 dry-run fingerprint invalidated by root guard revision

Root phase 006 changed the authenticated rate-limit guard files that P00 fingerprints. The previously saved C2 fingerprint `5d32a6c04b22cbcc5c161885dfa67b928d223a5caae0cd297e292548248b2719` therefore became stale before any C2 manifest or provider call existed. Preserved that output as `pre-phase006-stale-dry-run.json`, reran the dry-run only after root guard commit `8e03565`, and recorded fingerprint `e53a13408600aa8d3faf8dfafa59192f5ede1f052866a81b22536e926e637488`. This is provenance correction, not candidate quality evidence. No historical result, ledger event, UUID or unknown reservation changed.

## 2026-10-27 — Free billing tier unavailable from authenticated preflight

Authenticated catalog access passed for four unique numbered credentials, but the endpoint returned no allowlisted rate-limit headers and does not attest billing tier or remaining daily tokens. Because paid authorization is USD 0, a model completion could not be proven free. No campaign manifest, reservation, completion, or holdout was created. Keep generation blocked until account billing tier is verified from an authoritative account source; never infer it from catalog access or missing headers. Evidence: `artifacts/evidence/funded-candidate-continuation/authenticated-preflight.json`.
# 2026-10-27 — Phase 019 dry-run cap mismatch

The first P00 allocation dry-run still displayed the historical config ceiling (186 calls / 380,928 input / 47,616 output) after the authorized root policy was migrated to 196 / 401,408 / 50,176. It made no provider call and did not change any ledger. The dry-run now reads the applied shared policy and both append-only ledgers under the same campaign/account leases as dispatch, removes only WAL sidecars created by its read-only inspection, and rejects dirty/uncommitted candidate sources. The stale output is retained as `artifacts/evidence/funded-candidate-continuation/pre-reconciliation-cli-dry-run.json`; it is not allocation evidence. Latest full locked gate: 144 passed.
