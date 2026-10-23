# SPEC — Run a budgeted Groq live smoke check

## Goal

Verify the configured Groq model through P00's live adapter and provide bounded recovery from transient request timeouts.

## Acceptance criteria

- `openai/gpt-oss-20b` is checked against Groq's model list before a completion is sent.
- A live smoke run sends one short synthetic prompt, records model, status, latency, reported usage, cost estimate, and exit code, and never records credentials.
- If Groq rejects all configured credentials or the configured model is absent from the account model list, the smoke may use OpenRouter's verified free-model router; it must not route to a paid model.
- A Groq transport can rotate among explicitly configured keys after transient network failures/timeouts, with bounded attempts and backoff.
- HTTP 429 responses are not retried or used to rotate credentials; provider rate limits remain authoritative.
- Preflight budget accounts for retry attempts that could have reached the provider; uncertain failed attempts remain reserved.
- Existing fake/replay behavior and the P00 offline gate remain intact.

## Scope

This phase covers the P00 live adapter and one Groq smoke call, with a zero-price OpenRouter free-model fallback. It does not claim model quality for P01–P05, alter sibling projects, or bypass provider quotas.

## Budget

Use a local cap of USD 0.05 for the run. Current Groq published GPT-OSS 20B rates are USD 0.075/M input and USD 0.30/M output. The smoke prompt limits output to 128 tokens; retries are bounded to three attempts. The account is expected to be on Groq Free, but the local cap still applies.
