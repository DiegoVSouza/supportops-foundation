# Plan

1. Build a fresh snapshot with committed root/project sources and SQLite backups; verify no prior phase040 marker exists.
2. Persist a phase040 consumed marker, run exactly one complete locked fake gate, and save sanitized output.
3. On PASS, freeze the source binding and record it; on FAIL, preserve evidence and stop without a focused substitute or live action.

allowed_write_paths: `.planning/phases/040-current-allocation-gate/**`, `artifacts/evidence/additional-validation-040/**`, `docs/harness/progress.md`.

forbidden_changes: policy, ledgers, reservations, historical results, holdout84, confirmation60, provider/live calls, paid use, fallback, external effects, Terraform, human claims. Fake only; one gate maximum. Stop on snapshot/marker/gate uncertainty.
