# Audit remediation results

Engineering regression gate: PASS. Live campaign and readiness: INCOMPLETE.

| Command, from the P00 repository | Exit | Saved evidence |
| --- | ---: | --- |
| `uv run --locked pytest tests/llm/test_campaign_execution.py -q --basetemp artifacts/evidence/development-correction-one/tmp/audit-fix-focused` | 0 | `focused.txt`: 31 passed before the final explicit-revision regression was added |
| `uv run --locked python scripts/check_full.py` | 0 | `check-full.txt`: final 131 tests passed, lint/format/compile/dataset/Compose passed; includes the extra revision regression |
| Offline current-source/manifest/payload/receipt inspection through locked Python | 0 | `verification.json`: 12 cases, 36 maximum trials, full input bound 1911–2010, primary ceiling 126, protected confirmation 60, historical receipt attempts still 16 |

The stage/campaign gate rejects renamed development IDs, pilot and holdout before filesystem/provider effects. Repeated synthetic chunks complete at most the same 36 unique trial keys. Git regressions use isolated fixture repositories to reject unstaged/staged schema changes, an untracked schema/script and a dirty root-owned source. The explicit revision argument cannot bypass production source checks. Schema changes reject resume before another callback. A 126-reservation synthetic ledger includes its initial four reservations exactly once and rejects reservation 127, leaving all original confirmation dimensions protected.

Complete payload bounds include the exact canonical stream field and framing used by transport protocol v1. A boundary input previously accepted at 1871 serialized bytes now fails locally before provider initialization. An offline subprocess invokes the real transport encoder for all 12 development payloads and confirms exact bound equality; it never creates a provider session or loads credentials.

No provider call, key read/hash, policy/registry/ledger reset, budget expansion, dataset/rubric/grader change, holdout run or service mutation was performed. Historical free-pilot-v1 and free-dev-c1 artifacts remain immutable. The old free-dev-c1 source fingerprint now differs; resume is blocked, not migrated. New generation requires a separately declared allocation/candidate phase that preserves existing attempts. Human review remains pending.
