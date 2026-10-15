"""Strict JSONL cassette parsing for deterministic, ordered replay."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class CassetteError(ValueError):
    pass


class CassetteRecorder:
    """Append request/response records for an explicitly chosen local cassette."""

    def __init__(self, client, path: str | Path) -> None:
        self.client = client
        self.path = Path(path)
        self._lock = threading.Lock()

    def complete(self, messages, *, schema=None, tools=None, model=None):
        from .client import LLMResponse, Message

        normalized = [
            {"role": item.role, "content": item.content}
            if isinstance(item, Message)
            else {"role": item["role"], "content": item["content"]}
            for item in messages
        ]
        response = self.client.complete(messages, schema=schema, tools=tools, model=model)
        if not isinstance(response, LLMResponse):
            raise TypeError("recorded clients must return LLMResponse")
        record = {
            "request": {"messages": normalized, "tools": list(tools or []), "model": model},
            "response": {
                "text": response.text,
                "tool_calls": [item.model_dump(mode="json") for item in response.tool_calls],
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                "estimated_cost_usd": str(response.estimated_cost_usd),
                "latency_ms": response.latency_ms,
                "model": response.model,
                "provider": response.provider,
            },
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
        return response


def load_cassette(path: str | Path) -> list[dict[str, Any]]:
    records = []
    try:
        with Path(path).open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise CassetteError(f"invalid JSON at line {line_number}") from exc
                if (
                    not isinstance(record, dict)
                    or not isinstance(record.get("request"), dict)
                    or not isinstance(record.get("response"), dict)
                ):
                    raise CassetteError(
                        f"line {line_number} must contain request and response objects"
                    )
                request, response = record["request"], record["response"]
                if not isinstance(request.get("messages"), list) or not isinstance(
                    request.get("tools", []), list
                ):
                    raise CassetteError(f"line {line_number} has invalid request messages or tools")
                if not isinstance(response.get("text"), str):
                    raise CassetteError(f"line {line_number} response must contain text")
                if not isinstance(response.get("usage", {}), dict) or not isinstance(
                    response.get("tool_calls", []), list
                ):
                    raise CassetteError(
                        f"line {line_number} has invalid response usage or tool calls"
                    )
                records.append(record)
    except OSError as exc:
        raise CassetteError(f"cannot read cassette: {path}") from exc
    return records
