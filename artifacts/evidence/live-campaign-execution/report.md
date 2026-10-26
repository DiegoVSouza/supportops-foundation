# P00 free-only binding and first pilot

Implementation/offline regression: PASS (111 tests plus lint/format/compile/dataset/Compose checks). Candidate committed before provider generation: `476fae54e239cfc7c2200831662ef1af2af52e27`.

Pilot: INCOMPLETE, exit 2. Four provider requests, three evaluated model responses, zero passing responses, one operational failure, two of six planned trials unattempted. Three routing failures and one tool-selection failure are retained under `artifacts/evals/live/free-pilot-v1/`; no failed semantic case was repeated. The holdout was not executed.

Known usage: 844 input / 248 output tokens. Unknown failed usage retains its 1,475 input / 256 output reservation. Whole-account charged totals after this run: four requests, 2,319 input / 504 output tokens, estimated economic value 0.000325125 USD; provider billed cost remains PENDING. Paid authorization is USD 0. The per-project provider usage database is authoritative; this report is a derived snapshot referencing it.

The initial post-run ACL readback found pre-existing explicit access grants despite protected inheritance. Scoped ACL repair and independent readback now verify owner-only directory/database access; a new Windows regression injects and removes such grants. The full gate passed 112 tests after this fix and no additional generation occurred. All runtime SQLite/review files are ignored by Git. Raw synthetic answers exist only in the private review-application DB; trial artifacts contain discrete labels, usage/error metadata and review references.

Follow-up requirements: preserve baseline; add whitelisted HTTP/provider-code diagnostics (the exact original error was not retained); clarify generic answer/lookup versus request-information policy in a declared development correction; keep graders and sealed holdout unchanged. Do not interpret the old baseline's recorded resume command as permission to bypass the unresolved operational cause. After a code/prompt change, use a new frozen candidate rather than overriding this manifest. Human review and promotion remain INCOMPLETE.
