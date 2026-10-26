"""Single-attempt P00 chunk control; provider and account integration remain external."""

from __future__ import annotations

import math
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from scripts.campaign_runtime import CampaignBlocked, CampaignLease, CampaignLedger

ERROR_CLASSES = frozenset(
    [
        "configuration",
        "credential",
        "model_access",
        "rate_limit",
        "quota",
        "transport",
        "request_schema",
        "output_truncated",
        "output_schema",
        "classification",
        "routing",
        "tool_selection",
        "missing_evidence",
        "grounding",
        "citation",
        "abstention",
        "injection",
        "tenant_scope",
        "authorization_expired",
        "duplicate_effect",
        "crash_recovery",
        "telemetry_export",
        "accounting",
        "grader_error",
    ]
)


def _integer(value: object, *, minimum: int = 0) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError("resource count must be a bounded nonnegative integer")


def _money(value: object) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
        raise ValueError("estimated cost must be a finite nonnegative Decimal")


@dataclass(frozen=True)
class ResourceCaps:
    requests: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal

    def validate(self) -> None:
        for value in (self.requests, self.input_tokens, self.output_tokens):
            _integer(value)
        _money(self.estimated_cost_usd)


@dataclass(frozen=True)
class TrialReservation:
    case_id: str
    trial: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal

    def validate(self, caps: ResourceCaps) -> None:
        if not isinstance(self.case_id, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", self.case_id
        ):
            raise ValueError("invalid synthetic case ID")
        _integer(self.trial, minimum=1)
        if self.trial > 3:
            raise ValueError("P00 supports at most three trials per case")
        _integer(self.input_tokens, minimum=1)
        _integer(self.output_tokens, minimum=1)
        _money(self.estimated_cost_usd)
        if (
            self.input_tokens > caps.input_tokens
            or self.output_tokens > caps.output_tokens
            or self.estimated_cost_usd > caps.estimated_cost_usd
        ):
            raise ValueError("trial exceeds its approved reservation ceiling")


@dataclass(frozen=True)
class TrialOutcome:
    outcome: str
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: Decimal | None
    error_class: str | None = None

    def validate(self) -> None:
        if self.outcome not in {"passed", "failed", "provider_error"}:
            raise ValueError("invalid sanitized outcome")
        if (self.outcome == "passed" and self.error_class is not None) or (
            self.outcome != "passed" and self.error_class not in ERROR_CLASSES
        ):
            raise ValueError("invalid sanitized error class")
        for count in (self.input_tokens, self.output_tokens):
            if count is not None:
                _integer(count)
        if self.estimated_cost_usd is not None:
            _money(self.estimated_cost_usd)


