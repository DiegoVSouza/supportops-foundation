"""Environment-based client selection with no silent fallback between modes."""

from __future__ import annotations

import json
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal

from .cassette import CassetteError, load_cassette
from .client import FakeClient, ReplayClient
from .live import Budget, LiveClient, LiveConfigurationError

Mode = Literal["fake", "replay", "live"]


def get_llm(mode: Mode | None = None):
    """Create the selected client; missing replay/live configuration fails closed."""
    selected = mode or os.getenv("LLM_MODE", "fake")
    if selected == "fake":
        raw = os.getenv("LLM_FAKE_RESPONSES", '["Deterministic fake response."]')
        try:
            responses = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LiveConfigurationError(
                "LLM_FAKE_RESPONSES must be a JSON array of strings"
            ) from exc
        if not isinstance(responses, list) or not all(isinstance(item, str) for item in responses):
            raise LiveConfigurationError("LLM_FAKE_RESPONSES must be a JSON array of strings")
        return FakeClient(responses)
    if selected == "replay":
        cassette = os.getenv("LLM_CASSETTE_PATH")
        if not cassette:
            raise CassetteError("LLM_CASSETTE_PATH is required in replay mode")
        return ReplayClient(load_cassette(Path(cassette)))
    if selected == "live":
        try:
            input_rate = Decimal(os.environ["LLM_INPUT_USD_PER_MILLION"])
            output_rate = Decimal(os.environ["LLM_OUTPUT_USD_PER_MILLION"])
        except (KeyError, InvalidOperation) as exc:
            raise LiveConfigurationError(
                "verified LLM input/output token rates are required"
            ) from exc
        return LiveClient(
            budget=Budget.from_environment(),
            input_usd_per_million=input_rate,
            output_usd_per_million=output_rate,
        )
    raise LiveConfigurationError(f"unsupported LLM_MODE: {selected}")
