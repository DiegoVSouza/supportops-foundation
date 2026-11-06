"""Run the live-v3 DEVELOPMENT split against a local Ollama model as a prompt-iteration proxy.

This is not campaign evidence: the campaign model is Groq openai/gpt-oss-20b, a local model
behaves differently, and nothing here touches the shared policy, the ledgers or the budget.
Use it to compare candidate prompts cheaply; quality claims still come only from the sealed
runs. The final split is never loaded: this tool refuses any case that is not development.

  python evals/proxy/local_proxy_eval.py --model llama3.1:8b-instruct-q4_K_M --prompt agent/prompts/live-campaign.md
  python evals/proxy/local_proxy_eval.py --model <name> --prompt <file> --limit 20
"""

import argparse
import json
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))

from scripts.campaign_execution import complete_prediction  # noqa: E402
from scripts.run_live_campaign import validate_prediction  # noqa: E402

HOST = "http://127.0.0.1:11434"


def chat(model, system, user, schema, timeout):
    body = json.dumps(
        {
            "model": model,
            "stream": False,
            "format": schema,
            "options": {"temperature": 0, "seed": 7, "num_predict": 200},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
    ).encode()
    request = urllib.request.Request(
        HOST + "/api/chat", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())["message"]["content"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    schema = json.loads((PROJECT / "agent/schemas/live-decision.json").read_text(encoding="utf-8"))
    system = args.prompt.read_text(encoding="utf-8").strip()
    manifest = json.loads((PROJECT / "evals/datasets/live-v3/manifest.json").read_text(encoding="utf-8"))
    cases = [
        json.loads(line)
        for line in (PROJECT / "evals/datasets/live-v3/cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    cases = [case for case in cases if case["split"] == "development"]
    if args.limit:
        cases = cases[: args.limit]

    rows = []
    started = time.time()
    for case in cases:
        try:
            content = chat(args.model, system, case["input"], schema, args.timeout)
            prediction = complete_prediction(json.loads(content))
            issues = validate_prediction(case, prediction)
            decision = prediction.get("decision", {}) if isinstance(prediction, dict) else {}
            got = (decision.get("category"), decision.get("action"))
        except Exception as error:  # noqa: BLE001 - a failed call is a failed trial, not a crash
            issues, got = [f"error: {type(error).__name__}"], (None, None)
        rows.append(
            {
                "case_id": case["case_id"],
                "action": case["expected"]["action"],
                "family": case["family"],
                "language": case["language"],
                "passed": not issues,
                "got": got,
                "issues": issues,
            }
        )

    passed = sum(row["passed"] for row in rows)
    by_action = defaultdict(lambda: [0, 0])
    by_family = defaultdict(lambda: [0, 0])
    for row in rows:
        by_action[row["action"]][0] += row["passed"]
        by_action[row["action"]][1] += 1
        by_family[row["family"]][0] += row["passed"]
        by_family[row["family"]][1] += 1
    summary = {
        "NOTE": "local proxy, development split only, NOT campaign evidence",
        "model": args.model,
        "prompt": str(args.prompt),
        "dataset_version": manifest["dataset_version"],
        "cases": len(rows),
        "passed": passed,
        "by_action": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_action.items())},
        "by_family": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_family.items())},
        "errors": dict(Counter(issue for row in rows for issue in row["issues"])),
        "seconds": round(time.time() - started, 1),
    }
    print(json.dumps(summary, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
