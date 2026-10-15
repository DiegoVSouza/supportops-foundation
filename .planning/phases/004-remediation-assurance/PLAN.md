# Plan — Remediation assurance

## Execution controls
- `llm_mode`: `fake`; replay only with the checked-in traceable cassette fixture.
- `allowed_write_paths`: `.planning/phases/004-remediation-assurance/**`, `artifacts/evidence/**`, `tests/**`, `supportops_foundation/**`, `docs/**`, `README.md`, `README.pt-BR.md`, `pyproject.toml`, `uv.lock`.
- `forbidden_changes`: lab root including `roadmap-ai-engineer.md`, harness kit, sibling projects, unrelated phase artifacts, public API changes without ADR/version/consumer update, network/live provider calls, package publication, push, deploy, or secrets.
- Dependencies: P00's installed Python/uv environment and existing local artifacts; no external services.

## Tasks
1. **Audit deterministic contracts and evidence** — inspect fake/replay tests, golden-set coverage, cassette provenance, and local wheel/source hashes; add focused tests only for evidenced missing guarantees. Save audit commands and outputs under `artifacts/evidence/`.
2. **Verify live-budget limits and wording** — exercise the fake transport/budget boundary tests and review fail-closed behavior and generic-adapter limitations; correct documentation or implementation only where a concrete gap is found. Do not make a live request.
3. **Reconcile gate status and close evidence** — run the applicable fake-mode full check, classify service/provider/quality/cost/latency gates from actual evidence, and update P00-owned status/docs if needed. Save command, exit code, and output; leave unrun gates `INCOMPLETE` or `PENDING`.

## Checks
- `uv run --locked python scripts/check_fast.py`
- `uv run --locked python scripts/check_full.py` with `LLM_MODE=fake`
- `uv run --locked python scripts/doctor.py` (diagnostic only; unavailable services remain incomplete)
- Verify recorded package version, source commit, and SHA-256 against local artifacts; no package is published.

## Stop condition
Stop before changing a public contract if compatibility requires an ADR, new version, or consumer approval. If a required service/provider gate cannot run, save its reason and classify it `INCOMPLETE`/`PENDING`; do not convert absence of execution into a pass.

## Plan review
Coordinator review against GSD-LITE-PLUS and the P00 remediation criteria: three observable tasks, bounded paths, explicit dependencies and checks, no live calls, and evidence-based stop/status rules. Approved for execution.
