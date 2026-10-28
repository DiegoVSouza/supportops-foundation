# P00 continuity, accounting and review audit

## Current evidence

Root transport correction: 4dc8131. Initial locked full fake gate passed 146 tests; receipt reconciliation command exited 0. Read-only reconciliation matched all 29 trial records to completed provider receipts and logical outcomes: pilot 4, C1 12, C2 13. C2 candidate remains 7099cc5d0f4d576d14f28f7dab4648b074b59740. Manifest/trial hashes are in reconciliation.json. Zero historical reservations contain credential_slot; organization/key attribution is UNKNOWN. No inference from round-robin selection is valid.

Provider conservative usage: 11,470 input / 3,255 output; logical usage: 12,043 / 3,255. These are two views of the same 29 calls. The historical unknown pilot keeps provider 1,475/256 and logical 2,048/256 reservations. The dry-run confirms 107 P00 primary calls remaining and 60 confirmations protected. No new call, reservation or review was made.

## Crash and resume boundaries

The account lease serializes approval/slot selection/FULL commit; POST follows commit. Crash before commit sends nothing; crash after commit and before send remains conservatively reserved. Crash after send or response and before provider completion also leaves an unresolved reserve, blocking all subsequent account dispatch. Provider completion and private-answer/trial/logical completion are separate commits: missing trial/receipt/logical agreement fails closed, and a remaining logical reservation prevents replay. Checkpoint export failure after logical completion preserves the immutable outcome. Existing process-death, lease-contention, no-replay, checkpoint, capacity and provenance regressions pass in the full fake gate.

Root cumulative limits span projects/campaign IDs/restarts, and rolling minute/day windows include conservative unknown usage and smaller authenticated feedback. Credential selection is durable for new reservations only. No per-account capacity multiplication is implemented or authorized. ProviderClient bounds startup at 80 seconds and response waits normally at 17 seconds before kill; socket timeouts alone are not a total deadline guarantee. No exactly-once provider billing is claimed.

Confirmed defect: an existing provider_error outcome did not stop client initialization on resume. The red regression reached the forbidden client constructor. The correction rejects provider_failure_requires_review before initialization. This conservative stop has no automatic approval/reset path. It preserves error receipts and does not replay a completion. Focused correction passed 35 tests; full post-correction result is recorded separately.

## Review authorization and actual CLI

The development dry-run reports authorization.dataset_review and authorization.rubric_review as blockers to reviewed acceptance. AUTHORIZATION.md explicitly permits provisional synthetic development with those reviews pending. The real --execute-free path requires explicit live mode, fixed config, bounded chunk, enabled generation, fixed allocated stage/ID, committed source, applied policy/UUID, immutable fingerprint, receipts, critical/operational stop and account approval. It does not consult dry-run review blockers. This is the provisional-development exception, not dataset/rubric approval. --resume without --execute-free is inspection only; exit 0 with --dry-run authorizes no generation. Holdout is rejected by validate_live_scope; reviews and original holdout sealing requirements remain mandatory. Actual CLI flags are saved in help.txt.

Current sources cannot resume historical C2: fingerprinted root and P00 changes invalidate frozen provenance. Do not run the historical README command. Dry-run safe start/resume suggestions remain null. Human/independent/dataset/rubric/generalization/promotion remain PENDING.

## Private review

The nine private UI regressions in the full gate cover escaped untrusted content, read-only answer access, provenance, append-only corrections and score validation, loopback authentication, public-bind denial and stratified/double-review selection. Code verifies owner ACLs, binds annotations to candidate/prompt/schema/dataset/rubric and UTC creation time, and records OS author plus self-declared reviewer/role. Corrections reference an existing annotation for the same trial. Critical/suspected records are displayed; heldout sampling is deterministic by candidate/family/language and selects at least 20%, with 20% double review. UI navigation imports no provider. Reviewer independence remains self-declared: actual independent identities and coverage require humans. No annotation or human score was created during this audit. Historical 29-record navigation remains historical evidence, not a new review.

## Unapplied replacement proposal

Historical continuation has 23 C2 trials remaining plus 84 holdout = 107 calls. A replacement candidate needs 36 + 84 = 120, so an additional 13 primary calls are required, with confirmations untouched. At existing caps this is 26,624 input / 3,328 output and USD 0.0029952 economic estimate (USD 0 paid authorization). Proposed P00 allocation would be 196 -> 209 calls, primary 136 -> 149, total input 401,408 -> 428,032, output 50,176 -> 53,504, estimated value 0.0451584 -> 0.0481536; global calls 4,084 -> 4,097. This proposal is NOT applied and is NOT authorized by “continue”. No migration, new campaign ID or provider preflight may substitute for explicit authorization, source freeze and full eligibility checks. Slot 0 Free eligibility also remains unverified; numbered-key Free attestation remains recorded.
