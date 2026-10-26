# Phase 014 — Bounded campaign chunks

Implement P00's deterministic single-attempt chunk controller over the existing durable ledger and OS lease. Each P00 trial reserves one provider request; retries are zero. The provider/grade boundary is injected and returns sanitized outcomes/usage. This phase exercises only synthetic offline callbacks and does not enable the campaign CLI.

Acceptance: at most ten new trials per chunk; immutable successes and semantic failures are skipped on resume; outstanding reservations halt for reconciliation; reservation/checkpoint precede execution; unresolved/invalid caps or account guard rejection prevent dispatch; provider/adapter interruption preserves uncertain usage; deadlines, pacing and cumulative caps stop subsequent attempts; observed usage above reservation is retained and stops the chunk. No exception text or response content is written.

The controller requires an account guard and shared lease path supplied by a future reviewed launcher. Cross-project guard integration, real provider timeout/catalog/approval checks, actual batches, human review and promotion remain INCOMPLETE. No quota or budget changes.
