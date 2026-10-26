# Verify — Live campaign preparation

The verifier must use the repository artifacts and commands, not implementation-chat claims. Save command, exit code, and sanitized output under `artifacts/evidence/live-campaign-preparation/`.

- [ ] Dataset has exactly 40 unique semantic cases with 12 development and 28 sealed holdout; coverage and language counts match the reviewed manifest.
- [ ] Scenario/source grouping prevents close variants from crossing splits; expected outcomes and rubrics have review provenance.
- [ ] Rubrics reject deliberately wrong decisions, tool choices, unsupported facts and malformed output; grader defects are not concealed by changing cases.
- [ ] Config lists every required finite ceiling and approval source. Unapproved campaign limits remain visibly `PENDING`; paid spend remains zero.
- [ ] Dry-run reports counts and blockers and performs no SDK construction, credential reads, network access, or Docker mutation.
- [ ] Generation exits incomplete before dispatch if authorization, quota, model preflight or any required cap is unresolved; no silent model/provider fallback exists.
- [ ] Resume/chunk reservation model does not reset cumulative caps; this preparation phase does not claim durable real-trial accounting is implemented unless separately evidenced.
- [ ] P00 fake-mode fast and full checks pass, with no unexpected skips; command, exit code and output are saved.
- [ ] No provider request occurred; no quality, cost, or latency result is inferred from fixtures or dry-run output.
- [ ] Staged diff is limited to allowed paths and contains no credentials, generated secrets, or unrelated user data.
