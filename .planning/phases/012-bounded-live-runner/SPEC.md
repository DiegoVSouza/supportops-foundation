# Phase 012 — Bounded live campaign runner

## Goal

Extend the P00 preparation-only CLI into a resumable, auditable campaign runner while retaining its public library client contract and fake/replay defaults. P00 is a library/CLI product; no HTTP service is required. Implement the runner in P00 only. No provider request is in scope for this phase. The current reviewed dataset, account quota evidence, human review, and all cumulative limits remain pending, so generation must continue to fail closed.

## Required behavior

- Preserve six-case pilot and 12/28 development/holdout split, three independent trials, approved model, one generation call maximum per logical trial, and frozen dataset/rubric identity.
- Keep a successful dry-run offline and SDK-independent. Report every unresolved prerequisite without loading credentials or touching the network.
- Add a durable append-only campaign ledger and recovery rules. Reserve worst-case request, input/output tokens, and estimated cost before dispatch; record the reservation before the provider can be called. On a crash/timeout after possible dispatch, mark the attempt uncertain, retain its reservation, and never retry it automatically. Resume only new eligible trials.
- Serialize all lab campaigns with the same configured machine-local exclusive lease path; fail before dispatch on contention. Do not derive per-project paths that permit concurrent campaigns. Lease metadata must be secret-free.
- Enforce separate zero-paid-spend and finite authorized-free-request ceilings, along with cumulative request/token/estimated-cost caps. Missing quota, funding, review, pacing, deadline, or identity remains a blocker. Key rotation never creates extra quota.
- Use only the numbered Groq credentials loaded silently from the lab root `.env`; authenticated catalog preflight must confirm the configured model. Do not record secret values or fingerprints.
- Persist case/trial provenance, sanitized error class/status, observed usage when available, reservations, rubric outcomes and trace identifiers. Do not persist raw prompts, completions, provider headers, or model reasoning. Preserve completed failures. Never retry semantic failures or switch to fake/replay after a live failure.
- Accept bounded stage execution and resume by campaign ID. Generation is allowed only after every approval and cumulative cap is explicit and reconciled. This phase does not authorize spend or provider calls; retain `generation_enabled=false` for current config.

## Acceptance

1. Offline dry-run works under Python `-S`, reports exact stage reservations/blockers, and proves no credentials, SDK, network, or Docker access.
2. Ledger writes are atomic and append-only; crash-point tests prove reservation-before-dispatch and uncertain-attempt handling. Resume never repeats completed/uncertain attempts or resets caps.
3. Cross-project lease contention and stale-lease recovery are deterministic and secret-free.
4. Deliberate quota/token/cost/call cap and missing-review probes block before dispatch. Zero paid budget can coexist with an explicitly approved finite free-tier quota; unknown free quota remains blocked.
5. Existing public fake/replay/live client contracts and no-fallback behavior pass the P00 full gate. No real trial, metric or provider result is claimed.

## Out of scope

Dataset/rubric approval, human review, setting any pending budget or free-tier values, model catalog preflight, provider calls, campaign pilot, public service/deployment, cross-project code, changes to the shared lab spec, and live promotion.
