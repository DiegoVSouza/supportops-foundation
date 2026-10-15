# Verify — Domain contracts and testkit

- [x] All ten originally listed public domain types, plus the exported `Action` enum, reject malformed values; positive cases remain covered by focused tests.
- [x] Equal seeds yield byte-identical canonical dataset output and hash; different seeds vary.
- [x] Dataset cardinalities are exactly 40 customers, 200 tickets, 30 articles, 80 invoices, and 60 golden cases.
- [x] Golden cases include exactly ten named boundary/adversarial records and assert category, priority, action, and escalation; all 50 standard cases assert the same decision fields.
- [x] `uv run --locked python -m pytest -q --basetemp=artifacts/tmp/pytest-p00-contract tests/domain tests/testkit` passed (11 tests); command, exit code, and output are saved in `artifacts/evidence/phase-001-contract-coverage.txt`.
- [x] ADR-001 and package version 1.0.0 existed before the first consumer artifact; subsequent live-budget behavior is recorded by ADR-003 and released as 1.0.1.
