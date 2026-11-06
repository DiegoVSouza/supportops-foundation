#!/bin/bash
cd /c/estudo/Golpe/lab/projects/p00
D=artifacts/evidence/dev-c4-050
for n in 05 06 07 08 09; do
  sleep 70
  LLM_MODE=live uv run --locked python scripts/run_live_campaign.py --resume free-dev-c4 --execute-free --max-trials 10 > $D/batch-$n.json 2> $D/batch-$n.stderr.txt
  echo "batch $n exit=$?" >> $D/resume-loop.log
  python - >> $D/resume-loop.log <<PY
import json
d=json.load(open('$D/batch-$n.json',encoding='utf-8'))
print(d['chunk']['status'],d['chunk']['attempted'],d['chunk']['remaining'],d['recorded_trials'],d['passed_trials'],d['critical_failures'],d['operational_failures'],d.get('provider_stop'))
if d['chunk']['remaining']==0 or d['critical_failures'] or d['operational_failures']: raise SystemExit(0)
PY
  tail -1 $D/resume-loop.log | grep -qE "^(CHUNK_COMPLETE|COMPLETE|[A-Z_]+) [0-9]+ 0 " && break
done
echo DONE >> $D/resume-loop.log
