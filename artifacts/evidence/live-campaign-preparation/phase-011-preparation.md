# P00 Phase 011 — Campaign preparation evidence

## Final offline checks

| Command | Exit | Result |
|---|---:|---|
| `uv run --locked python scripts/run_live_campaign.py --help` | 0 | CLI exposes `pilot`, `development`, `holdout`, config and dry-run options. |
| `uv run --locked pytest -q tests/test_live_campaign_preparation.py` | 0 | 20 passed, including dataset structure, split isolation, calibrated negative grader probes, Python `-S` dry-run and fail-closed generation. |
| `uv run --locked python scripts/check_fast.py` | 0 | `check-fast: OK`. |
| `uv run --locked python scripts/check_full.py` | 0 | Ruff lint/format, compile, 60 tests, deterministic 60-case fixture contract, and Compose config passed. `OPTIONAL_SERVICE_E2E=INCOMPLETE`. |
| `uv run --locked python scripts/run_live_campaign.py --stage pilot --dry-run` | 0 | 6 cases, 6 calls, 1 trial each. Primary campaign ceiling 120 calls; confirmation reserve 60 calls; additive ceiling if pilot/confirmation are separate is 186. |
| `uv run --locked python scripts/run_live_campaign.py --stage development --dry-run` | 0 | 12 cases, 36 trials, 36 stage calls; full primary ceiling 120 calls. |
| `uv run --locked python scripts/run_live_campaign.py --stage holdout --dry-run` | 0 | 28 cases, 84 trials, 84 stage calls; full primary ceiling 120 calls. |

The frozen synthetic dataset has 40 cases, 12 development / 28 holdout, 24 English / 16 Portuguese, and at least three cases in each required family. Dataset SHA-256: `b1e3f779acf7948b2da17aee937f57f6fd643c7b0b0bb78294d09d6bf0326849`. Per-case caps are one provider call, 2,048 input tokens, and 256 output tokens. The planned primary campaign token ceilings are 245,760 input and 30,720 output; the 20-case, three-trial confirmation reserve is 60 calls, 122,880 input tokens, and 15,360 output tokens. These are planning maxima, not approved or consumed quota.

## Preserved preparation failures

- Initial pilot dry-run exited 1 on malformed case JSON; corrected the grader probe fixture.
- Next dry-run exited 1 on incorrect 12/28 split counts; fixed the explicit development membership and rebalanced the data to 24/16 language counts.
- First focused pytest collection failed because the script directory was not importable; added the project root to the test import path. A following split-leakage test failed because it reused a development case; corrected the test to cross a real development/holdout boundary.
- Full-gate attempts caught import-order and formatting violations; fixed them. The final full gate above passed.

## Limits and status

Every dry-run printed `generation_authorized=false`, `provider_accessed=false`, `credentials_read=false`, and `docker_mutated=false`. It displayed USD 0.00 authorized paid spend and unresolved quota, cumulative request/token/spend caps, timing/pacing, durable ledger, dataset/rubric review, approval reference, and confirmation funding as `PENDING`. The manifest and rubric explicitly await independent review. No Groq or Docker request was made. Campaign generation, human review, durable resume/accounting and all model quality/cost/latency gates remain `INCOMPLETE`/`PENDING`.
