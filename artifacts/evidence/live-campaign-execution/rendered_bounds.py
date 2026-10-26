"""Inspect the public synthetic payload contract without provider construction."""
import json
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
lab = project.parents[1]
sys.path.insert(0, str(lab / "scripts/harness"))
from live_provider_transport import encode_payload

config = json.loads((project / "evals/live-campaign.json").read_text())
policy = json.loads((lab / "shared/policies/groq-free-campaign.json").read_text())
cases = [json.loads(line) for line in (project / config["cases_path"]).read_text().splitlines()]
prompt = (project / "agent/prompts/live-campaign.md").read_text().strip()
bounds = []
for case in cases:
    _, bound, _ = encode_payload({"model": config["model"], "messages": [
        {"role": "system", "content": prompt}, {"role": "user", "content": case["input"]}],
        "max_completion_tokens": case["max_output_tokens"], "temperature": 0,
        "reasoning_effort": "low", "include_reasoning": False,
        "response_format": {"type": "json_object"}}, policy["projects"]["p00"])
    bounds.append(bound)
print(json.dumps({"cases_checked": len(bounds), "maximum_rendered_input_bound": max(bounds),
    "unchanged_input_cap": 2048, "unchanged_output_cap": 256,
    "pilot_cases": len(config["pilot_case_ids"]), "pilot_maximum_calls": 6,
    "pilot_gross_input_reservation": 12288, "pilot_gross_output_reservation": 1536,
    "approved_free_upper_limits": policy["free_limits"], "paid_authorization_usd": "0.00",
    "human_review": "PENDING", "remaining_daily_tokens": "PENDING",
    "provider_accessed": False, "credentials_read": False}, indent=2, sort_keys=True))
