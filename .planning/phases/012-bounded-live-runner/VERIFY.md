# Verify — bounded P00 campaign runner

- [ ] CLI `--help`, stage validation, dry-run and resume manifest contracts pass.
- [ ] Every missing approval/quota/cumulative cap blocks before credentials or dispatch; zero paid spend with a finite approved free cap is represented distinctly.
- [ ] Python `-S` dry-run succeeds and proves SDK, credential, network and Docker isolation.
- [ ] Atomic append-only reservation ledger covers requests/tokens/estimated cost and records unknown usage conservatively.
- [ ] Fault injection at pre-dispatch, dispatch uncertainty, response and ledger writes proves no silent retry or accounting reset.
- [ ] Resume skips completed and uncertain trials; failed semantic outcomes stay immutable.
- [ ] Shared machine lease contends across independent launchers; owner-safe release and crash recovery are tested.
- [ ] Groq preflight/dispatch uses only numbered keys and never exposes credentials; wrong provider/model and auth errors fail closed.
- [ ] Fake/replay are still offline defaults; live errors never fall back silently.
- [ ] Fast and full P00 gates pass; command, exit and sanitized output saved. No provider request occurred.
- [ ] Staged paths reviewed; implementation commit recorded.
- [ ] Clean-context verification completed.
