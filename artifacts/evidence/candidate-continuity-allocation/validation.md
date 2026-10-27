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
