# Official sources checked 2026-10-28

- https://console.groq.com/docs/model/openai/gpt-oss-20b: fixed model remains documented, including function tool use, JSON schema and reasoning. No alternate model/provider is selected.
- https://console.groq.com/docs/rate-limits: current Free table lists 30 RPM / 1,000 RPD / 8,000 TPM / 200,000 TPD for this model. Limits apply at organization level and exact account limits may differ; some organizations also have separate input/output minute limits. Distinct credentials do not multiply the lab envelope. Authenticated smaller limits/cooldowns take precedence. Published values do not prove usable daily remainder or billing.
- https://docs.python.org/3.13/library/urllib.request.html: socket timeout describes blocking operations, not an exact whole-request deadline. Actual custom transport behavior is established by source and injected tests, not SDK retry documentation.
- https://docs.python.org/3.13/library/subprocess.html: run(timeout=...) kills/waits for the child on expiry; process creation and cleanup are outside a strict timing SLA. Root public metadata CLI uses an 80-second worker bound; actual P00 parent bounds startup/response separately.

No model call, credential or authenticated provider access was used to check these public sources. Actual catalog access and ledger/window approval remain required immediately before any provisional generation. User Free attestation is explicit for slots 0–4; API billing/organization verification and human reviews remain pending.
