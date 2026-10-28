# Plan

1. Add regressions rejecting old C2/C1 live resume and preserving 149/60 primary/confirmation with the exact 209-call policy binding.
2. Update only current allocation/scope/report guidance to the explicit replacement ID; retain human/holdout and safety gates, fixed dataset/prompt/parameters and all historical artifacts. Run locked focused/full fake gates.
3. After root's committed validated migration, reconcile read-only ledgers/fingerprint and freeze a separate candidate scope. Run metadata preflight/generation only if the full audit, eligibility, funding and execution gates demonstrate continuity. Never replay provider errors or unknown work.

allowed_write_paths: `.planning/phases/028-funded-replacement/**`, `scripts/campaign_execution.py`, `scripts/run_live_campaign.py`, `tests/llm/test_campaign_execution.py`, `tests/test_live_campaign_preparation.py`, `artifacts/evidence/funded-replacement-028/**`.
forbidden_changes: historical campaigns/manifests/results, runtime usage ledgers except through the authorized normal future dispatch path, private answers except normal future synthetic review storage, datasets/splits/expectations/rubrics/prompts/schema, paid/per-call/rate/model caps, other project code, holdout, fabricated reviews and provider retries.

Preparation uses fake mode, zero provider calls and USD 0. Future generation is limited to 36 new primary calls under authorization p00-free-envelope-plus13-v1, at most ten per batch with reconciliation after each; no other calls are allocated. Stop on quota/provider/critical/uncertain/provenance failure. max_tries: 3 for local checks only; no live retry. Plan-check self-assessment, independent review pending. Preserve unrelated untracked files; new phase-owned scratch paths only.
