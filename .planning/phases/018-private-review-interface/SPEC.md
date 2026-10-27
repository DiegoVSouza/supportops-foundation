# Phase 018 — Private campaign review interface

Status: PLANNED. Reviewer execution and every approval remain PENDING.

## Goal

Prepare a local-only interface for reviewing existing synthetic assistant answers and future campaign answers from the protected P00 review store. Opening, navigating, filtering, and annotating review items must never initialize the provider client or use network access beyond loopback. Historical campaigns remain separated by candidate and immutable.

## Security and data contract

- Bind only to IPv4 loopback. Require a fresh per-process bearer secret entered in the browser; keep authentication material in memory and do not place it in URLs. Use an authenticated, HttpOnly, SameSite cookie and no third-party assets.
- Read assistant content from `.runtime/llm-review/answers.sqlite` using read-only SQLite access. Refuse symlinks/reparse points, unexpected files, unprotected ACLs, wrong owner, and non-UTF-8/corrupt records. Do not read or expose provider credentials.
- Render all case, answer, rubric, annotation, and metadata content as escaped text. Disable script execution, forms from stored content, external resources, and active links through escaping and a restrictive Content-Security-Policy. Treat answer text as untrusted data and display a clear instruction to ignore embedded instructions.
- Send no answer or annotation text to console output, application logs, telemetry, public artifacts, or exports. Persist annotations only in a separate owner-only private append-only store. Record OS author, UTC timestamp, candidate/campaign/case/trial, prompt/schema/dataset/rubric revisions, rubric scores, short redacted error labels, and optional notes. Corrections append a new record referencing the prior annotation; never update or delete history. Preserve disagreements.
- Derive candidate provenance from immutable campaign manifests and trial receipts; never join or pool across campaigns/candidates. Display missing provenance as unavailable and block annotation if the complete provenance tuple cannot be established.
- Show all critical and suspected failures and prepare stratified sampling metadata for unique held-out answer cases. The original protocol requires human review of all critical/suspected failures, a stratified 20% of unique held-out answer cases, and double review of at least 20% of that sample. No holdout is inspected or selected for development guidance in this phase. Reviewer and independent-review status stay PENDING until actual reviews occur.
- Display current pending counts and distinguish historical failed pilot outputs, partial old-candidate development outputs, and any future candidate outputs. Do not mark human, independent, dataset/rubric, or promotion gates as approved.

## Existing items

The pilot (`476fae54e239cfc7c2200831662ef1af2af52e27`) and old development candidate (`b42a198246274db5f7feb17a247ef1fe90e662e6`) are separate read-only review groups. Existing trial results remain immutable and do not transfer as quality evidence to the corrected source. The current corrected-source head after phase 017 is `d3a7f0a` and has no quality trials. The candidate identity for any future evaluation is the final source commit after this interface phase, subject to renewed allocation and freeze; no provider campaign is in progress.

## Exclusions

No provider calls, holdout inspection, expectation/rubric edits, campaign or ledger migration, other project integration, public listener, data export, promotion, or external deployment. The interface may prepare review but cannot perform or attest the deferred human review on the user's behalf.
