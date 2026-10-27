# Phase 017 plan check

Command: manual requirements review against `harness/GSD-LITE-PLUS.md`, P00 `AGENTS.md`, and phase 017 SPEC/PLAN/VERIFY.

Exit code: 0 (plan accepted with execution blocked on allocation).

Output:

- Three ordered tasks: within the required 2–4 range.
- Allowed write paths are concrete and limited to phase 017 and its evidence directory.
- Forbidden changes, offline mode, zero-call budget, validation commands, and stop condition are explicit.
- Arithmetic closes: 126 primary − 16 consumed = 110; 36 new development + 84 holdout = 120; deficit = 10. Confirmation remains 60 calls and is excluded.
- Candidate separation is explicit. The old 24 pending trials cannot be resumed under the corrected source or transferred to a new candidate.
- No migration source preserves all existing project commitments under the 4,074-call root cap; no allocation is made.
- No independent review, human review, dataset/rubric approval, or promotion is claimed.
- Dry-run records provider access and credential reads as false; no provider execution was performed.

Result: plan-check PASS for plan completeness; execution/allocation INCOMPLETE. No implementation or provider generation is authorized by this phase.
