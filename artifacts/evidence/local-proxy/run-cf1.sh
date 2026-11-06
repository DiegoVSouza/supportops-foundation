#!/bin/bash
cd /c/estudo/Golpe/lab/projects/p00
O=artifacts/evidence/local-proxy
run() { # name prompt seed
  python evals/proxy/local_proxy_eval.py --cloudflare --prompt $2 --seed $3 --out $O/cf-$1.json > $O/cf-$1.summary.json 2>$O/cf-$1.err.txt
  python -c "
import json;d=json.load(open('$O/cf-$1.summary.json'));print('$1',d['passed'],'/',d['cases'],d['by_action'],'neurons',d['estimated_neurons'])" >> $O/run-cf1.log 2>&1
}
run c6-s8 $O/prompt-c6.md 8
run c6-s9 $O/prompt-c6.md 9
run v1-s7 $O/variants/v1.md 7
run v2-s7 $O/variants/v2.md 7
run v3-s7 $O/variants/v3.md 7
echo DONE >> $O/run-cf1.log
