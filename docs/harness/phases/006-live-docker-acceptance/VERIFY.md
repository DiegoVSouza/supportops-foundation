# Verification

Result: PASS for the scoped acceptance.

The foundation live smoke passed with 147 input and 94 output tokens. All 40 offline tests passed. This is client acceptance; the optional HTTP demo service E2E remains outside this run.

Evidence: artifacts/evidence/live-docker/ contains executed commands, exit codes, retained failed attempts and sanitized results. Timestamped phase Groq reports are additional real-run evidence. Historical reports are preserved.

Every live run authenticated the requested model catalog before generation. Model: openai/gpt-oss-20b; official Groq SDK: 1.7.0; Docker Engine: 29.1.3. Only numbered root credentials were read silently. No silent fake fallback, paid provider fallback, kit edits, push, refunds or outbound customer messages occurred. Estimated costs derive only from observed usage; billed cost remains PENDING. This small synthetic sample does not establish general model quality.

Fake remains the default. Service integration checks use dedicated Compose projects. All 28 pre-existing container names are still present; this is not a health claim about unrelated stacks. Newly started live stacks are left available.
