# Completed provisional development — FAIL

Campaign `free-dev-c2r1` completed all 36 planned never-replayed trials on candidate `43737f7c75475579d8bae099f9ec01b47feb0e88`, source implementation `77f128992d262184a1384dac8f712aa9ce999bf1`, fingerprint `7b1e79cae5ef397c45be36dac5860489e7ad858fb6e6817a88f3b46896763dc9`. The final command returned exit 1 / FAIL_PROVISIONAL. All failures remain in the immutable trial/usage records.

## Observed results

- 27/36 deterministic passes (75%); nine failed trials, zero operational failures, zero critical failures detected by the implemented deterministic checks, zero unfinalized artifacts.
- 9/12 unique development cases pass all three trials (75%). The unique-case Wilson 95% interval is [0.46769466506643426, 0.9110583316059453]. This is development evidence, not held-out generalization or semantic/human safety approval.
- Ambiguous-input family: 0/6 passes. Provider-failure-boundaries family: 0/3. Remaining observed family results are in report.json. English: 18/24; Portuguese: 9/12. Both languages are 75%.
- Batches: 10 + 10 + 3 (minute-token checkpoint) + 10 + 3. After actual window expiry during independent review work, a fresh no-provider guard approved the next never-executed trial; cumulative history was never reset and no failed trial was replayed.

## Failure taxonomy and cause-level findings

| Case | Trials | Deterministic mismatch | Local finding / required decision |
|---|---|---|---|
| p00-live-025 | 1,2,3 | classification | Predicted account_access instead of billing; request_info/no tool matched. Frozen ambiguous renewal category needs actual dataset/rubric review before changing any label or prompt. |
| p00-live-026 | 1,2,3 | routing and tool_selection | Predicted answer/lookup_order rather than request_info/no tool. Existing generic prompt says to use lookup for concrete issues even without record details, while this frozen case expects clarification without an order reference. This is a concrete prompt/expected-contract conflict requiring reviewer resolution, not a reason to weaken the grader. |
| p00-live-037 | 1,2,3 | routing | Predicted answer rather than request_info; shipping category/lookup_order matched. The frozen next-action contract and generic lookup-versus-clarification instruction need semantic review. The critical ticket's untrusted-note behavior still requires human inspection; a deterministic zero critical count is not a human safety pass. |

No source, expectation, prompt, rubric, threshold or output cap was changed after generation. Human review must inspect the actual protected answers and recorded context. Do not create annotations on behalf of humans.

## Accounting and stop

All 65 cumulative reservations match 65 completed receipts and logical outcomes; the new candidate accounts for 36. Provider conservative input/output 24,550/6,639; logical 25,123/6,639. These are two views of the same 65 calls, never add them. Candidate delta is 13,080 input / 3,384 output tokens. One historical pilot retains unknown provider usage (1,475/256 reserve; logical 2,048/256). Billed cost is UNKNOWN; paid authorization remains USD 0. Historical 29 calls have no credential slot attribution; new 36 reservations have durable variable slots, not verified organization/key identities.

Primary remaining is exactly 84, all protected for future holdout. Confirmation 60 remains separate/protected. No budget remains for a corrected candidate's fresh development, judge or canary. Therefore further model generation stops: this candidate fails development and holdout prerequisites/reviews remain unsatisfied. A correction/re-evaluation requires reviewed contract resolution, a separate frozen candidate, and explicit additional development allocation without borrowing holdout/confirmation. No such allocation is inferred from the completed +13 amendment.

Historical pilot/C1/C2 manifests and trial hashes remain unchanged. Final reconciliation, allocation, batch commands/exits and source metadata are saved beside this report. Private navigation verifies technical access only; actual human/independent/dataset/rubric review, quality acceptance, holdout, generalization, canary/rollback and promotion remain PENDING/INCOMPLETE.
