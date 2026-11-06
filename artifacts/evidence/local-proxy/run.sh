#!/bin/bash
cd /c/estudo/Golpe/lab/projects/p00
O=artifacts/evidence/local-proxy
M=llama3.1:8b-instruct-q4_K_M
for p in c6 c7; do
  python evals/proxy/local_proxy_eval.py --model $M --prompt $O/prompt-$p.md --out $O/llama31-8b-$p.json > $O/llama31-8b-$p.summary.json 2>$O/llama31-8b-$p.err.txt
  echo "$p exit=$?" >> $O/run.log
done
echo DONE >> $O/run.log
