"""Write a reproducible JSON summary of a recorded live campaign.

The portfolio copies its P00 numbers from these files, so nothing is typed by hand. A summary is
computed only from `artifacts/evals/live/<campaign>/trials.jsonl` and the dataset, plus, when
asked, the exact replay of the deterministic director over the same trials.

  python evals/candidates/summarize_campaign.py free-final-c1 free-holdout-c1 free-dev-c6 --director free-dev-c6
"""

import argparse
import collections
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))

from scripts import director

OUT = PROJECT / "artifacts/evidence/summaries"
DATASETS = {
    "p00-live-v1": PROJECT / "evals/datasets/live-v1/cases.jsonl",
    "p00-live-v2": PROJECT / "evals/datasets/live-v2/cases.jsonl",
    "p00-live-v3": PROJECT / "evals/datasets/live-v3/cases.jsonl",
}


def wilson(k, n):
    z = 1.96
    p = k / n
    center = (p + z * z / 2 / n) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / 4 / n / n) / (1 + z * z / n)
    return [round(center - half, 3), round(center + half, 3)]


def load(campaign):
    base = PROJECT / "artifacts/evals/live" / campaign
    rows = [
        json.loads(line)
        for line in (base / "trials.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    return rows, manifest


def cases_for(rows):
    version = None
    for name, path in DATASETS.items():
        ids = {
            json.loads(line)["case_id"]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        if {r["case_id"] for r in rows} <= ids:
            version = name
    cases = {
        c["case_id"]: c
        for c in map(json.loads, DATASETS[version].read_text(encoding="utf-8").splitlines())
        if True
    }
    return version, cases


def tally(rows, key):
    out = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        out[key(r)][0] += r["passed"]
        out[key(r)][1] += 1
    return {k: f"{v[0]}/{v[1]}" for k, v in sorted(out.items())}


def summarize(campaign, with_director):
    rows, manifest = load(campaign)
    version, cases = cases_for(rows)
    n = len(rows)
    k = sum(r["passed"] for r in rows)
    by_case = collections.defaultdict(list)
    for r in rows:
        by_case[r["case_id"]].append(r["passed"])
    all3 = sum(all(v) for v in by_case.values())
    summary = {
        "campaign": campaign,
        "dataset_version": version,
        "stage": manifest.get("stage"),
        "trials": n,
        "passed": k,
        "pass_rate": round(k / n, 3),
        "wilson95": wilson(k, n),
        "cases": len(by_case),
        "cases_all_three_pass": all3,
        "critical_failures": sum(bool(r["critical_failure"]) for r in rows),
        "tokens": {
            "input": sum(r["usage"]["input_tokens"] for r in rows),
            "output": sum(r["usage"]["output_tokens"] for r in rows),
        },
        "by_expected_action": tally(rows, lambda r: cases[r["case_id"]]["expected"]["action"]),
        "by_family": tally(rows, lambda r: r["family"]),
        "by_domain": tally(rows, lambda r: r["domain"]),
        "by_language": tally(rows, lambda r: r["language"]),
        "source": f"artifacts/evals/live/{campaign}/trials.jsonl",
    }
    if with_director:
        after = 0
        replay_by_action = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            case = cases[r["case_id"]]
            action = r["prediction"]["action"]
            specific, risky, _ = director.direct(
                case["input"], action == "answer", action == "escalate"
            )
            ok = (
                r["prediction"]["category"] == case["expected"]["category"]
                and director.decide_action(risky, specific) == case["expected"]["action"]
            )
            after += ok
            replay_by_action[case["expected"]["action"]][0] += ok
            replay_by_action[case["expected"]["action"]][1] += 1
        summary["director_replay"] = {
            "passed": after,
            "pass_rate": round(after / n, 3),
            "wilson95": wilson(after, n),
            "by_expected_action": {
                k2: f"{v[0]}/{v[1]}" for k2, v in sorted(replay_by_action.items())
            },
            "note": "Exact replay over the recorded trials; the director rules were written after reading these development tickets, so this is in-sample.",
        }
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaigns", nargs="+")
    parser.add_argument(
        "--director", nargs="*", default=[], help="campaigns to replay with the director"
    )
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for campaign in args.campaigns:
        summary = summarize(campaign, campaign in args.director)
        path = OUT / f"{campaign}.json"
        path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        print(path.relative_to(PROJECT), summary["passed"], "/", summary["trials"])


if __name__ == "__main__":
    main()
