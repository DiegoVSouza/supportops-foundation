#!/bin/bash
# Waits for the fake gate and the preflight, then for the free daily window, then runs the
# whole free-dev-c8 pass (batch 1 starts the campaign, resume-loop.sh runs the rest).
cd /c/estudo/Golpe/lab/projects/p00
D=artifacts/evidence/dev-c8-056
until grep -q "^DONE" $D/prep3.log 2>/dev/null; do sleep 10; done
if ! grep -q "^full=0" $D/prep3.log || ! grep -q "^preflight=0" $D/prep3.log; then
  echo "ABORT: gate or preflight failed" >> $D/run-c8.log; echo DONE >> $D/run-c8.log; exit 1
fi
TARGET=$(date -u -d "2026-11-07 14:52:00" +%s)
while [ $(date -u +%s) -lt $TARGET ]; do sleep 20; done
LLM_MODE=live uv run --locked python scripts/run_live_campaign.py --stage development --campaign-id free-dev-c8 --execute-free --max-trials 10 > $D/batch-01.json 2> $D/batch-01.stderr.txt
echo "batch 01 exit=$?" >> $D/run-c8.log
bash $D/resume-loop.sh
echo "loop finished" >> $D/run-c8.log
echo DONE >> $D/run-c8.log
