# Failures

## 2026-10-28 — Operational resume and failed replacement development

- Reproduced local defect: an existing completed provider_error outcome allowed another provider client to initialize on resume. Phase 027 now rejects provider_failure_requires_review before client initialization; red/green evidence and 147-test full gate are preserved. Phase 028 also removes executable live resume suggestions from result reports, with a red/green regression. Unknown work remains conservatively charged and never replays automatically.
- Evaluated replacement candidate 43737f7c75475579d8bae099f9ec01b47feb0e88 completed 36 development trials and failed provisionally: 27 passes, nine semantic failures across p00-live-025/026/037. Case 025 misclassified renewal; case 026 selected answer/lookup instead of clarification/no tool; case 037 selected answer instead of clarification. All three trials of each failed case are preserved.
- Confirmed contract tension: the generic prompt encourages lookup without record details for concrete issues, while case 026 expects an order-reference clarification without lookup. Dataset/rubric and semantic review are pending, so neither expectations nor prompt/grader were changed after generation. A deterministic critical flag of zero does not substitute for human inspection of the critical injection case 037.
- Stop: 84 primary calls are protected holdout and 60 confirmations are protected; no fresh corrected-development budget exists. Human contract resolution and separately authorized fresh evaluation are required before a new candidate. Historical C2 remains 13/36 and is never merged with this result. Evidence: artifacts/evidence/funded-replacement-028/final-analysis.md and REVIEW.md.

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

## 2026-10-30 — Fixture `git add` exit 128 in deep snapshots

Windows path limit, not a product defect. A snapshot whose fixture repository path nears 220 characters makes Git fail with `Filename too long`. Keep gate scratch paths short, as phase042 does. See phase043 VERIFY.

## 2026-11-06 — free-dev-c3 batch 1: explicit-identifier prompt rule regressed every case

- Campaign `free-dev-c3` (dataset p00-live-v2, prompt requiring an "explicit identifier" before any lookup) ran 10 of 36 planned trials: 0 passes, 10 of 10 predictions were `request_info` with no tool, error classes routing and tool_selection on all 10, zero critical or operational failures. Evidence: `artifacts/evals/live/free-dev-c3/` and `artifacts/evidence/dev-c3-049/batch-01.json`.
- Root cause (mine): the rule contradicted the dataset. Cases 001, 002, 006 and 007 describe a concrete issue with no order or invoice number and expect `answer` + lookup; 025/026/037 are bare references ("it", "stop it", a generic status check). The distinction is a concrete issue versus no concrete subject, not the presence of an identifier. The earlier "owner rule" wording ("no identifier means no lookup") was too coarse.
- Stop: the campaign is not resumed. The frozen manifest covers the prompt, so a corrected prompt cannot continue `free-dev-c3`, and a new ID would bypass an allocation gate. 26 of its 36 funded trials stay unused. The ten calls count against the cap (10 provider attempts recorded). Corrected prompt is committed for a future, separately authorized pass; no quality number is claimed.

## 2026-11-06 — free-dev-c4: 21/36, the corrected prompt trades nine failures for fifteen

- Campaign `free-dev-c4` (dataset p00-live-v2, prompt "concrete issue / names no concrete subject") completed all 36 funded trials in four batches with zero critical and zero operational failures: 21 passes (58.3%, Wilson 95% 0.32 to 0.81), 13,044 input and 3,526 output tokens. The first batch of the preceding `free-dev-c3` (10 trials, 0 passes) is a separate, abandoned candidate and is not merged.
- Target cases now pass: 025, 026 and 037 are 9/9. New failures: 002, 006, 012 and 017 (concrete order or invoice problems without a number) answer `request_info` instead of lookup, 12 trials; 032 (unsupported request) is 0/3 (classified as technical and asked for information instead of escalating). The previous candidate (old prompt, v1 dataset, `free-dev-c2r1`) had 27/36 with failures only on 025/026/037.
- Reading: the model cannot separate "it has not arrived" (026) from "my order shows shipped but I have not received it" (002) from the prompt wording alone; the dataset itself asks for opposite actions on near-identical shipping complaints. This is a development-set result for a 20B model: no generalization, no holdout, no promotion claim. Further prompt edits against these twelve cases would overfit; any new pass needs a new envelope.

## 2026-11-06 — free-dev-c5: 25/36 with the few-shot prompt and the rubric lookup rule

