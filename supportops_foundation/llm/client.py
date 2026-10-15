"""Stable provider-neutral completion types and deterministic clients."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ValidationError

from supportops_foundation.domain import ToolCall


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def __post_init__(self) -> None:
        if self.input_tokens < 0 or self.output_tokens < 0:
            raise ValueError("token usage cannot be negative")


@dataclass(frozen=True)
class LLMResponse:
    text: str
    parsed: Any = None
    tool_calls: tuple[ToolCall, ...] = ()
    usage: Usage = field(default_factory=Usage)
    estimated_cost_usd: Decimal = Decimal(0)
    latency_ms: int = 0
    model: str = "fake"
    provider: str = "fake"

    @property
    def cost_usd(self) -> Decimal:
        """Compatibility name from the frozen P00 brief."""
        return self.estimated_cost_usd

    def __post_init__(self) -> None:
        if self.estimated_cost_usd < 0 or self.latency_ms < 0:
            raise ValueError("cost and latency cannot be negative")


@runtime_checkable
class LLMClient(Protocol):
    def complete(
        self,
        messages: Sequence[Message | Mapping[str, str]],
        *,
        schema: type[BaseModel] | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        model: str | None = None,
    ) -> LLMResponse: ...


@dataclass(frozen=True)
class FakeReply:
    text: str
    tool_calls: tuple[ToolCall, ...] = ()
    usage: Usage = field(default_factory=Usage)
    model: str = "fake-scripted"


class FakeClient:
    """Deterministic scripted client. It has no transport or network capability."""

    def __init__(self, replies: Sequence[FakeReply | str] = ()) -> None:
        self._replies = tuple(
            FakeReply(item) if isinstance(item, str) else item for item in replies
        )
        self.calls: list[tuple[Message, ...]] = []
        self._cursor = 0

    def complete(self, messages, *, schema=None, tools=None, model=None) -> LLMResponse:
        normalized = tuple(
            item if isinstance(item, Message) else Message(item["role"], item["content"])
            for item in messages
        )
        self.calls.append(normalized)
        if self._cursor >= len(self._replies):
            raise RuntimeError("fake response script exhausted")
        reply = self._replies[self._cursor]
        self._cursor += 1
        parsed = None
        if schema is not None:
            try:
                parsed = schema.model_validate_json(reply.text)
            except ValidationError as exc:
                raise ValueError(f"response does not match {schema.__name__}") from exc
        return LLMResponse(
            text=reply.text,
            parsed=parsed,
            tool_calls=reply.tool_calls,
            usage=reply.usage,
            model=model or reply.model,
            provider="fake",
        )


class ReplayClient:
    """Replays exact, ordered request records from a tracked JSONL cassette."""

    def __init__(self, records: Sequence[Mapping[str, Any]]) -> None:
        self._records = tuple(records)
        self._cursor = 0

    def complete(self, messages, *, schema=None, tools=None, model=None) -> LLMResponse:
        normalized = [
            {"role": item.role, "content": item.content}
            if isinstance(item, Message)
            else {"role": item["role"], "content": item["content"]}
            for item in messages
        ]
        if self._cursor >= len(self._records):
            raise RuntimeError("replay cassette exhausted")
        record = self._records[self._cursor]
        expected = record["request"]
        actual = {"messages": normalized, "tools": list(tools or []), "model": model}
        if expected != actual:
            raise RuntimeError(f"replay request mismatch at record {self._cursor + 1}")
        self._cursor += 1
        raw = record["response"]
        parsed = None
        if schema is not None:
            try:
                parsed = schema.model_validate_json(raw["text"])
            except (KeyError, ValidationError) as exc:
                raise ValueError(f"replay response does not match {schema.__name__}") from exc
        usage = raw.get("usage", {})
        return LLMResponse(
            text=raw["text"],
            parsed=parsed,
            tool_calls=tuple(ToolCall.model_validate(item) for item in raw.get("tool_calls", [])),
            usage=Usage(**usage),
            estimated_cost_usd=Decimal(raw.get("estimated_cost_usd", "0")),
            latency_ms=raw.get("latency_ms", 0),
            model=raw.get("model", "replay"),
            provider=raw.get("provider", "replay"),
        )
