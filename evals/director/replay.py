"""Replay the director over recorded Groq trials. Zero provider calls.

The director only post-processes the features the model reported, so the model's outputs do
not change and the replay gives the exact score of the full system on those trials. The
recorded trial keeps the final action, which is enough to recover the features
(escalate -> risky, answer -> specific, request_info -> neither).

  python evals/director/replay.py free-dev-c6 free-dev-c7
"""

import collections
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

import director  # noqa: E402

CASES = {
    case["case_id"]: case
    for case in map(json.loads, (PROJECT / "evals/datasets/live-v3/cases.jsonl").read_text(encoding="utf-8").splitlines())
    if case["split"] == "development"
}


def wilson(k, n):
    z = 1.96
    p = k / n
    center = (p + z * z / 2 / n) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / 4 / n / n) / (1 + z * z / n)
    return round(center - half, 3), round(center + half, 3)


def features_from(prediction):
    action = prediction["action"]
    return action == "answer", action == "escalate"


def replay(campaign):
    path = PROJECT / "artifacts/evals/live" / campaign / "trials.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    before = after = 0
    by_action = collections.defaultdict(lambda: [0, 0, 0])
    fired = collections.Counter()
    harmed = []
    for row in rows:
        case = CASES[row["case_id"]]
        expected = case["expected"]
        prediction = row["prediction"]
        specific, risky = features_from(prediction)
        new_specific, new_risky, reasons = director.direct(case["input"], specific, risky)
        new_action = director.decide_action(new_risky, new_specific)
        ok_before = row["passed"]
        ok_after = prediction["category"] == expected["category"] and new_action == expected["action"]
        before += ok_before
        after += ok_after
        by_action[expected["action"]][0] += ok_before
        by_action[expected["action"]][1] += ok_after
        by_action[expected["action"]][2] += 1
        for reason in reasons:
            fired[reason] += 1
        if ok_before and not ok_after:
            harmed.append((row["case_id"], row["trial"], reasons))
    return rows, before, after, by_action, fired, harmed


def decide_action_proxy(risky, specific):
    return "escalate" if risky else ("answer" if specific else "request_info")


director.decide_action = decide_action_proxy


def main():
    for campaign in sys.argv[1:]:
        rows, before, after, by_action, fired, harmed = replay(campaign)
        n = len(rows)
        print(f"{campaign}: recorded {before}/{n} -> with director {after}/{n} {wilson(after, n)}")
        print("  by expected action (recorded -> director / total):", {k: f"{v[0]}->{v[1]}/{v[2]}" for k, v in sorted(by_action.items())})
        print("  rules fired:", dict(fired), "| trials made worse:", harmed)


if __name__ == "__main__":
    main()
