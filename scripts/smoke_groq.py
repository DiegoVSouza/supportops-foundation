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
    print(
        json.dumps(
            {
                "status": "INCOMPLETE",
                "reason": "accounted_guard_required",
                "provider_accessed": False,
                "credentials_read": False,
            }
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
