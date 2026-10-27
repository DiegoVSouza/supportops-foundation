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

No product code, policy, account registry, ledgers, campaigns, review database, services, credentials, provider access, or other project is modified. A local-only dry-run artifact may record the arithmetic, candidate identities, pending review, and stop/resume requirements. Stop if current source identity, project HEAD, receipt reconciliation, or project-wide remaining commitments cannot be confirmed. Human review, independent review, rubric approval, holdout, generalization, and promotion remain PENDING/INCOMPLETE.
