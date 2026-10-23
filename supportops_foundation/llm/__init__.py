"""Provider-neutral LLM contracts with explicit fake, replay, and live modes."""

from .cassette import CassetteError, CassetteRecorder, load_cassette
from .client import FakeClient, FakeReply, LLMClient, LLMResponse, Message, ReplayClient, Usage
from .factory import get_llm
from .live import (
    Budget,
    GroqKeyRotationTransport,
    HTTPTransport,
    LiveClient,
    LiveConfigurationError,
    LiveError,
)

FakeLLM = FakeClient
ReplayLLM = ReplayClient
LiveLLM = LiveClient

__all__ = [
    "Budget",
    "CassetteError",
    "CassetteRecorder",
    "FakeClient",
    "FakeLLM",
    "FakeReply",
    "GroqKeyRotationTransport",
    "HTTPTransport",
    "LLMClient",
    "LLMResponse",
    "LiveClient",
    "LiveConfigurationError",
    "LiveError",
    "LiveLLM",
    "Message",
    "ReplayClient",
    "ReplayLLM",
    "Usage",
    "get_llm",
    "load_cassette",
]
