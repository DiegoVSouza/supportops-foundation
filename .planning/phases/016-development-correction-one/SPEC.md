# Phase 016 — First development correction

Preserve the incomplete `free-pilot-v1` baseline and its three semantic failures/one unknown provider failure. Declare correction round 1 before generation, limited to the frozen 12 development cases with three trials each, in a new `free-dev-c1` manifest/candidate. Do not execute or tune using holdout in this phase.

Root-cause hypothesis for observed routing failures: missing retrieved record details were interpreted as requiring clarification rather than selecting the available read-only verification step. Clarify the global workflow policy without case-specific expected values. Add a strict JSON Schema for the existing structured contract using officially supported GPT-OSS structured decoding; this is preventive output control, not proof of the unknown historical provider cause. Preserve the existing grader, dataset, thresholds and 2,048/256 caps.

Keep HTTP status/allowlisted error code and request-schema/tool failures in sanitized trial metadata. Preserve unknown usage. Protect the predeclared fresh-confirmation request/token/economic reserve from consumption by pilot/development/holdout. Candidate metrics remain provisional pending human review, even if development passes.

Acceptance: deterministic payload/no-expectation-leakage, schema/provenance/error/confirmation-budget tests and all regressions; commit candidate before calls; run at most 36 declared development attempts in chunks, checkpoint on limits/errors, and report every failure without semantic retry. Holdout, human approval, quality generalization and promotion remain INCOMPLETE.
