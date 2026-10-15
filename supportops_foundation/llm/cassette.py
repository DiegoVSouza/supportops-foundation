"""Strict JSONL cassette parsing for deterministic, ordered replay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CassetteError(ValueError):
    pass


def load_cassette(path: str | Path) -> list[dict[str, Any]]:
    records = []
    try:
        with Path(path).open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise CassetteError(f"invalid JSON at line {line_number}") from exc
                if not isinstance(record, dict) or not isinstance(record.get("request"), dict) or not isinstance(record.get("response"), dict):
                    raise CassetteError(f"line {line_number} must contain request and response objects")
                records.append(record)
    except OSError as exc:
        raise CassetteError(f"cannot read cassette: {path}") from exc
    return records
