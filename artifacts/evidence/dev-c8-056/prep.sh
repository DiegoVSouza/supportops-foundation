#!/bin/bash
cd /c/estudo/Golpe/lab/projects/p00
D=artifacts/evidence/dev-c8-056
python -S scripts/run_live_campaign.py --stage development --dry-run > $D/dry-run.json 2>&1
uv run --locked python scripts/check_full.py > $D/check-full.txt 2>&1
echo "full=$?" >> $D/prep.log
uv run --locked python -S ../../scripts/harness/live_free_account.py --catalog-preflight > $D/catalog-preflight.json 2>$D/catalog-preflight.stderr.txt
echo "preflight=$?" >> $D/prep.log
echo DONE >> $D/prep.log
