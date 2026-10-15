# Verify — Domain contracts and testkit

- [ ] All ten public domain types validate expected and malformed inputs.
- [ ] Equal seeds yield byte-identical canonical dataset output and hash; different seeds vary.
- [ ] Dataset cardinalities are exactly 40 customers, 200 tickets, 30 articles, 80 invoices, and 60 golden cases.
- [ ] Golden cases include at least 10 boundary/adversarial records and assert all decision fields.
- [ ] `uv run pytest -q tests/domain tests/testkit` passes; command, exit code, and output are saved under `artifacts/evidence/`.
- [ ] ADR-001 and package version 1.0.0 exist before consumers use the package.
