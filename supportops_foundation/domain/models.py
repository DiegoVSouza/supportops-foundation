"""Pydantic v2 domain contracts. These field names are frozen by ADR-001."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class TicketCategory(StrEnum):
    BILLING = "billing"
    ACCOUNT_ACCESS = "account_access"
    TECHNICAL = "technical"
    SHIPPING = "shipping"
    OTHER = "other"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Action(StrEnum):
    ANSWER = "answer"
    REQUEST_INFO = "request_info"
    REFUND = "refund"
    ESCALATE = "escalate"


class Customer(ContractModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    tier: Literal["standard", "plus", "enterprise"] = "standard"


class Ticket(ContractModel):
    id: str = Field(min_length=1, max_length=64)
    customer_id: str = Field(min_length=1, max_length=64)
    subject: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=1, max_length=20_000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    category: TicketCategory | None = None
    priority: Priority = Priority.NORMAL
    status: Literal["open", "pending", "resolved", "closed"] = "open"

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include a timezone")
        return value


class Invoice(ContractModel):
    id: str = Field(min_length=1, max_length=64)
    customer_id: str = Field(min_length=1, max_length=64)
    amount: Decimal = Field(gt=Decimal("0"), max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    status: Literal["open", "paid", "overdue", "refunded"] = "open"
    due_at: datetime


class KBArticle(ContractModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=1, max_length=20_000)
    category: TicketCategory
    updated_at: datetime


class ToolCall(ContractModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(ContractModel):
    call_id: str = Field(min_length=1, max_length=128)
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def error_matches_result(self) -> Self:
        if self.ok and self.error is not None:
            raise ValueError("successful tool results cannot contain an error")
        if not self.ok and not self.error:
            raise ValueError("failed tool results must contain an error")
        return self


class AgentRun(ContractModel):
    id: str = Field(min_length=1, max_length=64)
    ticket_id: str = Field(min_length=1, max_length=64)
    status: Literal["running", "completed", "failed", "escalated"] = "running"
    started_at: datetime
    finished_at: datetime | None = None
    step_count: int = Field(default=0, ge=0)


class TriageDecision(ContractModel):
    category: TicketCategory
    priority: Priority
    action: Action
    escalate: bool
    rationale: str = Field(min_length=1, max_length=2_000)

    @field_validator("escalate")
    @classmethod
    def action_requires_escalation(cls, value: bool, info: Any) -> bool:
        if info.data.get("action") == Action.ESCALATE and value is not True:
            raise ValueError("escalate action must set escalate=true")
        return value
