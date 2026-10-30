# Plan

1. Prepare a fresh short-path snapshot with committed source, read-only SQLite backups and an owned scratch directory. Record exact candidate and dependencies.
2. Persist a create-only attempt marker and run one complete locked fake full gate. Capture stdout, stderr, command, cwd and exit.
3. Record the outcome and freeze the binding only if PASS. Stop on failure or uncertainty; no focused substitute, provider or replay.

allowed_write_paths: `.planning/phases/041-short-snapshot-gate/**`, `artifacts/evidence/short-snapshot-gate-041/**`, `docs/harness/progress.md`; owned scratch under `C:/estudo/Golpe/lab/.runtime/p00-gate-041/**`.

forbidden_changes: policy, ledgers, reservations, prior reports, source, provider calls, paid use, holdout84, confirmation60, Docker, Terraform apply or human evaluation. One fake gate maximum. Stop if scratch exists, marker exists, source is dirty, backup is invalid or gate fails. Plan-check is implementer self-assessment.
