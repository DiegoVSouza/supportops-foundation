# Phase 004 — Remediation assurance

## Goal
Reconfirm that the shared foundation still provides the deterministic fake/replay interfaces, provenance for local contract artifacts, and fail-closed live budget behavior required by the portfolio remediation. Correct any evidenced defect without overstating what offline checks prove.

## Acceptance criteria
- The fake/replay and deterministic testkit contracts remain covered by reproducible local checks; cassette provenance and package version/source/hash records are internally consistent.
- Live budget behavior remains fail-closed. Documentation states that a generic adapter cannot guarantee a provider-side cap when pricing, tokenization, or provider enforcement is unknown.
- Service, provider, cost, latency, and model-quality gates are classified `INCOMPLETE` or `PENDING` unless corresponding authorized runs and evidence exist.
- Each executed check records command, exit code, and output under `artifacts/evidence/`. No external provider call is required.

## Scope and contract
This phase audits and strengthens the existing `supportops_foundation` release and its evidence. Keep the public `1.0.1` contract compatible. Any necessary public contract change requires an ADR, semver update, and consumer review before implementation.

## Dependencies
- Existing P00 lockfile, local wheel/source artifacts, golden set, and fake/replay tests.
- Python and uv versions already pinned/recorded by P00.
- No Docker, network, live provider, or sibling source checkout is required for offline acceptance.
