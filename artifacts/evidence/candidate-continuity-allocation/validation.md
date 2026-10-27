# Phase 017 validation evidence

## Plan check

Manual review command: compare phase 017 SPEC/PLAN/VERIFY with `harness/GSD-LITE-PLUS.md`, P00 `AGENTS.md`, and phase 016 audit requirements.

Exit code: 0. Output: three ordered tasks; concrete write ownership; forbidden changes; offline zero-call budget; validation and stop conditions; exact 10-call deficit; no unapproved reallocation; separate historical/control/candidate evidence; pending reviews preserved. Full checklist is in `plan-check.md`.

## Offline dry-run arithmetic

Command (from `projects/p00`, locked environment):

```powershell
uv run --locked python -c "import json,pathlib; p=json.loads(pathlib.Path('artifacts/evidence/candidate-continuity-allocation/dry-run.json').read_text(encoding='utf-8')); assert p['capacity']['p00_primary_envelope_calls']-p['capacity']['existing_consumed_calls']==p['capacity']['remaining_primary_calls']; assert p['capacity']['remaining_primary_calls']+p['capacity']['deficit_calls']==p['fresh_candidate_plan']['maximum_required_primary_calls']; assert sum(p['fresh_candidate_plan']['chunks'])==p['fresh_candidate_plan']['maximum_required_primary_calls']; assert max(p['fresh_candidate_plan']['chunks'])<=10; assert p['capacity']['protected_confirmation']['available_to_primary'] is False; assert p['provider_accessed'] is False and p['credentials_read'] is False; print('offline allocation dry-run validation PASS; deficit=10 calls; confirmation protected; provider=none; credentials=none')"
```

Exit code: 0. Output: `offline allocation dry-run validation PASS; deficit=10 calls; confirmation protected; provider=none; credentials=none`.

An initial draft of the dry-run chunk list failed the arithmetic assertion (exit 1). The chunk list was corrected before the recorded passing validation; no project source, campaign record, credential, or provider was touched by either validation.

## Read-only provenance checks

- `Get-Content projects/p00/.git/HEAD; Get-Content projects/p00/.git/refs/heads/main`: exit 0; branch `main`, ref `c9df52641d729da401498fec21b850d75445ef55`.
- `git status --short` in P00: exit 0; output `?? artifacts/tmp-pytest/`. Preserved without reading, staging, or deleting it.
- Campaign reports/manifests and audit evidence were read only. No service, Docker stack, credential, provider, registry, SQLite ledger, receipt, or campaign artifact was mutated.

Phase result: **plan-check PASS; allocation and live execution INCOMPLETE**. No CLI resume command is safe or valid for provider execution.

## SQLite/account reconciliation, 2026-10-27

Command: `uv run --locked python artifacts/evidence/candidate-continuity-allocation/reconcile.py`.

Exit code: 0. Complete sanitized output: `accounting.json`. Both ledgers were opened with SQLite `mode=ro`; the registry/policy were read only. The registry UUID matches P00's provider ledger. Known input/output is 5,236/1,650; charged provider total is 6,711/1,906 with a 1,475/256 unknown reservation. Charged logical total is 7,284/1,906 with a 2,048/256 unknown reservation. There are sixteen unique attempts at both layers. The exact deficient dimensions for a fresh candidate plus holdout are ten calls and 370 output tokens. All other projects' original commitments and confirmation exactly occupy their allocations. No donor or migration is applied.

Correction to the earlier manual-plan-check record: a manual implementing-agent review has no subprocess exit code. Its PASS is a plan completeness assessment, not an executed machine command or independent review. The actual arithmetic and SQLite commands above exited 0. Independent verification remains PENDING.

## Committed-source resume rejection

Command: `uv run --locked python artifacts/evidence/candidate-continuity-allocation/verify_provenance.py`.

Exit code: 0. Output: `provenance.json`. On committed implementation `3d1384995790585c6c0ad37bd12b3017ed225dc0`, the real campaign runner rejects historical `free-dev-c1` with `immutable_campaign_provenance_mismatch` before the deny-only offline provider factory is initialized (initializations: zero). It checks committed sources through the normal path. Snapshots confirm no change to either historical campaign, logical/provider ledger, account registry or protected answer database. All saved hashes are public source/configuration identities; no credential is read or hashed. No replacement campaign or allocation is created.
