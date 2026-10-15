# Verify — Remediation assurance

For every executed check, save the exact command, exit code, and output in `artifacts/evidence/`.

- [ ] Fake/replay tests and deterministic dataset/golden-set checks pass; cassette provenance is traceable.
- [ ] Local wheel and source provenance agree on version, source commit, and SHA-256.
- [ ] Live budget boundary remains fail-closed under fake transport; no provider call was made.
- [ ] Full fake-mode gate result is recorded with its actual exit code.
- [ ] Docker/service availability is recorded separately; unavailable services are `INCOMPLETE`.
- [ ] Provider quality, cost, and latency remain `PENDING` absent authorized comparable runs.
- [ ] Documentation states the generic adapter's provider-side budget limitation.
- [ ] Any public API change has an ADR, semver change, and consumer update before acceptance; otherwise the `1.0.1` public contract remains compatible.
