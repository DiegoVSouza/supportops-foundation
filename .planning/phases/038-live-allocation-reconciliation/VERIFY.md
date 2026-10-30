# Verification plan

- Independently inspect the policy, migration state, provider ledger references/history, and logical P01/P04 reservation event rows.
- Tests must establish that allocation follows durable reservations across changed policy totals, keeps provider consumption separate from logical reservations, and fails closed on ambiguous/missing ledger data. Expected values must be calculated from fixtures representing the contract, not copied from the report under test.
- Record each command, cwd, exit code, and sanitized output in `artifacts/evidence/live-allocation-reconciliation-038/`.
- Run the one authorized complete fake gate only after source and focused contract checks are ready, on a fresh isolated snapshot. If it fails, preserve evidence and stop further gates.
