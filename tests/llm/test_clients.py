import json
from decimal import Decimal
from urllib.error import HTTPError

import pytest
from pydantic import BaseModel

from supportops_foundation.domain import ToolCall
from supportops_foundation.llm import (
    Budget,
    CassetteError,
    CassetteRecorder,
    FakeClient,
    FakeReply,
    GroqKeyRotationTransport,
    LiveClient,
    LiveConfigurationError,
    LiveError,
    Message,
    ReplayClient,
    Usage,
    get_llm,
    load_cassette,
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


def test_factory_defaults_to_fake_and_never_falls_back_from_replay(monkeypatch) -> None:
    monkeypatch.delenv("LLM_MODE", raising=False)
    assert get_llm().complete([Message("user", "x")]).provider == "fake"
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.delenv("LLM_CASSETTE_PATH", raising=False)
    with pytest.raises(CassetteError, match="required"):
        get_llm()


def test_recorder_writes_replayable_jsonl(tmp_path) -> None:
    path = tmp_path / "nested" / "record.jsonl"
    recorder = CassetteRecorder(FakeClient(["captured"]), path)
    recorder.complete([Message("user", "hello")], model="m1")
    replay = ReplayClient(load_cassette(path))
    assert replay.complete([Message("user", "hello")], model="m1").text == "captured"


def test_replay_is_ordered_and_requires_exact_request(tmp_path) -> None:
    path = tmp_path / "calls.jsonl"
    record = {
        "request": {"messages": [{"role": "user", "content": "hello"}], "tools": [], "model": "m1"},
        "response": {
            "text": '{"answer":"world"}',
            "usage": {"input_tokens": 1, "output_tokens": 2},
        },
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    client = ReplayClient(load_cassette(path))
    assert (
        client.complete([Message("user", "hello")], schema=Answer, model="m1").parsed.answer
        == "world"
    )
    with pytest.raises(RuntimeError, match="exhausted"):
        client.complete([Message("user", "hello")], model="m1")


def test_replay_mismatch_does_not_consume_record() -> None:
    record = {
        "request": {"messages": [{"role": "user", "content": "right"}], "tools": [], "model": None},
        "response": {"text": "ok"},
    }
    client = ReplayClient([record])
    with pytest.raises(RuntimeError, match="mismatch"):
        client.complete([Message("user", "wrong")])
    assert client.complete([Message("user", "right")]).text == "ok"


@pytest.mark.parametrize(
    "contents",
    [
        "{broken}\n",
        '{"request": {}}\n',
        '{"request":{"messages":[],"tools":[],"model":null},"response":{}}\n',
    ],
)
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
        endpoint="https://provider.invalid/v1",
        api_key="test-only",
        budget=Budget(Decimal(cap)),
        input_usd_per_million=Decimal(1),
        output_usd_per_million=Decimal(1),
        transport=transport,
    )


def test_live_missing_configuration_and_budget_fail_before_transport(monkeypatch) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(LiveConfigurationError, match="required"):
        LiveClient(input_usd_per_million=Decimal(1), output_usd_per_million=Decimal(1))
    transport = StubTransport(b"{}")
    client = live_client(transport, cap="0.001")
    with pytest.raises(LiveError, match="preflight"):
        client.complete([Message("user", "hello")], model="m1")
    assert transport.calls == []


@pytest.mark.parametrize("raw", [None, "0", "-1", "not-a-number"])
def test_environment_budget_must_be_present_positive_and_decimal(monkeypatch, raw) -> None:
    if raw is None:
        monkeypatch.delenv("LAB_MAX_USD", raising=False)
    else:
        monkeypatch.setenv("LAB_MAX_USD", raw)
    with pytest.raises(LiveConfigurationError, match="LAB_MAX_USD"):
        Budget.from_environment()


def test_live_fake_transport_returns_usage_and_tool_calls_without_network() -> None:
    result = {
        "model": "m1",
        "choices": [
            {
                "message": {
                    "content": "ok",
                    "tool_calls": [
                        {"id": "tc", "function": {"name": "lookup", "arguments": '{"id":"1"}'}}
                    ],
                }
            }
        ],
        "usage": {"prompt_tokens": 2, "completion_tokens": 3},
    }
    transport = StubTransport(json.dumps(result).encode())
    client = live_client(transport)
    response = client.complete([Message("user", "hello")], model="m1")
    assert response.text == "ok"
    assert response.tool_calls[0].name == "lookup"
    assert response.estimated_cost_usd == Decimal("0.000005")
    assert transport.calls[0][0] == "https://provider.invalid/v1/chat/completions"
    assert transport.calls[0][2]["max_completion_tokens"] == 4096


def test_live_budget_accepts_exact_preflight_boundary() -> None:
    transport = StubTransport(
        b'{"choices":[{"message":{"content":"ok"}}],"usage":{"prompt_tokens":1,"completion_tokens":1}}'
    )
    request_bytes = len(
        json.dumps(
            {"messages": [{"role": "user", "content": "hello"}], "tools": []}, ensure_ascii=False
        ).encode()
    )
    cap = Decimal(request_bytes + 4096) / Decimal(1_000_000)
    client = live_client(transport, cap=str(cap))
    client.complete([Message("user", "hello")], model="m1")
    assert client.budget.reserved_usd == Decimal("0.000002")


def test_live_missing_usage_keeps_preflight_reservation() -> None:
    transport = StubTransport(b'{"choices":[{"message":{"content":"ok"}}]}')
    client = live_client(transport)
    client.complete([Message("user", "hello")], model="m1")
    assert client.budget.reserved_usd > 0


def test_live_invalid_usage_shape_fails_without_releasing_reservation() -> None:
    transport = StubTransport(b'{"choices":[{"message":{"content":"ok"}}],"usage":null}')
    client = live_client(transport)
    with pytest.raises(LiveError, match="provider completion failed"):
        client.complete([Message("user", "hello")], model="m1")
    assert client.budget.reserved_usd > 0


def test_live_reconciles_actual_cost_and_blocks_next_request_after_overrun() -> None:
    request = {"messages": [{"role": "user", "content": "hello"}], "tools": []}
    request_bytes = len(json.dumps(request, ensure_ascii=False).encode())
    observed_input_tokens = request_bytes + 100  # Provider framing may exceed local estimate.
    transport = StubTransport(
        json.dumps(
            {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {
                    "prompt_tokens": observed_input_tokens,
                    "completion_tokens": 4096,
                },
            }
        ).encode()
    )
    cap = Decimal(request_bytes + 4096) / Decimal(1_000_000)
    client = live_client(transport, cap=str(cap))
    with pytest.raises(LiveError, match="observed provider cost exceeded"):
        client.complete([Message("user", "hello")], model="m1")
    assert client.budget.reserved_usd == Decimal(observed_input_tokens + 4096) / Decimal(1_000_000)
    with pytest.raises(LiveError, match="preflight"):
        client.complete([Message("user", "hello")], model="m1")
    assert len(transport.calls) == 1


def test_live_schema_parse_failure_is_reported_after_reservation() -> None:
    transport = StubTransport(b'{"choices":[{"message":{"content":"not json"}}]}')
    client = live_client(transport)
    with pytest.raises(LiveError, match="provider completion failed"):
        client.complete([Message("user", "x")], schema=Answer, model="m1")
    assert client.budget.reserved_usd > 0


def test_live_provider_error_keeps_budget_reserved() -> None:
    class Broken:
        def post(self, *args):
            raise TimeoutError("fixture timeout")

    client = live_client(Broken())
    with pytest.raises(LiveError, match="after budget reservation"):
        client.complete([Message("user", "hello")], model="m1")
    assert client.budget.reserved_usd > 0


def test_groq_rotation_retries_timeout_with_next_key_and_bounds_attempts(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MAX_COMPLETION_TOKENS", "10")

    class Flaky:
        def __init__(self):
            self.headers = []

        def post(self, url, headers, body, timeout):
            self.headers.append(headers["Authorization"])
            if len(self.headers) < 2:
                raise TimeoutError("synthetic timeout")
            return b'{"choices":[{"message":{"content":"ok"}}],"usage":{"prompt_tokens":2,"completion_tokens":1}}'

    flaky = Flaky()
    transport = GroqKeyRotationTransport(
        ["key-a", "key-b", "key-c"], max_attempts=3, backoff_seconds=0, transport=flaky
    )
    client = LiveClient(
        endpoint="https://api.groq.com/openai/v1",
        api_key="key-a",
        budget=Budget(Decimal("0.001")),
        input_usd_per_million=Decimal("0.075"),
        output_usd_per_million=Decimal("0.30"),
        transport=transport,
    )
    result = client.complete([Message("user", "synthetic")], model="openai/gpt-oss-20b")
    assert flaky.headers == ["Bearer key-a", "Bearer key-b"]
    assert transport.last_attempt_count == 2
    assert result.text == "ok"
    assert result.estimated_cost_usd > Decimal(0)


def test_groq_rotation_does_not_retry_rate_limit() -> None:
    class RateLimited:
        def __init__(self):
            self.calls = 0

        def post(self, url, headers, body, timeout):
            self.calls += 1
            raise HTTPError(url, 429, "rate limited", {}, None)

    transport = RateLimited()
    rotating = GroqKeyRotationTransport(
        ["key-a", "key-b"], max_attempts=3, backoff_seconds=0, transport=transport
    )
    with pytest.raises(HTTPError) as error:
        rotating.post("https://api.groq.com", {}, b"{}", 1)
    assert error.value.code == 429
    assert transport.calls == 1
    assert rotating.last_attempt_count == 1


def test_groq_rotation_rejects_empty_keys() -> None:
    with pytest.raises(LiveConfigurationError, match="at least one"):
        GroqKeyRotationTransport(["", " "])
