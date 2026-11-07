#!/bin/bash
cd /c/estudo/Golpe/lab/projects/p00
D=artifacts/evidence/final-053
uv run --locked python scripts/check_full.py > $D/check-full.txt 2>&1
echo "full=$?" >> $D/prep2.log
echo DONE >> $D/prep2.log
