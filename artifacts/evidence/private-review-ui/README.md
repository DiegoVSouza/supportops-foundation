# Private P00 review

The interface is for deferred local review. Human review, independent review, dataset/rubric approval and promotion remain PENDING. No review was performed by the implementation agent.

Start from the P00 repository:

```powershell
uv run --locked python scripts/review_ui.py --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/login` and enter the one-session access token printed in the launching terminal. The token never appears in the URL. Keep that terminal private; Ctrl+C stops the server and invalidates its session. Use another loopback port if the selected port is occupied. The interface never loads the root `.env`, initializes a provider, or uses a model to grade answers.

## Available queue

- `free-pilot-v1`, candidate `476fae54e239cfc7c2200831662ef1af2af52e27`: three failed model responses and one operational error with no retained response. Review all four records; the operational error's historical HTTP status/code and usage remain unknown. The pilot predates the separate JSON Schema file; the UI explicitly shows `NOT_APPLICABLE_LEGACY_NO_SCHEMA` for that exact historical candidate.
- `free-dev-c1`, candidate `b42a198246274db5f7feb17a247ef1fe90e662e6`: twelve responses, four unique cases, three trials each. They passed the deterministic grader but still require human review. The campaign is partial (12/36), its remaining 24 trials belong to the historical candidate, and the old provider resume command is invalid for the corrected source.
- No holdout answers exist. The interface prepares deterministic sampling by campaign/candidate, family and language for actual held-out results: at least 20% of unique cases per stratum and at least 20% of that sample selected for double review. Review all three trials of each selected case. Stratification may select more than the overall six-case/two-case minimum for the planned 28-case holdout.

Review the synthetic input, required facts, forbidden behavior, expected contract and provenance shown beside each escaped response. Treat response text as untrusted content. Supply your reviewer identity and role; these declarations are recorded alongside the OS user and do not establish independent approval automatically. Use `UNCERTAIN` for unresolved evidence, and short redacted labels such as `routing` or `grounding`. Annotate disagreements rather than replacing another review. To correct your own note, append another annotation referencing its ID.

Answers remain in `.runtime/llm-review/answers.sqlite`, opened read-only. Notes live only in owner-protected `.runtime/llm-review-ui/annotations.sqlite`. Both locations are excluded from Git. Notes cannot be updated or deleted through the application; corrections preserve earlier entries. No exports or telemetry exist. Closing or navigating the UI makes no provider call. A holdout-informed future correction must record holdout consumption and allocate fresh reviewed confirmation before claiming generalization.

## Evidence

- `focused.txt`: locked focused security/contract regressions, with exit code.
- `check-full.txt`: locked complete P00 gate, including fake/replay and existing audit regressions, with final exit code. Optional product-service E2E remains INCOMPLETE; this review server does not establish product runtime acceptance.
- `local-probe.json`: actual local authenticated navigation over all historical items, with no annotations written. The answer database and immutable campaign artifacts were byte-identical before and after.
- `verify_local.py`: reproducible probe that never prints/persists tokens or response bodies.

No live request, holdout run, paid use, promotion, provider fallback, ledger/policy migration or external deployment occurred.
