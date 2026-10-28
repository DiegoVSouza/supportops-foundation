"""Explicit synthetic-only local live operation through the accounted transport."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from scripts.campaign_execution import (
    ProviderClient,
    build_payload,
    fingerprint,
    require_committed_sources,
)

PROJECT = Path(__file__).resolve().parents[1]
LAB = PROJECT.parents[1]
sys.path.insert(0, str(LAB / "scripts/harness"))
from live_free_account import AccountBlocked, SharedAccount, machine_lease


class LocalLiveBlocked(RuntimeError):
    """A sanitized stop that does not permit another attempt."""


def require_committed_operation_config(project):
    path = "evals/local-live-operation.json"
    for command in (
        ["git", "ls-files", "--error-unmatch", "--", path],
        ["git", "diff", "--quiet", "HEAD", "--", path],
    ):
        try:
            result = subprocess.run(
                command, cwd=project, capture_output=True, timeout=10, check=False
            )
        except (OSError, subprocess.SubprocessError):
            raise LocalLiveBlocked("operational_configuration_not_committed") from None
        if result.returncode:
            raise LocalLiveBlocked("operational_configuration_not_committed")


def run_operation(
    project,
    request_id,
    text,
    *,
    account_factory=SharedAccount,
    client_factory=ProviderClient,
    lease_factory=machine_lease,
    mode=None,
):
    project = Path(project)
    lab = project.parents[1]
    if (mode if mode is not None else os.getenv("LLM_MODE", "fake")) != "live":
        raise LocalLiveBlocked("explicit_live_mode_required")
    if not isinstance(request_id, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", request_id
    ):
        raise LocalLiveBlocked("stable_request_id_required")
    if not isinstance(text, str) or not text.strip() or len(text.encode("utf-8")) > 512:
        raise LocalLiveBlocked("bounded_synthetic_input_required")
    try:
        config = json.loads((project / "evals/local-live-operation.json").read_text())
        policy = json.loads((lab / "shared/policies/groq-free-campaign.json").read_text())
        policy_sha = hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest()
        registry = json.loads(
            (lab / ".runtime/llm-live-readiness/ledger-references.json").read_text()
        )
        if (
            config.get("enabled") is not True
            or config.get("synthetic_only") is not True
            or config.get("authorized_paid_spend_usd") != "0.00"
            or config.get("campaign_id") != "local-live-operation-v1"
            or type(config.get("max_calls")) is not int
            or config["max_calls"] != 10
            or config.get("preexisting_p00_calls") != 65
            or config.get("protected_holdout_calls") != 84
            or config.get("protected_confirmation_calls") != 60
            or config.get("policy_sha256") != policy_sha
            or registry.get("policy_sha256") != policy_sha
            or policy["projects"]["p00"]["requests"] != 219
            or policy.get("authorized_paid_spend_usd") != "0.00"
        ):
            raise LocalLiveBlocked("operational_allocation_not_applied")
        require_committed_operation_config(project)
        require_committed_sources(
            project, fingerprint(project, lab / "shared/policies/groq-free-campaign.json")
        )
        prompt = (project / "agent/prompts/live-campaign.md").read_text(encoding="utf-8").strip()
        payload = build_payload(project, prompt, text, {"model": policy["model"]})
    except LocalLiveBlocked:
        raise
    except (OSError, ValueError, KeyError, TypeError):
        raise LocalLiveBlocked("operational_configuration_unavailable") from None

    with lease_factory(lab / ".runtime/llm-live-readiness/campaign.lock"):
        account = account_factory(lab, policy)
        rows = account._history()
        p00 = [row for row in rows if row["project"] == "p00"]
        operation = [row for row in p00 if row["campaign"] == config["campaign_id"]]
        if len(p00) >= 65 + config["max_calls"] or len(operation) >= config["max_calls"]:
            raise LocalLiveBlocked("operational_allocation_exhausted")
        if any(row["event"] == "reserved" for row in rows):
            raise LocalLiveBlocked("uncertain_attempt_requires_reconciliation")
        if any(row.get("status") != "ok" for row in operation):
            raise LocalLiveBlocked("prior_operational_failure_requires_review")
        if any(row["case_id"] == request_id for row in operation):
            raise LocalLiveBlocked("request_id_already_used")
        try:
            account.preview("p00", config["campaign_id"], request_id, 1, 1, 2048, 256)
        except AccountBlocked as error:
            raise LocalLiveBlocked(str(error)) from None
        client = client_factory(project)
        try:
            result = client.request(
                {
                    "campaign_id": config["campaign_id"],
                    "case_id": request_id,
                    "trial": 1,
                    "call_index": 1,
                    "payload": payload,
                    "timeout_seconds": 15,
                },
                "complete",
            )
        finally:
            client.close()
        if result.get("status") != "ok":
            raise LocalLiveBlocked("provider_result_incomplete_no_replay")
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--synthetic-text", required=True)
    args = parser.parse_args(argv)
    try:
        result = run_operation(PROJECT, args.request_id, args.synthetic_text)
    except (LocalLiveBlocked, AccountBlocked):
        print(json.dumps({"status": "INCOMPLETE", "reason": "local_live_blocked"}))
        return 2
    except Exception:  # noqa: BLE001 - Do not emit credentials or provider exceptions.
        print(json.dumps({"status": "INCOMPLETE", "reason": "local_live_uncertain"}))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
