# Shared SupportOps contracts

`supportops_foundation` is the installable source of shared domain, LLM, and testkit contracts. Applications should install a versioned wheel and record its version, source commit, and artifact SHA-256. Do not import source from a neighboring repository.

## LLM modes

`get_llm()` selects `LLM_MODE=fake` by default. Fake responses can be scripted through `LLM_FAKE_RESPONSES` as a JSON array. Replay requires `LLM_CASSETTE_PATH` and consumes exact request records in order. `CassetteRecorder` can record any `LLMClient`; review/redact data before keeping a cassette.

Live requires endpoint, API key, explicit model, a positive `LAB_MAX_USD`, and caller-supplied verified input/output rates. It is never used by tests. Missing configuration fails explicitly rather than silently switching modes.

## Dataset and golden cases

`generate_dataset(seed=42)` returns 40 customers, 200 tickets, 30 KB articles, 80 invoices, and 60 cases. `dataset_sha256()` hashes its canonical JSON. To add a golden case, provide a stable ID, ticket, expected category/priority/action/escalation, and whether it is a boundary. Extend tests for the new behavior and review the digest change with the source diff. Fixture outcomes are synthetic contracts, not measured model quality.
