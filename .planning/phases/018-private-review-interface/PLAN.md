# Plan — private campaign review interface

## Tasks

1. Implement a loopback-only, authenticated, standard-library review server that reads the protected answer store and immutable campaign manifests read-only, validates provenance, and renders untrusted text safely without provider/network initialization.
2. Implement private append-only annotations with OS author/time, complete candidate/case/trial/revision linkage, correction references and preserved disagreement. Show critical failures, separate candidates and outstanding human/independent/stratified/double-review coverage without opening holdout.
3. Add offline contract/security regressions for authentication, loopback binding, escaping/CSP, no external resources/provider import, read-only answer access, append-only annotations, provenance separation, ACL/reparse/UTF-8 handling and sanitized logging. Run focused and full locked P00 gates; save outputs and inspect staged diff.

## Ownership

allowed_write_paths:
- `.planning/phases/018-private-review-interface/SPEC.md`
- `.planning/phases/018-private-review-interface/PLAN.md`
- `.planning/phases/018-private-review-interface/VERIFY.md`
- `docs/harness/progress.md`
- `docs/harness/failures.md`
- `docs/knowledge/private-campaign-review.md`
- `scripts/review_ui.py`
- `scripts/check_full.py` (optional isolated pytest basetemp override, retaining the default; quiet Compose validation to keep expanded configuration out of logs)
- `tests/llm/test_review_ui.py`
- `artifacts/evidence/private-review-ui/**`
- `.runtime/llm-review-ui/**` (local private runtime state only; never stage or commit)

forbidden_changes: campaign candidate code outside the listed review interface, prompts, schema, datasets, rubric, graders, thresholds, campaign artifacts, existing answer database, provider receipts/ledgers, `.runtime/llm-review/answers.sqlite*`, credentials, shared policy/registry, services/stacks, sibling projects, lab kit, public artifacts containing answers, and external effects.

llm_mode: offline only; no provider, no network except a local loopback review session, no credential reads.

budget: provider calls 0; paid spend USD 0. Human review is not performed by implementation or automated checks.

## Validation commands

- `uv run --locked pytest tests/llm/test_review_ui.py -q`
- `uv run --locked python scripts/check_fast.py`
- `uv run --locked python scripts/check_full.py`
- Set `P00_PYTEST_BASETEMP=artifacts/evidence/private-review-ui/full-gate-pytest` for the full gate so pytest does not clear the pre-existing `artifacts/tmp/pytest` tree.
- Start the UI only on `127.0.0.1` using a locally generated ephemeral access token; verify auth, navigation, and annotation in a temporary private fixture store, never in historical production review rows during implementation.
- Inspect output/artifacts to confirm no raw answers, annotations, credentials, or access token are present. Preserve command, exit code, and sanitized output under `artifacts/evidence/private-review-ui/`.

## Stop condition

Stop if the protected store ACL/provenance cannot be validated, if an answer or annotation reaches logs/exports, if server bind is not loopback, or if provider/network code is initialized. Do not modify historical answers. Review outcomes remain PENDING until user review; independent, dataset/rubric approval, and promotion remain PENDING. This interface commit changes the project source identity; freeze any later candidate only after the final code commit and renewed valid allocation.
