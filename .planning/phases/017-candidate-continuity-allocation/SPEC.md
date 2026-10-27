# Phase 017 — Candidate continuity and allocation

Status: **INCOMPLETE — allocation deficit blocks generation**.

## Outcome

Preserve the failed `free-pilot-v1` and partial `free-dev-c1` records, establish the corrected source as a distinct candidate only after confirming the project HEAD, and decide whether the original P00 evaluation can be funded without changing its sample, trial count, holdout, protected confirmation, or any other project's commitments.

The corrected controls are recorded at commit `c9df52641d729da401498fec21b850d75445ef55`. The prior `free-dev-c1` candidate is `b42a198246274db5f7feb17a247ef1fe90e662e6`; its 12 completed trials and 24 pending trials remain attached to that candidate. The historical pilot is immutable and failed. No trial, UUID, receipt, event, reservation, unknown usage, manifest, or ledger may be deleted, rewritten, transferred, or reset.

## Allocation decision

The P00 primary allocation is 126 calls and includes its existing 16 calls (four pilot attempts and twelve development attempts), leaving 110. A fresh development evaluation for the corrected candidate requires 36 calls. The required 84-case holdout requires another 84 calls, totaling 120. The deficit is **10 primary calls**. The 60-call/122,880-input/15,360-output confirmation reserve (economic estimate USD 0.013824) is protected and cannot cover the deficit. The full P00 envelope remains 186 calls; paid authorization remains USD 0.

The root campaign envelope is 4,074 calls and the project allocations sum to that envelope. Moving ten calls from another project would leave that project's unchanged original commitments unfunded. No valid reallocation or policy migration is identified in the current authorization. Therefore this phase may produce offline evidence and a concrete allocation proposal, but must not create a replacement campaign allocation, invoke a provider, consume holdout, or claim a complete candidate evaluation. Proposal for a future explicitly authorized allocation phase: provide at least ten additional primary calls for P00 while separately preserving every other project's original remaining evaluation and confirmation commitments, or identify a verified uncommitted allocation source of at least ten calls. No ceiling is increased in this phase.

## Evidence boundaries

- Historical evidence: pilot and the twelve `free-dev-c1` trials belong only to their recorded candidates and retain their original failure/unknown-use semantics.
- Reusable control evidence: audit regressions, locked offline gates, full transport bounds, ACL/UTF-8/privacy checks, and other deterministic control tests can support control readiness but cannot count as quality trials.
- Candidate quality evidence: only provider attempts with matching candidate, prompt/schema/dataset/rubric provenance count; none transfer between candidates.
- The pilot's unknown call retains the historical logical reservation of 2,048 tokens and the transport reservation of 1,475 tokens as separate layer-specific values. Do not replace either with inferred usage or add the two reservations together. Provider-account usage and project logical-ledger usage describe the same requests at different layers and must not be summed.
- Known charged usage is distinguished from reserved unknown usage, the logical ledger's conservative cap, the provider-account usage ledger, economic estimate, and actual billed amount. Billing remains unknown/PENDING.

## Scope and stop conditions

### Reconciled allocation dimensions, 2026-10-27

Read-only SQLite reconciliation (`artifacts/evidence/candidate-continuity-allocation/accounting.json`) confirms sixteen attempts. Known usage is 5,236 input / 1,650 output tokens; one unknown attempt retains its 2,048/256 logical reservation and 1,475/256 provider-transport reservation. Logical charged totals are 7,284/1,906 and USD 0.001118100 economic estimate; the authoritative campaign guard's provider ledger totals are 6,711/1,906 and USD 0.001075125. These are not additive. Actual billed cost and current provider daily quota remain unknown.

Primary capacity remaining is 110 calls / 250,764 input / 30,350 output / USD 0.027912300 economic estimate. A fresh 36+84 evaluation reserves 120 calls / 245,760 input / 30,720 output / USD 0.0276480. The exact deficient dimensions are **10 calls and 370 output tokens**; input and economic dimensions have no additional deficit at this checkpoint. The 60-call confirmation remains excluded. Account guard remaining calls are 4,058, already assigned across all projects; this is not a provider quota balance. Each other project's six-case pilot, original three-trial main suite and protected confirmation exactly consume its allocation, so no donor is identified without underfunding those commitments.

A concrete, unapproved future policy proposal is to add a uniform ten-call P00 envelope at the original per-call maxima: 10 calls / 20,480 input / 2,560 output / USD 0.002304 economic estimate, with USD 0 paid authorization unchanged. This would raise P00 186→196 and root 4,074→4,084 requests, so it is explicitly outside the current no-cap-increase authorization. It requires the user's budget decision and a separate allocation/migration phase preserving registry UUIDs, policy history, events and unknown reservations. No policy or ledger change is performed here.

No product code, policy, account registry, ledgers, campaigns, review database, services, credentials, provider access, or other project is modified. A local-only dry-run artifact may record the arithmetic, candidate identities, pending review, and stop/resume requirements. Stop if current source identity, project HEAD, receipt reconciliation, or project-wide remaining commitments cannot be confirmed. Human review, independent review, rubric approval, holdout, generalization, and promotion remain PENDING/INCOMPLETE.
