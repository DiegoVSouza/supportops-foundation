# Verify â€” bounded P00 campaign runner

- [x] CLI `--help`, stage validation, offline dry-run and ledger resume inspection contracts pass. Actual execution resume remains pending.
- [x] Current incomplete approval/quota/cumulative cap configuration blocks before credentials or dispatch; zero paid spend is a separate field from free quota.
- [x] Python `-S` dry-run succeeds with the standard library and no provider/SDK import, credential read, network, or Docker access.
- [x] SQLite attempt reservations are durable, append-only and conservative when usage is unknown. Concurrency and multi-campaign tests prove cumulative P00 request caps cannot race or reset under a new campaign ID.
- [ ] Process-crash injection around actual provider dispatch/response and atomic ledger writes is not yet implemented; the dispatcher does not exist.
- [x] Resume inspection distinguishes reserved/uncertain attempts; reserve rejects any previously reserved/completed case trial. Automated stage continuation is pending.
- [x] OS lease blocks a separate process and releases safely on normal exit.
- [ ] All-project launcher integration and stale-process recovery remain pending.
- [ ] Groq numbered-key catalog preflight and bounded dispatch are not implemented; no provider call occurred.
- [x] Fake/replay defaults and no-silent-fallback contracts remain unchanged.
- [x] Fast and full P00 gates pass; command, exit and sanitized output saved. No provider request occurred.
- [ ] Staged paths reviewed; implementation commit recorded.
- [ ] Clean-context verification completed.
