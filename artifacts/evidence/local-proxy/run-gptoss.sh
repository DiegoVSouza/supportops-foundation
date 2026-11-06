#!/bin/bash
cd /c/estudo/Golpe/lab/projects/p00
O=artifacts/evidence/local-proxy
for p in c6 c7; do
  python evals/proxy/local_proxy_eval.py --model gpt-oss:20b --cpu --timeout 600 --prompt $O/prompt-$p.md --out $O/gptoss20b-$p.json > $O/gptoss20b-$p.summary.json 2>$O/gptoss20b-$p.err.txt
  echo "$p exit=$?" >> $O/run-gptoss.log
done
echo DONE >> $O/run-gptoss.log
