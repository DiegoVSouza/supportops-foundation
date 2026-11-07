#!/bin/bash
cd /c/estudo/Golpe/lab/projects/p00
D=artifacts/evidence/final-053
uv run --locked python scripts/check_full.py > $D/check-full.txt 2>&1
echo "full=$?" >> $D/prep.log
uv run --locked python -S ../../scripts/harness/live_free_account.py --catalog-preflight > $D/catalog-preflight.json 2>$D/catalog-preflight.stderr.txt
echo "preflight=$?" >> $D/prep.log
echo DONE >> $D/prep.log
