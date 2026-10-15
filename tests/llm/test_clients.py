import json
from decimal import Decimal

import pytest
from pydantic import BaseModel

from supportops_foundation.domain import ToolCall
from supportops_foundation.llm import (
    Budget, CassetteError, FakeClient, FakeReply, LiveClient,
    LiveConfigurationError, LiveError, Message, ReplayClient, Usage, load_cassette,
)


class Answer(BaseModel):
    answer: str


def test_fake_script_is_ordered_structured_and_exhausts() -> None:
    call = ToolCall(id="tc-1", name="lookup", arguments={"ticket_id": "t-1"})
    client = FakeClient([FakeReply('{"answer":"ok"}', (call,), Usage(3, 2)), "second"])
    response = client.complete([Message("user", "first")], schema=Answer)
    assert response.parsed == Answer(answer="ok")
    assert response.tool_calls == (call,)
    assert response.usage == Usage(3, 2)
    assert client.complete([{"role": "user", "content": "next"}]).text == "second"
    with pytest.raises(RuntimeError, match="exhausted"):
        client.complete([Message("user", "extra")])
    assert len(client.calls) == 3


def test_fake_schema_parse_failure_is_clear() -> None:
    with pytest.raises(ValueError, match="does not match Answer"):
        FakeClient(["not-json"]).complete([Message("user", "x")], schema=Answer)


def test_replay_is_ordered_and_requires_exact_request(tmp_path) -> None:
    path = tmp_path / "calls.jsonl"
    record = {
        "request": {"messages": [{"role": "user", "content": "hello"}], "tools": [], "model": "m1"},
        "response": {"text": '{"answer":"world"}', "usage": {"input_tokens": 1, "output_tokens": 2}},
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    client = ReplayClient(load_cassette(path))
    assert client.complete([Message("user", "hello")], schema=Answer, model="m1").parsed.answer == "world"
    with pytest.raises(RuntimeError, match="exhausted"):
        client.complete([Message("user", "hello")], model="m1")


def test_replay_mismatch_does_not_consume_record() -> None:
    record = {"request": {"messages": [{"role": "user", "content": "right"}], "tools": [], "model": None}, "response": {"text": "ok"}}
    client = ReplayClient([record])
    with pytest.raises(RuntimeError, match="mismatch"):
        client.complete([Message("user", "wrong")])
    assert client.complete([Message("user", "right")]).text == "ok"


@pytest.mark.parametrize("contents", ["{broken}\n", '{"request": {}}\n'])
def test_malformed_cassette_fails_with_line(contents, tmp_path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(CassetteError, match="line 1"):
        load_cassette(path)


class StubTransport:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.calls = []

    def post(self, url, headers, body, timeout):
        self.calls.append((url, headers, json.loads(body), timeout))
        return self.body


def live_client(transport, cap="0.02"):
    return LiveClient(
        endpoint="https://provider.invalid/v1", api_key="test-only",
        budget=Budget(Decimal(cap)),
        input_usd_per_million=Decimal("1"),
        output_usd_per_million=Decimal("1"), transport=transport,
    )


def test_live_missing_configuration_and_budget_fail_before_transport(monkeypatch) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(LiveConfigurationError, match="required"):
        LiveClient(input_usd_per_million=Decimal("1"), output_usd_per_million=Decimal("1"))
    transport = StubTransport(b"{}")
    client = live_client(transport, cap="0.001")
    with pytest.raises(LiveError, match="preflight"):
        client.complete([Message("user", "hello")], model="m1")
    assert transport.calls == []


def test_live_fake_transport_returns_usage_and_tool_calls_without_network() -> None:
    result = {
        "model": "m1", "choices": [{"message": {
            "content": "ok", "tool_calls": [{"id": "tc", "function": {"name": "lookup", "arguments": "{\"id\":\"1\"}"}}],
        }}], "usage": {"prompt_tokens": 2, "completion_tokens": 3},
    }
    transport = StubTransport(json.dumps(result).encode())
    client = live_client(transport)
    response = client.complete([Message("user", "hello")], model="m1")
    assert response.text == "ok"
    assert response.tool_calls[0].name == "lookup"
    assert response.estimated_cost_usd == Decimal("0.000005")
    assert transport.calls[0][0] == "https://provider.invalid/v1/chat/completions"
    assert transport.calls[0][2]["max_completion_tokens"] == 4096


def test_live_provider_error_keeps_budget_reserved() -> None:
    class Broken:
        def post(self, *args):
            raise TimeoutError("fixture timeout")

    client = live_client(Broken())
    with pytest.raises(LiveError, match="after budget reservation"):
        client.complete([Message("user", "hello")], model="m1")
    assert client.budget.reserved_usd > 0
