# ADR-003: Reconcile observed live usage against the budget ledger

- Status: Accepted for `supportops-foundation==1.0.1`.
- Date: 2026-10-15.
- Context: the generic live adapter reserves a tokenizer-free estimate before transport. A compatible provider can report more input tokens than the local UTF-8 estimate because request framing and tokenization vary.
- Decision: keep each in-flight reservation separate from committed observed spend. After a successful response with both prompt and completion token counts, atomically replace its reservation with cost computed from caller-supplied verified rates. If usage is absent, keep the preflight estimate reserved. If observed accumulated spend exceeds `LAB_MAX_USD`, report a live error and reject all subsequent requests at preflight.
- Limit: reconciliation happens after a provider response, so it cannot undo or prevent an individual provider charge that unexpectedly exceeds the cap. A provider-specific hard spending limit or verified tokenizer/quote is required to guarantee a strict provider-side per-request maximum. No live provider is contacted by tests.
- Compatibility: method signatures and response schema are unchanged; this patch corrects budget accounting and makes observed over-cap usage fail explicitly. Bump the package patch version and require consumers to record the new artifact provenance.
- Alternatives considered: discard the estimate after each response (rejected because it loses concurrent in-flight reservations); silently report estimated cost as actual (rejected because it hides provider-reported spend).
