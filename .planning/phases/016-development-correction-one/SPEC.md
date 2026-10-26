# Phase 016 — First development correction

## Detailed correction requirements

Implement the root luna-corrections SPEC requirements for P00 only. Preserve free-pilot-v1 and its unknown historical HTTP metadata. New free-dev-c1 is exactly 12 development cases × three trials, maximum 36 attempts. No holdout or promotion.

Create agent/schemas/live-decision.json: existing decision/tool contract, all existing fields required, existing global enums, nullable read-only tool, additionalProperties false at both levels. Preserve grader and forbidden-effect checks. Clarify generic concrete-issue lookup versus unclear-issue request_info; no expected labels/facts in prompts. Use one pure payload builder and fingerprint schema. Complete serialized schema/messages/framing must fit 2048 input/256 output; reduce overhead instead of increasing caps.

Propagate typed http_status and allowlisted provider_error_code/OTHER; preserve request_schema/tool_selection without raw errors/headers. Protect confirmation 60 calls/122880 input/15360 output/USD 0.013824 economic estimate. Primary ceiling126/258048/32256/USD 0.0290304 includes existing four attempts. After36 new attempts,86 remain, including84 for holdout. Never reset policy/registry/ledgers.


Preserve the incomplete `free-pilot-v1` baseline and its three semantic failures/one unknown provider failure. Declare correction round 1 before generation, limited to the frozen 12 development cases with three trials each, in a new `free-dev-c1` manifest/candidate. Do not execute or tune using holdout in this phase.

Root-cause hypothesis for observed routing failures: missing retrieved record details were interpreted as requiring clarification rather than selecting the available read-only verification step. Clarify the global workflow policy without case-specific expected values. Add a strict JSON Schema for the existing structured contract using officially supported GPT-OSS structured decoding; this is preventive output control, not proof of the unknown historical provider cause. Preserve the existing grader, dataset, thresholds and 2,048/256 caps.

Keep HTTP status/allowlisted error code and request-schema/tool failures in sanitized trial metadata. Preserve unknown usage. Protect the predeclared fresh-confirmation request/token/economic reserve from consumption by pilot/development/holdout. Candidate metrics remain provisional pending human review, even if development passes.

Acceptance: deterministic payload/no-expectation-leakage, schema/provenance/error/confirmation-budget tests and all regressions; commit candidate before calls; run at most 36 declared development attempts in chunks, checkpoint on limits/errors, and report every failure without semantic retry. Holdout, human approval, quality generalization and promotion remain INCOMPLETE.