def run_chunk(
    ledger: CampaignLedger,
    trials: Sequence[TrialReservation],
    *,
    cumulative_caps: ResourceCaps,
    per_trial_caps: ResourceCaps,
    execute: Callable[[TrialReservation], TrialOutcome],
    account_guard: Callable[[TrialReservation], bool],
    lease_path: Path,
    checkpoint_path: Path,
    wall_clock_seconds: float,
    min_interval_seconds: float,
    max_trials: int = 10,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, str | int]:
    """Run one bounded chunk under a caller-configured lab lease.

    ``execute`` must enforce its own finite request timeout and perform exactly
    one provider attempt, returning only sanitized usage and grading metadata.
    ``account_guard`` must reconcile all project ledgers under this same lease
    and explicitly approve before each reservation. This module supplies neither
    provider access nor approval; the public campaign CLI remains disabled.
    """
    cumulative_caps.validate()
    per_trial_caps.validate()
    _integer(max_trials, minimum=1)
    if max_trials > 10 or per_trial_caps.requests != 1:
        raise ValueError("P00 chunks allow at most ten single-attempt trials")
    for value, minimum in ((wall_clock_seconds, 0), (min_interval_seconds, -1)):
        if type(value) not in (int, float) or not math.isfinite(value) or value <= minimum:
            raise ValueError("finite positive wall clock and nonnegative pacing required")
    if min_interval_seconds < 0:
        raise ValueError("pacing cannot be negative")
    paths = [path.resolve() for path in (ledger.path, lease_path, checkpoint_path)]
    if len(set(paths)) != 3:
        raise ValueError("ledger, lease and checkpoint must use distinct files")
    manifest = tuple(trials)
    for item in manifest:
        item.validate(per_trial_caps)
    keys = {(item.case_id, item.trial) for item in manifest}
    if len(keys) != len(manifest):
        raise ValueError("duplicate manifest trial")
    attempted = 0
    completed: set[tuple[str, int]] = set()
    skipped = 0

    def result(reason: str, *, finished: bool = False) -> dict[str, str | int]:
        return {
            "status": "CHUNK_COMPLETE" if finished else "INCOMPLETE",
            "reason": reason,
            "attempted": attempted,
            "skipped": skipped,
            "remaining": len(keys - completed),
        }

    with CampaignLease(lease_path, ledger.campaign_id):
        recorded = ledger.reserved_trials()
        completed = {
            (row["case_id"], row["trial"]) for row in recorded if row["event"] == "completed"
        }
        skipped = len(keys & completed)
        if any(row["event"] == "reserved" for row in recorded):
            return result("uncertain_attempt")
        deadline = clock() + wall_clock_seconds
        last_started: float | None = None
        for item in manifest:
            if (item.case_id, item.trial) in completed:
                continue
            if attempted == max_trials:
                return result("chunk_limit", finished=True)
            now = clock()
            wait = (
                max(0.0, last_started + min_interval_seconds - now)
                if last_started is not None
                else 0.0
            )
            if now + wait >= deadline:
                return result("deadline")
            if wait:
                sleep(wait)
            if clock() >= deadline:
                return result("deadline")
            try:
                approved = account_guard(item)
            except Exception:  # noqa: BLE001 - Guard failures must deny without exposing content.
                return result("account_guard_unavailable")
            if approved is not True:
                return result("account_guard_rejected")
            if clock() >= deadline:
                return result("deadline")
            try:
                ledger.reserve(
                    case_id=item.case_id,
                    trial=item.trial,
                    input_tokens=item.input_tokens,
                    output_tokens=item.output_tokens,
                    estimated_cost_usd=item.estimated_cost_usd,
                    caps=vars(cumulative_caps),
                )
            except CampaignBlocked:
                return result("reservation_blocked")
            ledger.export_jsonl(checkpoint_path)
            last_started = clock()
            if last_started >= deadline:
                return result("uncertain_attempt")
            attempted += 1
            try:
                observation = execute(item)
                if not isinstance(observation, TrialOutcome):
                    raise TypeError("invalid sanitized outcome")
                observation.validate()
            except Exception:  # noqa: BLE001 - Any adapter/grader failure leaves uncertain usage.
                # A response or usage may exist; preserve the full reservation.
                return result("uncertain_attempt")
            ledger.complete(
                case_id=item.case_id,
                trial=item.trial,
                actual_input_tokens=observation.input_tokens,
                actual_output_tokens=observation.output_tokens,
                actual_cost_usd=observation.estimated_cost_usd,
                outcome=observation.outcome,
                error_class=observation.error_class,
            )
            completed.add((item.case_id, item.trial))
            ledger.export_jsonl(checkpoint_path)
            if any(
                actual is not None and actual > reserved
                for actual, reserved in (
                    (observation.input_tokens, item.input_tokens),
                    (observation.output_tokens, item.output_tokens),
                    (observation.estimated_cost_usd, item.estimated_cost_usd),
                )
            ):
                return result("accounting_overrun")
            if observation.outcome == "provider_error":
                return result("provider_error")
        return result("manifest_exhausted", finished=True)
