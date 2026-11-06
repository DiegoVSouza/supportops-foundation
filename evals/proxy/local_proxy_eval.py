"""Run the live-v3 DEVELOPMENT split against a non-campaign backend as a prompt-iteration proxy.

This is not campaign evidence: the campaign model is Groq openai/gpt-oss-20b under the sealed
runner. Backends here (a local Ollama model, or the same open-weights model on the Cloudflare
Workers AI free tier) use a different inference stack, and nothing here touches the shared
policy, the ledgers or the Groq budget. Use it to compare candidate prompts; quality claims
still come only from the sealed runs. The final split is never loaded: this tool keeps only
development cases.

  python evals/proxy/local_proxy_eval.py --cloudflare --prompt agent/prompts/live-campaign.md
  python evals/proxy/local_proxy_eval.py --model llama3.1:8b-instruct-q4_K_M --prompt <file>
"""

import argparse
import json
import os
import re
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
CF_SUFFIX = (
    "\nReply with only this JSON: "
    '{"decision":{"category":"billing|account_access|technical|shipping|other",'
    '"action":"answer|request_info|escalate","rationale":"short"}}'
)
CF_SUFFIX_FEATURES = (
    "\nReply with only this JSON: "
    '{"decision":{"category":"billing|account_access|technical|shipping|other",'
    '"specific":true,"risky":false,"rationale":"short"}}'
)
# Published Workers AI rates for @cf/openai/gpt-oss-20b, in neurons per million tokens.
CF_NEURONS_IN, CF_NEURONS_OUT = 18182, 27273


def load_env_value(name):
    value = os.environ.get(name)
    if value:
        return value
    pattern = re.compile(r"\s*(?:export\s+)?" + name + r"\s*=\s*(.*?)\s*$")
    for line in (PROJECT.parents[1] / ".env").read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip('"').strip("'")
    raise SystemExit(f"{name} is not set in the environment or in the lab .env")


def cloudflare_chat(system, user, timeout, seed=7, features=False):
    """Free-tier Cloudflare Workers AI. It does not enforce a JSON schema, so the contract is
    requested in the prompt plus `json_object` mode and validated by the same grader.
    Returns (content, prompt_tokens, completion_tokens) so the caller can count neurons."""
    account = load_env_value("CLOUDFLARE_ACCOUNT_ID")
    token = load_env_value("CLOUDFLARE_API_TOKEN")
    body = json.dumps(
        {
            "model": "@cf/openai/gpt-oss-20b",
            "temperature": 0,
            "seed": seed,
            "max_tokens": 1500,
            "reasoning_effort": "low",
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": system + (CF_SUFFIX_FEATURES if features else CF_SUFFIX),
                },
                {"role": "user", "content": user},
            ],
        }
    ).encode()
    request = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read())
    usage = data.get("usage") or {}
    return (
        data["choices"][0]["message"]["content"],
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0),
    )


def ollama_chat(model, system, user, schema, timeout, cpu=False):
    payload = {
        "model": model,
        "stream": False,
        "format": schema,
        "options": {"temperature": 0, "seed": 7, "num_predict": 200},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    if "gpt-oss" in model:
        payload["think"] = "low"
        payload["options"]["num_predict"] = 1500
    if cpu:
        # The CUDA runner of the tested Ollama build crashes on an RTX 5060 Ti; CPU is stable.
        payload["options"]["num_gpu"] = 0
    request = urllib.request.Request(
        HOST + "/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())["message"]["content"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="@cf/openai/gpt-oss-20b")
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--cpu", action="store_true", help="force CPU inference (Ollama)")
    parser.add_argument("--cloudflare", action="store_true", help="Cloudflare Workers AI free tier")
    parser.add_argument(
        "--neuron-cap", type=int, default=8000, help="stop before this many neurons"
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--features",
        action="store_true",
        help="ask for category/specific/risky; the runner derives the action",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    schema = json.loads((PROJECT / "agent/schemas/live-decision.json").read_text(encoding="utf-8"))
    system = args.prompt.read_text(encoding="utf-8").strip()
    manifest = json.loads(
        (PROJECT / "evals/datasets/live-v3/manifest.json").read_text(encoding="utf-8")
    )
    cases = [
        json.loads(line)
        for line in (PROJECT / "evals/datasets/live-v3/cases.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    cases = [case for case in cases if case["split"] == "development"]
    if args.limit:
        cases = cases[: args.limit]

    rows = []
    started = time.time()
    neurons = 0.0
    tokens_in = tokens_out = 0
    stopped = None
    for case in cases:
        if args.cloudflare and neurons >= args.neuron_cap:
            stopped = f"neuron cap {args.neuron_cap} reached; remaining cases not run"
            break
        try:
            if args.cloudflare:
                content, used_in, used_out = cloudflare_chat(
                    system, case["input"], args.timeout, args.seed, args.features
                )
                tokens_in += used_in
                tokens_out += used_out
                neurons += used_in * CF_NEURONS_IN / 1e6 + used_out * CF_NEURONS_OUT / 1e6
            else:
                content = ollama_chat(
                    args.model, system, case["input"], schema, args.timeout, args.cpu
                )
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
        "NOTE": "proxy backend, development split only, NOT campaign evidence",
        "backend": "cloudflare-workers-ai" if args.cloudflare else "ollama",
        "model": args.model,
        "seed": args.seed,
        "features": args.features,
        "prompt": str(args.prompt),
        "dataset_version": manifest["dataset_version"],
        "cases": len(rows),
        "passed": passed,
        "by_action": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_action.items())},
        "by_family": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_family.items())},
        "errors": dict(Counter(issue for row in rows for issue in row["issues"])),
        "seconds": round(time.time() - started, 1),
    }
    if args.cloudflare:
        summary["tokens"] = {"input": tokens_in, "output_incl_reasoning": tokens_out}
        summary["estimated_neurons"] = round(neurons, 1)
    if stopped:
        summary["stopped"] = stopped
    print(json.dumps(summary, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
