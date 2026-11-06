#!/bin/bash
cd /c/estudo/Golpe/lab/projects/p00
O=artifacts/evidence/local-proxy
for sd in 7 8 9; do
  python evals/proxy/local_proxy_eval.py --cloudflare --features --prompt $O/variants/f1.md --seed $sd --out $O/cf-f1-s$sd.json > $O/cf-f1-s$sd.summary.json 2>$O/cf-f1-s$sd.err.txt
  python -c "
import json;d=json.load(open('$O/cf-f1-s$sd.summary.json'));print('f1 s$sd',d['passed'],'/',d['cases'],d['by_action'],d['errors'],'neurons',d['estimated_neurons'])" >> $O/run-cf2.log 2>&1
done
echo DONE >> $O/run-cf2.log
