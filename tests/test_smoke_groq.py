"""Offline contract tests for the opt-in Groq smoke script."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.smoke_groq import GroqSDKTransport, collect_keys, list_models_for_valid_keys


def test_credential_selection_uses_only_numbered_keys(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "legacy-extra")
    for index, value in enumerate(("key-one", "key-two", "key-three", "key-four"), 1):
        monkeypatch.setenv(f"GROQ_API_KEY_{index}", value)
    assert collect_keys() == ["key-one", "key-two", "key-three", "key-four"]


def test_sdk_transport_adapts_structured_completion_without_logging_key(monkeypatch):
    captured = {}

    class Completion:
        @property
        def choices(self):
            return [SimpleNamespace(message=SimpleNamespace(content="{}"))]

        def model_dump_json(self):
            return json.dumps(
                {
                    "model": "openai/gpt-oss-20b",
                    "choices": [{"message": {"content": "{}", "tool_calls": None}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 2},
                }
            )

    class SDK:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    captured.update(kwargs)
                    return Completion()

        def __init__(self, **kwargs):
            captured["client_config"] = kwargs

    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=SDK, GroqError=Exception))
    raw = GroqSDKTransport().post(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Authorization": "Bearer dummy-test-key"},
        b'{"model":"openai/gpt-oss-20b","messages":[]}',
        2,
    )
    result = json.loads(raw)
    assert result["usage"]["completion_tokens"] == 2
    assert result["choices"][0]["message"]["tool_calls"] == []
    assert captured["model"] == "openai/gpt-oss-20b"
    assert captured["client_config"]["max_retries"] == 0


def test_model_preflight_uses_sdk_catalog_without_generation(monkeypatch):
    class SDK:
        def __init__(self, **_kwargs):
            self.models = SimpleNamespace(
                list=lambda: SimpleNamespace(data=[SimpleNamespace(id="openai/gpt-oss-20b")])
            )

    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=SDK, GroqError=Exception))
    valid, models = list_models_for_valid_keys(["dummy-a", "dummy-b"])
    assert valid == ["dummy-a", "dummy-b"]
    assert "openai/gpt-oss-20b" in models


def test_sdk_transport_preserves_retryable_http_status(monkeypatch):
    class SDK:
        def __init__(self, **_kwargs):
            pass

        class chat:
            class completions:
                @staticmethod
                def create(**_kwargs):
                    error = RuntimeError("fixture")
                    error.status_code = 429
                    error.response = SimpleNamespace(headers={"retry-after": "1"})
                    raise error

    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=SDK, GroqError=Exception))
    try:
        GroqSDKTransport().post(
            "https://api.groq.com/chat/completions", {"Authorization": "Bearer dummy"}, b"{}", 1
        )
    except HTTPError as exc:
        assert exc.code == 429
        assert exc.headers["retry-after"] == "1"
    else:
        raise AssertionError("HTTP status was not propagated")


def test_legacy_smoke_refuses_before_credentials_and_provider(monkeypatch):
    from scripts import smoke_groq

    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected external access")

    monkeypatch.setattr(smoke_groq, "load_root_env", forbidden)
    monkeypatch.setattr(smoke_groq, "list_models_for_valid_keys", forbidden)
    monkeypatch.setattr(smoke_groq, "write_evidence", forbidden)
    assert smoke_groq.main() == 2