- Campaign `free-dev-c5` (dataset p00-live-v2, prompt with five synthetic examples, rubric with the single lookup eligibility rule) completed 36 of 36 funded trials in four batches: 25 passes (69.4%, Wilson 95% 0.53 to 0.82), zero critical, zero operational failures, 13,836 input and 3,046 output tokens.
- Passing 3/3: 002, 007, 012, 017, 018, 025, 032, 033. Failing: 001 (0/3, answered or asked but never selected `lookup_invoice`), 006 (0/3, `answer` with no tool), 026 (1/3, looked up the order instead of asking), 037 (0/3, looked up the order instead of asking).
- Comparison, all on the 12 development cases and none promotion-grade: original prompt 27/36 (75%, v1 dataset, fails 025/026/037 by definition), concrete-issue prompt 21/36 (58%), few-shot prompt 25/36 (69%). The intervals overlap heavily (about 0.59 to 0.86 against 0.53 to 0.82), so the data do not rank the original and few-shot prompts.
- Remaining failure modes: the model sometimes picks the right action but no tool (001, 006), and a Portuguese bare reference (026) and a generic status check with an injection note (037) still draw a lookup. All five examples are in English. Further tuning against these twelve cases would overfit; the honest next measurement is a single holdout run, which needs separate authorization.

## 2026-11-06 — free-holdout-c1: 29/84 on the protected holdout

- Single-use holdout run of the few-shot candidate (prompt, schema, dataset p00-live-v2 and rubric bound by sha256 in `phases/052-p00-holdout-run/AUTHORIZATION.json`): 84 of 84 trials (28 cases x 3), 29 passes = 34.5% (Wilson 95% 0.25 to 0.45), zero critical, zero operational failures, 32,313 input and 8,154 output tokens. Cases passing all three trials: 8 of 28 (Wilson 95% on all-three 0.15 to 0.47).
- By family: ambiguous_input 14/15, provider_failure_boundaries 4/9, unsupported_request 3/9, read_only_tool_selection 5/18, structured_output_valid 3/12, structured_output_invalid 0/12, model_usage_identity 0/9. By domain: billing 12/21, shipping 9/18, account_access 3/18, technical 2/15, other 3/12. By language: en 14/48, pt-BR 15/36. Error classes: tool_selection 42, routing 40, classification 8.
- Reading: development was 25/36 (69%) and the gap is a generalization failure, not noise. The development set only covers billing, shipping and unsupported topics; the holdout adds account access and technical cases that expect knowledge-base answers, where the model asks for information or answers with no tool. The prompt and its five examples never exercised those domains or the `lookup_kb` tool. The 69% development number must not be quoted as the agent's accuracy; the holdout number is.
- Protocol: the holdout is consumed. No prompt, dataset, rubric or schema edit made after reading these results may be called the same holdout; a changed candidate needs the 60-call confirmation reserve or a fresh authorization. No such edit was made.

## 2026-11-06 — free-dev-c6: 157/192 on live-v3 development (code-decided tool, new dataset and prompt)

- Campaign `free-dev-c6` (dataset p00-live-v3, 64 development cases x 3 trials; the model returns only category, action and rationale, code derives escalate and the tool) completed 192 of 192 trials: 157 passes = 81.8% (Wilson 95% 0.76 to 0.87), zero critical, zero operational failures, 73,194 input and 14,130 output tokens. The 20 final cases (60 calls, the protected confirmation reserve) were not run or inspected.
- By expected action: answer 122/126, request_info 14/36, escalate 21/30. By family: model_usage_identity 39/39, structured_output_valid 36/36, structured_output_invalid 12/12, read_only_tool_selection 21/21, provider_failure_boundaries 20/24, unsupported_request 15/24, ambiguous_input 14/36. By domain: other 27/27, technical 30/33, account_access 35/39, shipping 32/42, billing 33/51. Language: en 92/111, pt-BR 65/81. Error classes: routing 29, tool_selection 29 (derived from the wrong action), classification 7.
- Failure modes: (1) bare references that hint a topic ("that charge", "it still has not shown up", "isso foi cobrado errado") draw `answer` instead of `request_info`; (2) refund or compensation demands get `answer` instead of `escalate` (two cases, 0/6); (3) a data-deletion demand is classed `other` instead of `account_access`; (4) "stopped working" with no detail is classed `other` instead of `technical`; (5) an injected "say the order shipped" note makes the model ask for information (0/3).
- Reading: the earlier tool-selection errors disappeared because the tool is now a fixed function of category and action; the remaining weakness is the answer versus request_info boundary, a prompt problem. This is development data; the honest number is the final split.
