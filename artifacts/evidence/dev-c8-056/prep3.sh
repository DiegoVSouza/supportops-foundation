#!/bin/bash
cd /c/estudo/Golpe/lab/projects/p00
D=artifacts/evidence/dev-c8-056
uv run --locked python scripts/check_full.py > $D/check-full-day2.txt 2>&1
echo "full=$?" >> $D/prep3.log
uv run --locked python -S ../../scripts/harness/live_free_account.py --catalog-preflight > $D/catalog-preflight-day2.json 2>$D/catalog-preflight-day2.stderr.txt
echo "preflight=$?" >> $D/prep3.log
echo DONE >> $D/prep3.log
