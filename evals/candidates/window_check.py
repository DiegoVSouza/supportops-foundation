"""Show how much of the shared free daily token window (rolling 24 h) is used and when the
remaining funded Groq trials would fit. Read-only; makes no provider call.

  python evals/candidates/window_check.py [--calls 192] [--tokens-per-call 600]
"""

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
LAB = PROJECT.parents[1]
sys.path.insert(0, str(LAB / "scripts/harness"))

from live_free_account import SharedAccount  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--calls", type=int, default=192)
parser.add_argument("--tokens-per-call", type=int, default=600)
args = parser.parse_args()

policy = json.loads((LAB / "shared/policies/groq-free-campaign.json").read_text(encoding="utf-8"))
account = SharedAccount(LAB, policy)
now = time.time()
rows = sorted(
    (r for r in account._history() if r["reserved_at"] >= now - 86400),
    key=lambda r: r["reserved_at"],
)


def used(r):
    usage = account.usage(r)
    return usage["input_tokens"] + usage["output_tokens"]


total = sum(used(r) for r in rows)
limit = 200000
need = args.calls * args.tokens_per_call + 2304
print(f"window: {total:,} of {limit:,} tokens used in the last 24 h ({len(rows)} attempts)")
print(
    f"to run {args.calls} calls (~{args.calls * args.tokens_per_call:,} tokens) the window must hold at most {limit - need:,}"
)
remaining = total
if remaining <= limit - need:
    print("fits now")
else:
    for row in rows:
        remaining -= used(row)
        if remaining <= limit - need:
            print(
                "fits after",
                time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(row["reserved_at"] + 86400)),
            )
            break
    else:
        print("does not fit within the current window")
