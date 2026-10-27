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

Actual reviewer instructions and counts are supplied only after implementation evidence is verified. No reviewer approval is implied.
