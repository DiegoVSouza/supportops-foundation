#!/bin/bash
cd /c/estudo/Golpe/lab/projects/p00
O=artifacts/evidence/local-proxy
for sd in 7 8; do
  python evals/proxy/local_proxy_eval.py --cloudflare --features --prompt $O/variants/f3.md --seed $sd --out $O/cf-f3-s$sd.json > $O/cf-f3-s$sd.summary.json 2>$O/cf-f3-s$sd.err.txt
  python -c "
import json;d=json.load(open('$O/cf-f3-s$sd.summary.json'));print('f3 s$sd',d['passed'],'/',d['cases'],d['by_action'],d['errors'],'neurons',d['estimated_neurons'])" >> $O/run-cf4.log 2>&1
done
echo DONE >> $O/run-cf4.log
