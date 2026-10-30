# Plan

1. Prepare a fresh snapshot with committed sources and SQLite backups, and verify the pytest scratch path is within the exact allowed roots defined by `scripts/check_full.py` before consuming the gate.
2. Persist a create-only attempt marker and run one complete locked fake gate, capturing command, cwd, exit and output.
3. Record the result and candidate binding; stop on failure or uncertainty. Never repeat this gate or invoke live.

allowed_write_paths: `.planning/phases/042-verified-scratch-gate/**`, `artifacts/evidence/verified-scratch-gate-042/**`, `docs/harness/progress.md`; owned isolated scratch `.runtime/.git/p00-gate-042/**`.

forbidden_changes: policy, ledgers, reservations, prior reports, source, provider calls, paid use, fallback, Docker, Terraform apply, holdout84, confirmation60 or human evaluation. Fake only, one gate maximum. Stop on unsafe scratch, dirty source, invalid snapshot, existing marker or gate failure. Plan-check is implementer self-assessment.
