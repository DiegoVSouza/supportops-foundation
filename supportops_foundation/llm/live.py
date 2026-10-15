"""Budget-gated OpenAI-compatible HTTP adapter with injectable transport."""

from __future__ import annotations

import json
import os
import threading
import time
from decimal import Decimal
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ValidationError

from .client import LLMResponse, Message, Usage
from supportops_foundation.domain import ToolCall


class LiveConfigurationError(RuntimeError):
    pass


class LiveError(RuntimeError):
    pass


class Budget:
    """Thread-safe spend cap; reserves preflight estimates before network I/O."""

    def __init__(self, maximum_usd: Decimal) -> None:
        if maximum_usd <= 0:
            raise ValueError("budget must be positive")
        self.maximum_usd = maximum_usd
        self._reserved = Decimal("0")
        self._lock = threading.Lock()

    @classmethod
    def from_environment(cls) -> "Budget":
        raw = os.getenv("LAB_MAX_USD")
        if not raw:
            raise LiveConfigurationError("LAB_MAX_USD must be set to a positive amount")
        try:
            return cls(Decimal(raw))
        except Exception as exc:
            raise LiveConfigurationError("LAB_MAX_USD must be a positive decimal") from exc

    def reserve(self, estimate: Decimal) -> None:
        if estimate < 0:
            raise ValueError("estimated cost cannot be negative")
        with self._lock:
            if self._reserved + estimate > self.maximum_usd:
                raise LiveError("request blocked by LAB_MAX_USD preflight")
            self._reserved += estimate

    @property
    def reserved_usd(self) -> Decimal:
        with self._lock:
            return self._reserved


class HTTPTransport(Protocol):
    def post(self, url: str, headers: dict[str, str], body: bytes, timeout: float) -> bytes: ...


class UrllibTransport:
    def post(self, url: str, headers: dict[str, str], body: bytes, timeout: float) -> bytes:
        request = Request(url, data=body, headers=headers, method="POST")
        with urlopen(request, timeout=timeout) as response:
            return response.read()


class LiveClient:
    """Adapter for an explicitly configured OpenAI-compatible endpoint.

    Token pricing is supplied by the caller and must be based on verified provider
    pricing; there is no bundled or assumed price list.
    """

    def __init__(
        self, *, endpoint: str | None = None, api_key: str | None = None,
        budget: Budget | None = None, input_usd_per_million: Decimal,
        output_usd_per_million: Decimal, transport: HTTPTransport | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.endpoint = (endpoint or os.getenv("LLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        if not self.endpoint or not self.api_key:
            raise LiveConfigurationError("LLM_BASE_URL and LLM_API_KEY are required")
        if input_usd_per_million < 0 or output_usd_per_million < 0:
            raise LiveConfigurationError("verified token rates must be non-negative")
        self.budget = budget or Budget.from_environment()
        self.input_rate = input_usd_per_million
        self.output_rate = output_usd_per_million
        self.transport = transport or UrllibTransport()
        self.timeout_seconds = timeout_seconds

    def complete(self, messages, schema=None, tools=None, model=None) -> LLMResponse:
        if not model:
            raise LiveConfigurationError("model must be explicitly selected")
        normalized = [
            {"role": item.role, "content": item.content}
            if isinstance(item, Message) else {"role": item["role"], "content": item["content"]}
            for item in messages
        ]
        # Character-based upper bound is conservative for UTF-8 text and avoids a paid tokenizer.
        input_tokens = max(1, sum(len(item["content"]) for item in normalized))
        output_tokens = 4096
        estimate = (Decimal(input_tokens) * self.input_rate + Decimal(output_tokens) * self.output_rate) / Decimal(1_000_000)
        self.budget.reserve(estimate)
        payload: dict[str, Any] = {"model": model, "messages": normalized, "max_completion_tokens": output_tokens}
        if tools:
            payload["tools"] = list(tools)
        started = time.perf_counter()
        try:
            raw_bytes = self.transport.post(
                f"{self.endpoint}/chat/completions",
                {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json.dumps(payload).encode("utf-8"), self.timeout_seconds,
            )
            raw = json.loads(raw_bytes)
            choice = raw["choices"][0]["message"]
            text = choice.get("content") or ""
            usage_raw = raw.get("usage", {})
            usage = Usage(
                input_tokens=usage_raw.get("prompt_tokens", 0),
                output_tokens=usage_raw.get("completion_tokens", 0),
            )
            parsed = schema.model_validate_json(text) if schema is not None else None
            calls = tuple(
                ToolCall(
                    id=item["id"], name=item["function"]["name"],
                    arguments=json.loads(item["function"]["arguments"]),
                )
                for item in choice.get("tool_calls", [])
            )
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, KeyError, IndexError, ValidationError, ValueError) as exc:
            # The reservation remains: a failed request may still have reached the provider.
            raise LiveError(f"provider completion failed after budget reservation: {exc}") from exc
        actual = (Decimal(usage.input_tokens) * self.input_rate + Decimal(usage.output_tokens) * self.output_rate) / Decimal(1_000_000)
        return LLMResponse(
            text=text, parsed=parsed, tool_calls=calls,
            usage=usage, estimated_cost_usd=actual, latency_ms=round((time.perf_counter() - started) * 1000),
            model=raw.get("model", model), provider="openai-compatible",
        )
