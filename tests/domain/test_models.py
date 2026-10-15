from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from supportops_foundation.domain import (
    Action,
    Customer,
    Invoice,
    Priority,
    Ticket,
    TicketCategory,
    ToolResult,
    TriageDecision,
)


def test_customer_rejects_empty_identity_and_unknown_fields():
    with pytest.raises(ValidationError):
        Customer(id="", name="Name", email="x@y.test")
    with pytest.raises(ValidationError):
        Customer(id="c1", name="Name", email="x@y.test", private_note="unexpected")


def test_ticket_requires_timezone_and_preserves_public_enum_values():
    with pytest.raises(ValidationError, match="timezone"):
        Ticket(id="t1", customer_id="c1", subject="Help", body="Question", created_at=datetime(2026, 1, 1))
    ticket = Ticket(id="t1", customer_id="c1", subject="Help", body="Question", category="billing")
    assert ticket.category is TicketCategory.BILLING
    assert ticket.priority is Priority.NORMAL


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-0.01")])
def test_invoice_rejects_non_positive_amount(amount):
    with pytest.raises(ValidationError):
        Invoice(id="i1", customer_id="c1", amount=amount, due_at="2026-01-01T00:00:00Z")


def test_tool_result_requires_error_only_for_failure():
    assert ToolResult(call_id="c1", ok=True, data={}).ok
    with pytest.raises(ValidationError):
        ToolResult(call_id="c1", ok=False)
    with pytest.raises(ValidationError):
        ToolResult(call_id="c1", ok=True, error="contradiction")


def test_escalate_action_requires_escalation_flag():
    decision = TriageDecision(category="billing", priority="high", action="escalate", escalate=True, rationale="Policy review.")
    assert decision.action is Action.ESCALATE
    with pytest.raises(ValidationError):
        TriageDecision(category="billing", priority="high", action="escalate", escalate=False, rationale="Bad contract.")
