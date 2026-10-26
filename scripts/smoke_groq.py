"""Run one sanitized, budget-capped live smoke check against Groq."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal
from urllib.error import HTTPError, URLError

from pydantic import BaseModel

from supportops_foundation.llm import (
    Budget,
    GroqKeyRotationTransport,
    LiveClient,
    Message,
)

ROOT = Path(__file__).resolve().parents[3]
PROJECT = Path(__file__).resolve().parents[1]
CHAT_ENDPOINT = "https://api.groq.com/openai/v1"
MAX_BUDGET_USD = Decimal("0.05")
DEFAULT_MODEL = "openai/gpt-oss-20b"


class Assessment(BaseModel):
    decision: Literal["answer", "escalate"]
    tool: Literal["lookup_invoice", "issue_refund", "search_kb"]
    escalate: bool


class GroqSDKTransport:
    """Adapt the official SDK to P00's budgeted OpenAI-compatible transport."""

    def __init__(self) -> None:
        self.last_content_metadata: dict[str, object] = {}

    def post(self, url: str, headers: dict[str, str], body: bytes, timeout: float) -> bytes:
        from groq import Groq, GroqError

        api_key = headers.get("Authorization", "").removeprefix("Bearer ").strip()
        try:
            completion = Groq(
                api_key=api_key, max_retries=0, timeout=timeout
            ).chat.completions.create(**json.loads(body))
            content = completion.choices[0].message.content or ""
            self.last_content_metadata = {
                "content_length": len(content),
                "starts_with_json_object": content.lstrip().startswith("{"),
                "ends_with_json_object": content.rstrip().endswith("}"),
            }
            payload = json.loads(completion.model_dump_json())
            for choice in payload.get("choices", []):
                message = choice.get("message") or {}
                if message.get("tool_calls") is None:
                    message["tool_calls"] = []
            return json.dumps(payload).encode("utf-8")
        except GroqError as exc:
            status = getattr(exc, "status_code", None)
            if status is not None:
                response = getattr(exc, "response", None)
                response_headers = getattr(response, "headers", {})
                raise HTTPError(
                    url, int(status), type(exc).__name__, response_headers, None
                ) from None
            if type(exc).__name__ in {"Timeout", "APIConnectionError"}:
                raise URLError(type(exc).__name__) from None
            raise


def load_root_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        raise RuntimeError("lab-root .env is missing")
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip().strip('"').strip("'")
        if name and value and name not in os.environ:
            os.environ[name] = value


def collect_keys() -> list[str]:
    names = [f"GROQ_API_KEY_{index}" for index in range(1, 5)]
    return list(
        dict.fromkeys(os.getenv(name, "").strip() for name in names if os.getenv(name, "").strip())
    )


def list_models_for_valid_keys(keys: list[str]) -> tuple[list[str], set[str]]:
    from groq import Groq, GroqError

    valid_keys: list[str] = []
    model_ids: set[str] = set()
    for key in keys:
        try:
            models = Groq(api_key=key, max_retries=0, timeout=15).models.list()
        except GroqError as exc:
            status = getattr(exc, "status_code", None)
            if status in (401, 403):
                continue
            raise RuntimeError(
                f"model-list request failed ({type(exc).__name__}, status={status})"
            ) from None
        valid_keys.append(key)
        model_ids.update(item.id for item in models.data if getattr(item, "id", None))
    if not valid_keys:
        raise RuntimeError("all configured Groq credentials were rejected with HTTP 401/403")
    return valid_keys, model_ids


