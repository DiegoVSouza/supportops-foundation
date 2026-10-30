# Plan

1. Rebuild the fixture under the phase040 layout and vary path length and the `.git` path component, capturing stderr.
2. Record the cause in VERIFY.md and `docs/harness/failures.md`.

allowed_write_paths: `.planning/phases/043-git-128-diagnostic/**`, `artifacts/evidence/git-128-diagnostic-043/**`, `docs/harness/failures.md`, `docs/harness/progress.md`.

forbidden_changes: product code, tests, ledgers, provider calls, consuming a gate.

llm_mode: fake. budget: USD 0. validation: `python artifacts/evidence/git-128-diagnostic-043/reproduce.py`. stop conditions: cause not reproduced after three attempts.
