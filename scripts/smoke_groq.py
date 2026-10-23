"""Run one sanitized, budget-capped live smoke check against Groq."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from supportops_foundation.llm import (
    Budget,
    GroqKeyRotationTransport,
    LiveClient,
    Message,
)

ROOT = Path(__file__).resolve().parents[3]
PROJECT = Path(__file__).resolve().parents[1]
MODEL_ENDPOINT = "https://api.groq.com/openai/v1/models"
CHAT_ENDPOINT = "https://api.groq.com/openai/v1"
MAX_BUDGET_USD = Decimal("0.05")
OPENROUTER_MODELS_ENDPOINT = "https://openrouter.ai/api/v1/models"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1"


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
    names = ["GROQ_API_KEY", *(f"GROQ_API_KEY_{index}" for index in range(1, 5))]
    return list(
        dict.fromkeys(os.getenv(name, "").strip() for name in names if os.getenv(name, "").strip())
    )


def list_models_for_valid_keys(keys: list[str]) -> tuple[list[str], set[str]]:
    valid_keys: list[str] = []
    model_ids: set[str] = set()
    for key in keys:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        request = Request(MODEL_ENDPOINT, headers=headers)
        try:
            with urlopen(request, timeout=15) as response:
                models = json.loads(response.read())
        except HTTPError as exc:
            if exc.code in (401, 403):
                continue
            raise RuntimeError(f"model-list request returned HTTP {exc.code}") from exc
        except (TimeoutError, URLError, OSError) as exc:
            raise RuntimeError(f"model-list request failed: {type(exc).__name__}") from exc
        valid_keys.append(key)
        model_ids.update(
            item.get("id") for item in models.get("data", []) if isinstance(item, dict)
        )
    if not valid_keys:
        raise RuntimeError("all configured Groq credentials were rejected with HTTP 401/403")
    return valid_keys, model_ids


def run_openrouter_free(result: dict[str, object]) -> None:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Groq credentials/model unavailable and OPENROUTER_API_KEY is missing")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        with urlopen(Request(OPENROUTER_MODELS_ENDPOINT, headers=headers), timeout=15) as response:
            models = json.loads(response.read())
    except HTTPError as exc:
        raise RuntimeError(f"OpenRouter model-list request returned HTTP {exc.code}") from exc
    except (TimeoutError, URLError, OSError) as exc:
        raise RuntimeError(f"OpenRouter model-list request failed: {type(exc).__name__}") from exc
    model_ids = {item.get("id") for item in models.get("data", []) if isinstance(item, dict)}
    if "openrouter/free" not in model_ids:
        raise RuntimeError("OpenRouter free-model router is not available to this account")

    os.environ["LLM_MAX_COMPLETION_TOKENS"] = "128"
    client = LiveClient(
        endpoint=OPENROUTER_ENDPOINT,
        api_key=key,
        budget=Budget(MAX_BUDGET_USD),
        input_usd_per_million=Decimal(0),
        output_usd_per_million=Decimal(0),
        timeout_seconds=20,
    )
    response = client.complete(
        [Message("user", "Reply with exactly: Free model live smoke check passed.")],
        model="openrouter/free",
    )
    result.update(
        provider="openrouter-free",
        model="openrouter/free",
        routed_model=response.model,
        model_available=True,
        status="PASS",
        exit_code=0,
        usage={
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
        estimated_cost_usd="0",
        latency_ms=response.latency_ms,
        attempts=1,
        response_characters=len(response.text),
    )


def write_evidence(result: dict[str, object]) -> None:
    evidence = PROJECT / "artifacts" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "groq-live-smoke.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "Command: python scripts/smoke_groq.py",
        f"Exit code: {result['exit_code']}",
        f"Status: {result['status']}",
        f"Model: {result.get('model', 'PENDING')}",
        f"Credential count (values withheld): {result.get('credential_count', 0)}",
        f"Usage: {result.get('usage', 'PENDING')}",
        f"Estimated cost USD: {result.get('estimated_cost_usd', 'PENDING')}",
        f"Latency ms: {result.get('latency_ms', 'PENDING')}",
        f"Error: {result.get('error', 'none')}",
    ]
    (evidence / "groq-live-smoke.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    result: dict[str, object] = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "provider": "groq",
        "budget_cap_usd": str(MAX_BUDGET_USD),
        "status": "INCOMPLETE",
        "exit_code": 1,
    }
    try:
        load_root_env()
        keys = collect_keys()
        result["credential_count"] = len(keys)
        model = os.getenv("GROQ_MODEL", "").strip()
        if not keys:
            raise RuntimeError("no GROQ_API_KEY credentials are configured")
        model = os.getenv("GROQ_MODEL", "").strip()
        groq_ready = False
        if keys and model:
            try:
                keys, model_ids = list_models_for_valid_keys(keys)
                result["valid_credential_count"] = len(keys)
                groq_ready = model in model_ids
            except RuntimeError as exc:
                if "all configured Groq credentials were rejected" not in str(exc):
                    raise
                result["groq_credential_status"] = "rejected"
        if groq_ready:
            result.update(provider="groq", model=model, model_available=True)
            os.environ["LLM_MAX_COMPLETION_TOKENS"] = "128"
            transport = GroqKeyRotationTransport(keys, max_attempts=3, backoff_seconds=0.25)
            client = LiveClient(
                endpoint=CHAT_ENDPOINT,
                api_key=keys[0],
                budget=Budget(MAX_BUDGET_USD),
                input_usd_per_million=Decimal("0.075"),
                output_usd_per_million=Decimal("0.30"),
                transport=transport,
                timeout_seconds=15,
            )
            response = client.complete(
                [Message("user", "Reply with exactly: Groq live smoke check passed.")],
                model=model,
            )
            result.update(
                status="PASS",
                exit_code=0,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                estimated_cost_usd=str(response.estimated_cost_usd),
                latency_ms=response.latency_ms,
                attempts=transport.last_attempt_count,
                response_characters=len(response.text),
            )
        else:
            result["groq_model_available"] = False if model else "GROQ_MODEL missing"
            run_openrouter_free(result)
        return_code = 0
    except (RuntimeError, ValueError, OSError, HTTPError, URLError, json.JSONDecodeError) as exc:
        result["error"] = f"{type(exc).__name__}: {str(exc)[:180]}"
        return_code = 1
    finally:
        result["finished_at_utc"] = datetime.now(UTC).isoformat()
        result["exit_code"] = return_code if "return_code" in locals() else 1
        write_evidence(result)
        print(json.dumps(result, sort_keys=True))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
