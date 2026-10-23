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

from pydantic import ValidationError

from supportops_foundation.domain import ToolCall

from .client import LLMResponse, Message, Usage


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
        self._committed = Decimal(0)
        self._in_flight: dict[str, Decimal] = {}
        self._next_reservation = 0
        self._lock = threading.Lock()

    @classmethod
    def from_environment(cls) -> Budget:
        raw = os.getenv("LAB_MAX_USD")
        if not raw:
            raise LiveConfigurationError("LAB_MAX_USD must be set to a positive amount")
        try:
            return cls(Decimal(raw))
        except Exception as exc:
            raise LiveConfigurationError("LAB_MAX_USD must be a positive decimal") from exc

    def reserve(self, estimate: Decimal) -> str:
        if estimate < 0:
            raise ValueError("estimated cost cannot be negative")
        with self._lock:
            if self._committed + sum(self._in_flight.values()) + estimate > self.maximum_usd:
                raise LiveError("request blocked by LAB_MAX_USD preflight")
            self._next_reservation += 1
            reservation_id = str(self._next_reservation)
            self._in_flight[reservation_id] = estimate
            return reservation_id

    def reconcile(self, reservation_id: str, actual_cost: Decimal) -> None:
        """Replace a preflight reservation with observed provider usage atomically."""
        if actual_cost < 0:
            raise ValueError("actual cost cannot be negative")
        with self._lock:
            try:
                self._in_flight.pop(reservation_id)
            except KeyError as exc:
                raise ValueError("unknown or already reconciled reservation") from exc
            self._committed += actual_cost

    @property
    def reserved_usd(self) -> Decimal:
        with self._lock:
            return self._committed + sum(self._in_flight.values())


class HTTPTransport(Protocol):
    def post(self, url: str, headers: dict[str, str], body: bytes, timeout: float) -> bytes: ...


class UrllibTransport:
    def post(self, url: str, headers: dict[str, str], body: bytes, timeout: float) -> bytes:
        request = Request(url, data=body, headers=headers, method="POST")
        with urlopen(request, timeout=timeout) as response:
            return response.read()


class GroqKeyRotationTransport:
    """Retry transient transport failures with a bounded rotation of Groq keys.

    Rate-limit responses are returned as errors immediately. Key rotation is not
    used to work around provider quotas.
    """

    def __init__(
        self,
        api_keys: list[str],
        *,
        max_attempts: int = 3,
        backoff_seconds: float = 0.25,
        transport: HTTPTransport | None = None,
    ) -> None:
        keys = list(dict.fromkeys(key.strip() for key in api_keys if key.strip()))
        if not keys:
            raise LiveConfigurationError("at least one Groq API key is required")
        if max_attempts < 1 or backoff_seconds < 0:
            raise ValueError("max_attempts must be positive and backoff_seconds non-negative")
        self.api_keys = keys
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds
        self.transport = transport or UrllibTransport()
        self.last_attempt_count = 0

    def post(self, url: str, headers: dict[str, str], body: bytes, timeout: float) -> bytes:
        self.last_attempt_count = 0
        for attempt in range(self.max_attempts):
            self.last_attempt_count = attempt + 1
            request_headers = dict(headers)
            request_headers["Authorization"] = (
                f"Bearer {self.api_keys[attempt % len(self.api_keys)]}"
            )
            try:
                return self.transport.post(url, request_headers, body, timeout)
            except HTTPError as exc:
                # 429 must remain visible to the caller; rotating here could bypass quotas.
                if exc.code == 429 or exc.code < 500 or attempt + 1 >= self.max_attempts:
                    raise
            except (URLError, TimeoutError, OSError):
                if attempt + 1 >= self.max_attempts:
                    raise
            time.sleep(min(self.backoff_seconds * (2**attempt), 2.0))
        raise AssertionError("unreachable retry state")


class LiveClient:
    """Adapter for an explicitly configured OpenAI-compatible endpoint.

    Token pricing is supplied by the caller and must be based on verified provider
    pricing; there is no bundled or assumed price list.
    """

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        api_key: str | None = None,
        budget: Budget | None = None,
        input_usd_per_million: Decimal,
        output_usd_per_million: Decimal,
        transport: HTTPTransport | None = None,
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

    def complete(self, messages, *, schema=None, tools=None, model=None) -> LLMResponse:
        if not model:
            raise LiveConfigurationError("model must be explicitly selected")
        normalized = [
            {"role": item.role, "content": item.content}
            if isinstance(item, Message)
            else {"role": item["role"], "content": item["content"]}
            for item in messages
        ]
        request_text = json.dumps(
            {"messages": normalized, "tools": list(tools or [])}, ensure_ascii=False
        )
        input_tokens = max(1, len(request_text.encode("utf-8")))
        output_tokens = int(os.getenv("LLM_MAX_COMPLETION_TOKENS", "4096"))
        if output_tokens < 1:
            raise LiveConfigurationError("LLM_MAX_COMPLETION_TOKENS must be positive")
        estimate = (
            Decimal(input_tokens) * self.input_rate + Decimal(output_tokens) * self.output_rate
        ) / Decimal(1_000_000)
        max_attempts = max(1, int(getattr(self.transport, "max_attempts", 1)))
        reservation_id = self.budget.reserve(estimate * max_attempts)
        payload: dict[str, Any] = {
            "model": model,
            "messages": normalized,
            "max_completion_tokens": output_tokens,
        }
        if tools:
            payload["tools"] = list(tools)
        started = time.perf_counter()
        try:
            raw_bytes = self.transport.post(
                f"{self.endpoint}/chat/completions",
                {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json.dumps(payload).encode("utf-8"),
                self.timeout_seconds,
            )
            raw = json.loads(raw_bytes)
            choice = raw["choices"][0]["message"]
            text = choice.get("content") or ""
            usage_raw = raw.get("usage", {})
            if not isinstance(usage_raw, dict):
                raise TypeError("provider usage must be an object")
            usage_reported = "prompt_tokens" in usage_raw and "completion_tokens" in usage_raw
            usage = Usage(
                input_tokens=usage_raw.get("prompt_tokens", 0),
                output_tokens=usage_raw.get("completion_tokens", 0),
            )
            parsed = schema.model_validate_json(text) if schema is not None else None
            calls = tuple(
                ToolCall(
                    id=item["id"],
                    name=item["function"]["name"],
                    arguments=json.loads(item["function"]["arguments"]),
                )
                for item in choice.get("tool_calls", [])
            )
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
            KeyError,
            IndexError,
            TypeError,
            ValidationError,
            ValueError,
        ) as exc:
            # The reservation remains: a failed request may still have reached the provider.
            raise LiveError(f"provider completion failed after budget reservation: {exc}") from exc
        failed_attempts = max(0, int(getattr(self.transport, "last_attempt_count", 1)) - 1)
        actual = estimate * failed_attempts
        if usage_reported:
            actual += (
                Decimal(usage.input_tokens) * self.input_rate
                + Decimal(usage.output_tokens) * self.output_rate
            ) / Decimal(1_000_000)
        else:
            actual += estimate
        self.budget.reconcile(reservation_id, actual)
        if self.budget.reserved_usd > self.budget.maximum_usd:
            raise LiveError(
                "observed provider cost exceeded LAB_MAX_USD; subsequent requests are blocked"
            )
        return LLMResponse(
            text=text,
            parsed=parsed,
            tool_calls=calls,
            usage=usage,
            estimated_cost_usd=actual,
            latency_ms=round((time.perf_counter() - started) * 1000),
            model=raw.get("model", model),
            provider="openai-compatible",
        )
