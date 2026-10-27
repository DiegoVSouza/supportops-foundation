"""Read-only logical/provider/account ledger reconciliation; no provider imports."""

import json
import sqlite3
from contextlib import closing
from decimal import Decimal
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
LAB = PROJECT.parents[1]


def rows(path, table):
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM " + table + " ORDER BY sequence")]


def latest(events, fields):
    result = {}
    for event in events:
        result[tuple(event[name] for name in fields)] = event
    return list(result.values())


logical = latest(rows(PROJECT / "artifacts/evals/live/ledger.sqlite", "events"), ("project", "campaign_id", "case_id", "trial"))
provider = latest(rows(PROJECT / "artifacts/evals/live/provider-usage.sqlite", "usage_events"), ("attempt_id",))
registry = json.loads((LAB / ".runtime/llm-live-readiness/ledger-references.json").read_text())
policy = json.loads((LAB / "shared/policies/groq-free-campaign.json").read_text())


def totals(events, input_key, output_key, reserved_input_key, reserved_output_key, actual_cost_key, reserved_cost_key):
    return {
        "attempts": len(events),
        "known_input": sum(event[input_key] or 0 for event in events),
        "known_output": sum(event[output_key] or 0 for event in events),
        "unknown_attempts": sum(event[input_key] is None or event[output_key] is None for event in events),
        "reserved_unknown_input": sum(event[reserved_input_key] for event in events if event[input_key] is None),
        "reserved_unknown_output": sum(event[reserved_output_key] for event in events if event[output_key] is None),
        "charged_input": sum(event[input_key] if event[input_key] is not None else event[reserved_input_key] for event in events),
        "charged_output": sum(event[output_key] if event[output_key] is not None else event[reserved_output_key] for event in events),
        "charged_economic_estimate_usd": str(sum(Decimal(event[actual_cost_key] if event[actual_cost_key] is not None else event[reserved_cost_key]) for event in events)),
    }


logical_totals = totals(logical, "actual_input_tokens", "actual_output_tokens", "reserved_input_tokens", "reserved_output_tokens", "actual_cost_usd", "reserved_cost_usd")
provider_totals = totals(provider, "actual_input", "actual_output", "reserved_input", "reserved_output", "actual_cost", "reserved_cost")
identities = {}
account_attempts = 0
for project, identity in registry["projects"].items():
    path = LAB / "projects" / project / "artifacts/evals/live/provider-usage.sqlite"
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        observed = db.execute("SELECT identity FROM identity").fetchone()[0]
    assert observed == identity, "Registry identity mismatch"
    identities[project] = observed
    account_attempts += len(latest(rows(path, "usage_events"), ("attempt_id",)))
primary = {
    "calls": 126 - logical_totals["attempts"],
    "input_tokens": 258048 - logical_totals["charged_input"],
    "output_tokens": 32256 - logical_totals["charged_output"],
    "economic_estimate_usd": str(Decimal("0.0290304") - Decimal(logical_totals["charged_economic_estimate_usd"])),
}
required = {"calls": 120, "input_tokens": 120 * 2048, "output_tokens": 120 * 256, "economic_estimate_usd": "0.0276480"}
assert logical_totals["attempts"] == provider_totals["attempts"] == 16
assert sum(p["requests"] for p in policy["projects"].values()) == policy["campaign_caps"]["requests"] == 4074
report = {
    "remaining_project_commitments": {
        project: {
            "pilot_and_original_main_calls": (6 + cases * 3) * policy["projects"][project]["calls_per_trial"],
            "protected_confirmation_calls": 60 * policy["projects"][project]["calls_per_trial"],
            "policy_allocation_calls": policy["projects"][project]["requests"],
            "unallocated_calls_before_any_consumption": policy["projects"][project]["requests"] - (6 + cases * 3 + 60) * policy["projects"][project]["calls_per_trial"],
        }
        for project, cases in {"p00": 40, "p01": 60, "p02": 80, "p03": 30, "p04": 60, "p05": 120}.items()
    },
    "logical": logical_totals,
    "provider_account": provider_totals,
    "ledgers_are_not_additive": True,
    "registry_identities": identities,
    "registered_account_attempts": account_attempts,
    "account_request_cap": 4074,
    "account_request_cap_remaining": 4074 - account_attempts,
    "primary_remaining": primary,
    "fresh_development_and_holdout_requirement": required,
    "minimum_deficit": {
        "calls": max(0, required["calls"] - primary["calls"]),
        "input_tokens": max(0, required["input_tokens"] - primary["input_tokens"]),
        "output_tokens": max(0, required["output_tokens"] - primary["output_tokens"]),
        "economic_estimate_usd": str(max(Decimal(0), Decimal(required["economic_estimate_usd"]) - Decimal(primary["economic_estimate_usd"]))),
    },
    "confirmation_protected": {"calls": 60, "input_tokens": 122880, "output_tokens": 15360, "economic_estimate_usd": "0.013824"},
    "billed_amount_usd": None,
    "billing_tier": "UNVERIFIED",
    "provider_accessed": False,
    "credentials_read": False,
    "ledger_registry_policy_writes": 0,
    "status": "INCOMPLETE",
}
print(json.dumps(report, indent=2))
