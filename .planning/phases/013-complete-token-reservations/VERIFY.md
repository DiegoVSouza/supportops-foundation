# Verify — Complete P00 token reservation dry-run

Save command output and exits under `artifacts/evidence/live-token-reservations/`.

- [x] Confirmation input/output maxima equal 20 fresh cases × 3 trials × current 2,048/256 per-case token ceilings (122,880/15,360).
- [x] `-S` pilot, development, and holdout dry-runs exit 0, remain offline, and leave generation blocked.
- [x] Paid ceiling remains USD 0; quota/reviews remain `PENDING`.
- [x] Focused preparation tests (21) and fast/full fake gates pass; evidence and progress are updated.
- [ ] Staged diff is reviewed and locally committed.