def write_evidence(result: dict[str, object]) -> None:
    evidence = PROJECT / "artifacts" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    (evidence / f"phase-005-groq-live-{stamp}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "Command: LLM_MODE=live uv run --extra live python scripts/smoke_groq.py",
        f"Exit code: {result['exit_code']}",
        f"Status: {result['status']}",
        f"Model: {result.get('model', 'PENDING')}",
        f"Credential count (values withheld): {result.get('credential_count', 0)}",
        f"Usage: {result.get('usage', 'PENDING')}",
        f"Estimated cost USD: {result.get('estimated_cost_usd', 'PENDING')}",
        f"Latency ms: {result.get('latency_ms', 'PENDING')}",
        f"Error class/status: {result.get('error', 'none')}",
    ]
    (evidence / f"phase-005-groq-live-{stamp}.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    result: dict[str, object] = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "provider": "groq",
        "budget_cap_usd": str(MAX_BUDGET_USD),
        "status": "INCOMPLETE",
        "exit_code": 1,
    }
    try:
        if os.getenv("LLM_MODE", "").strip().lower() != "live":
            raise RuntimeError("set LLM_MODE=live explicitly to run the Groq evaluation")
        load_root_env()
        keys = collect_keys()
        result["credential_count"] = len(keys)
        model = os.getenv("GROQ_MODEL", DEFAULT_MODEL).strip()
        if not keys:
            raise RuntimeError("no GROQ_API_KEY credentials are configured")
        if not model:
            raise RuntimeError("GROQ_MODEL must identify one explicit Groq model")
        keys, model_ids = list_models_for_valid_keys(keys)
        result["valid_credential_count"] = len(keys)
        if model not in model_ids:
            raise RuntimeError("requested Groq model is unavailable in the authenticated catalog")
        result.update(provider="groq", model=model, model_available=True)
        os.environ["LLM_MAX_COMPLETION_TOKENS"] = "256"
        transport = GroqKeyRotationTransport(
            keys, max_attempts=min(4, len(keys)), backoff_seconds=0.25, transport=GroqSDKTransport()
        )
        client = LiveClient(
            endpoint=CHAT_ENDPOINT,
            api_key=keys[0],
            budget=Budget(MAX_BUDGET_USD),
            input_usd_per_million=Decimal("0.075"),
            output_usd_per_million=Decimal("0.30"),
            transport=transport,
            timeout_seconds=15,
        )
        prompt = (
            "Classify this synthetic support request: a customer asks how to find the tracking link for a delayed parcel. "
            "Return exactly one JSON object with required keys decision (answer or escalate), tool "
            "(lookup_invoice, issue_refund, or search_kb), and escalate (boolean). No markdown or explanation. "
            "Use support knowledge for a generic tracking question; do not claim a live carrier lookup."
        )
        response = client.complete(
            [Message("user", prompt)],
            schema=Assessment,
            model=model,
        )
        expected = {"decision": "answer", "tool": "search_kb", "escalate": False}
        prediction = response.parsed.model_dump()
        assertions = {name: prediction.get(name) == value for name, value in expected.items()}
        status = "PASS" if all(assertions.values()) else "FAIL"
        result.update(
            status=status,
            exit_code=0 if status == "PASS" else 1,
            actual_model=response.model,
            expected=expected,
            prediction=prediction,
            assertions=assertions,
            failure_category=next(
                (f"{name}_mismatch" for name, ok in assertions.items() if not ok), None
            ),
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            estimated_cost_usd=str(response.estimated_cost_usd),
            latency_ms=response.latency_ms,
            attempts=transport.last_attempt_count,
        )
        return_code = 0 if status == "PASS" else 1
    except (RuntimeError, ValueError, OSError, HTTPError, URLError, json.JSONDecodeError) as exc:
        cause = exc.__cause__
        result["error"] = {
            "class": type(exc).__name__,
            "cause_class": type(cause).__name__ if cause is not None else None,
            "status": getattr(cause, "code", getattr(exc, "code", None)),
        }
        if "transport" in locals():
            sdk_transport = getattr(transport, "transport", None)
            if sdk_transport is not None:
                result["error"].update(sdk_transport.last_content_metadata)
        if cause is not None and hasattr(cause, "errors"):
            result["error"]["validation_issues"] = [
                {"path": list(item.get("loc", ())), "type": item.get("type")}
                for item in cause.errors()
            ]
        return_code = 1
    finally:
        result["finished_at_utc"] = datetime.now(UTC).isoformat()
        result["exit_code"] = return_code if "return_code" in locals() else 1
        write_evidence(result)
        print(json.dumps(result, sort_keys=True))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
