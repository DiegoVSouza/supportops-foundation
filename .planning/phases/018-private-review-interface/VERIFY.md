# Verify — private campaign review interface

All implementation checks start PENDING. The design/plan check is not security or reviewer approval.

- [ ] Server binds only to loopback and requires a per-process secret outside URLs; unauthorized callers cannot see item data or append annotations.
- [ ] Reading, filtering, and navigation make no provider call and perform no external network access.
- [ ] Answer store opens read-only; historical answer rows and receipts remain unchanged.
- [ ] Reparse points/links, ACL owner/inheritance/grants, unexpected files, invalid UTF-8, and database errors fail closed.
- [ ] All stored content is escaped; scripts, links, active HTML, and embedded instructions are inert; CSP disallows scripts and external assets.
- [ ] Logs, telemetry, public evidence, and exports contain no answer, annotation, credential, or access token.
- [ ] Annotation store is owner-only and append-only; every entry binds candidate/campaign/case/trial/prompt/schema/dataset/rubric and records author/time; correction and disagreement preserve prior entries.
- [ ] Pilot, old development candidate, and corrected source remain distinct; missing candidate/revision provenance blocks annotation.
- [ ] UI shows all critical/suspected failures and exposes pending unique-heldout stratified 20% and double-review 20% requirements without examining holdout in this phase.
- [ ] Focused and complete locked P00 checks pass and sanitized commands/exits/output are saved.
- [ ] User review, independent review, dataset/rubric approval, holdout, generalization, and promotion remain PENDING/INCOMPLETE.

## Executed verification, 2026-10-27

Internal technical verification: PASS. Independent clean-context verification: PENDING.

- Locked focused gate: nine tests passed; `artifacts/evidence/private-review-ui/focused.txt`, exit 0.
- Locked complete P00 gate: 140 tests passed, including existing accounting, provenance, unknown usage, fake/replay, ACL, UTF-8 and interruption regressions; lint, formatting, compile, deterministic dataset and Compose quiet configuration checks passed. `artifacts/evidence/private-review-ui/check-full.txt`, final exit 0. Optional product-service E2E remains INCOMPLETE.
- Actual loopback navigation: unauthenticated and invalid-token requests returned 401; authenticated index and every one of the sixteen historical records returned 200. CSP forbids scripts. Fifteen private responses are available (three pilot, twelve development); one operational record has no response. No annotation was written and before/after snapshots confirmed the answer database and campaign files unchanged. `local-probe.json`, probe exit 0.
- Pilot schema absence is explicitly recorded only for its exact historical candidate. Current candidates must have complete revision hashes. Dataset hash and answer/trial receipt identity are verified before display.
- Sampling is deterministic by candidate, family/language and unique case; at least 20% per stratum and at least 20% of that sample selected for double review. It does not inspect unavailable holdout answers. Annotation authorship stores OS user and self-declared reviewer/role; declarations do not imply independent approval.
- Windows fixture ACL checks ran in the focused/full suites; existing full-suite reparse/privacy checks remain passing. Annotations use a separate owner-only directory, append-only database triggers, correction references and escaped history. Navigation and tests make no provider call or root `.env` read.
- CLI launch and reviewer instructions: `artifacts/evidence/private-review-ui/README.md`.

The unchecked original list is the verifier's contract; this executed evidence is the implementing agent's technical assessment, not an independent sign-off. Human/independent review, dataset/rubric approval, holdout, generalization and promotion remain PENDING/INCOMPLETE.
