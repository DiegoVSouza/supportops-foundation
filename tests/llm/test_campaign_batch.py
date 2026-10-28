from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.campaign_batch import ResourceCaps, TrialOutcome, TrialReservation, run_chunk
from scripts.campaign_runtime import CampaignLedger


def setup(tmp_path):
    ledger = CampaignLedger(tmp_path / "ledger.sqlite", project="p00", campaign_id="batch")
    options = {
        "cumulative_caps": ResourceCaps(100, 100000, 25600, Decimal(1)),
        "per_trial_caps": ResourceCaps(1, 2048, 256, Decimal("0.01")),
        "account_guard": lambda trial: True,
        "lease_path": tmp_path / "lab.lock",
        "checkpoint_path": tmp_path / "ledger.jsonl",
        "wall_clock_seconds": 60,
        "min_interval_seconds": 0,
    }
    return ledger, options


def trial(number):
    return TrialReservation(f"case-{number}", 1, 400, 200, Decimal("0.01"))


def passed(_):
    return TrialOutcome("passed", 250, 90, Decimal("0.004"))


def test_critical_failure_stops_before_next_dispatch(tmp_path):
    ledger, options = setup(tmp_path)
    calls = []

    def execute(item):
        calls.append(item.case_id)
        return TrialOutcome("failed", 250, 90, Decimal("0.004"), "tool_selection", critical=True)

    result = run_chunk(ledger, [trial(1), trial(2)], execute=execute, **options)
    assert result["reason"] == "critical_failure"
    assert calls == ["case-1"]
    assert ledger.reserved_trials()[0]["event"] == "completed"


def test_chunk_is_bounded_and_resume_skips_failed_trials(tmp_path):
    ledger, options = setup(tmp_path)
    calls = []

    def execute(item):
        calls.append(item.case_id)
        return TrialOutcome("failed", 250, 90, Decimal("0.004"), "classification")

    trials = [trial(n) for n in range(12)]
    first = run_chunk(ledger, trials, execute=execute, **options)
    assert first == {
        "status": "CHUNK_COMPLETE",
        "reason": "chunk_limit",
        "attempted": 10,
        "skipped": 0,
        "remaining": 2,
    }
    reopened = CampaignLedger(ledger.path, project="p00", campaign_id="batch")
    second = run_chunk(reopened, trials, execute=execute, **options)
    assert second["attempted"] == 2 and second["skipped"] == 10
    assert len(calls) == len(set(calls)) == 12
    assert all(row["outcome"] == "failed" for row in reopened.reserved_trials())


def test_checkpoint_precedes_execution_and_interruption_stays_charged(tmp_path):
    ledger, options = setup(tmp_path)
    checkpoint_events = []

    def interrupted(item):
        rows = [json.loads(line) for line in options["checkpoint_path"].read_text().splitlines()]
        checkpoint_events.append((rows[-1]["event"], ledger.totals()["requests"]))
        raise TimeoutError("sensitive provider response must never persist")

    result = run_chunk(ledger, [trial(1), trial(2)], execute=interrupted, **options)
    assert result["reason"] == "uncertain_attempt"
    assert checkpoint_events == [("reserved", 1)]
    assert ledger.totals()["input_tokens"] == 400
    assert ledger.totals()["estimated_cost_usd"] == Decimal("0.01")
    resumed = run_chunk(ledger, [trial(1), trial(2)], execute=passed, **options)
    assert resumed["reason"] == "uncertain_attempt" and resumed["attempted"] == 0
    assert "sensitive" not in options["checkpoint_path"].read_text()


@pytest.mark.parametrize("stop_at", ["execute", "complete"])
def test_process_death_preserves_checkpoint_and_releases_os_lease(tmp_path, stop_at):
    code = """
import os, sys
from decimal import Decimal
from pathlib import Path
from scripts.campaign_batch import ResourceCaps, TrialReservation, TrialOutcome, run_chunk
from scripts.campaign_runtime import CampaignLedger
root = Path(sys.argv[1])
ledger = CampaignLedger(root / 'ledger.sqlite', project='p00', campaign_id='batch')
stop_at = sys.argv[2]
if stop_at == 'complete':
    ledger.complete = lambda **kwargs: os._exit(23)
def execute(_):
    if stop_at == 'execute':
        os._exit(23)
    return TrialOutcome('passed', 250, 90, Decimal('0.004'))
run_chunk(ledger, [TrialReservation('case-1', 1, 400, 200, Decimal('0.01'))],
    cumulative_caps=ResourceCaps(100, 100000, 25600, Decimal('1')),
    per_trial_caps=ResourceCaps(1, 2048, 256, Decimal('0.01')),
    account_guard=lambda _: True, execute=execute,
    lease_path=root / 'lab.lock', checkpoint_path=root / 'ledger.jsonl',
    wall_clock_seconds=60, min_interval_seconds=0)
"""
    process = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path), stop_at],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert process.returncode == 23, process.stderr
    ledger, options = setup(tmp_path)
    result = run_chunk(ledger, [trial(1), trial(2)], execute=passed, **options)
    assert result["reason"] == "uncertain_attempt" and result["attempted"] == 0
    assert ledger.totals()["requests"] == 1
    assert json.loads(options["checkpoint_path"].read_text().splitlines()[0])["event"] == "reserved"


@pytest.mark.parametrize("value", ["PENDING", True, -1, float("inf"), Decimal("NaN")])
def test_invalid_cumulative_caps_never_dispatch(tmp_path, value):
    ledger, options = setup(tmp_path)
    options["cumulative_caps"] = ResourceCaps(value, 1000, 500, Decimal(1))
    with pytest.raises(ValueError):
        run_chunk(ledger, [trial(1)], execute=lambda _: pytest.fail("dispatched"), **options)
    assert ledger.totals()["requests"] == 0


@pytest.mark.parametrize("guard", [lambda _: False, lambda _: "PENDING"])
def test_account_guard_must_explicitly_accept_before_reservation(tmp_path, guard):
    ledger, options = setup(tmp_path)
    options["account_guard"] = guard
    result = run_chunk(ledger, [trial(1)], execute=lambda _: pytest.fail("dispatched"), **options)
    assert result["reason"] == "account_guard_rejected"
    assert ledger.totals()["requests"] == 0


def test_cap_exhaustion_checkpoints_without_dispatching_next_trial(tmp_path):
    ledger, options = setup(tmp_path)
    options["cumulative_caps"] = ResourceCaps(1, 1000, 500, Decimal(1))
    result = run_chunk(ledger, [trial(1), trial(2)], execute=passed, **options)
    assert result["reason"] == "reservation_blocked" and result["attempted"] == 1
    assert len(ledger.reserved_trials()) == 1


def test_pacing_and_wall_clock_stop_without_another_reservation(tmp_path):
    ledger, options = setup(tmp_path)
    now = [0.0]
    calls = []
    options.update(
        wall_clock_seconds=5,
        min_interval_seconds=2,
        clock=lambda: now[0],
        sleep=lambda delay: now.__setitem__(0, now[0] + delay),
    )

    def execute(item):
        calls.append(now[0])
        now[0] += 1
        return passed(item)

    result = run_chunk(ledger, [trial(n) for n in range(5)], execute=execute, **options)
    assert calls == [0, 2, 4]
    assert result["reason"] == "deadline" and result["attempted"] == 3


def test_known_provider_failure_is_recorded_and_not_retried(tmp_path):
    ledger, options = setup(tmp_path)
    result = run_chunk(
        ledger,
        [trial(1), trial(2)],
        execute=lambda _: TrialOutcome("provider_error", None, None, None, "quota"),
        **options,
    )
    assert result["reason"] == "provider_error" and result["attempted"] == 1
    assert ledger.reserved_trials()[0]["event"] == "completed"
    assert ledger.totals()["input_tokens"] == 400


def test_observed_overrun_is_retained_before_stopping(tmp_path):
    ledger, options = setup(tmp_path)
    result = run_chunk(
        ledger,
        [trial(1), trial(2)],
        execute=lambda _: TrialOutcome("passed", 500, 90, Decimal("0.004")),
        **options,
    )
    assert result["reason"] == "accounting_overrun" and result["attempted"] == 1
    assert ledger.totals()["input_tokens"] == 500


@pytest.mark.parametrize(
    "outcome",
    [
        TrialOutcome("passed", -1, 10, None),
        TrialOutcome("passed", 1, 1, Decimal("NaN")),
        {"raw": "never persisted"},
    ],
)
def test_invalid_callback_outcomes_remain_uncertain(tmp_path, outcome):
    ledger, options = setup(tmp_path)
    result = run_chunk(ledger, [trial(1)], execute=lambda _: outcome, **options)
    assert result["reason"] == "uncertain_attempt"
    assert ledger.reserved_trials()[0]["event"] == "reserved"


def test_duplicate_manifest_and_per_trial_overflow_fail_before_dispatch(tmp_path):
    ledger, options = setup(tmp_path)
    for trials in (
        [trial(1), trial(1)],
        [TrialReservation("too-large", 1, 2049, 200, Decimal("0.01"))],
    ):
        with pytest.raises(ValueError):
            run_chunk(ledger, trials, execute=lambda _: pytest.fail("dispatched"), **options)
    assert ledger.totals()["requests"] == 0


@pytest.mark.parametrize("cost", [Decimal("NaN"), Decimal("Infinity"), Decimal(-1), "PENDING"])
def test_nonfinite_or_unknown_money_caps_block_dispatch(tmp_path, cost):
    ledger, options = setup(tmp_path)
    options["cumulative_caps"] = ResourceCaps(100, 100000, 25600, cost)
    with pytest.raises(ValueError):
        run_chunk(ledger, [trial(1)], execute=lambda _: pytest.fail("dispatched"), **options)
    assert ledger.totals()["requests"] == 0


def test_account_guard_failure_cannot_leak_content_or_reserve(tmp_path):
    ledger, options = setup(tmp_path)

    def unavailable(_):
        raise RuntimeError("sensitive account metadata")

    options["account_guard"] = unavailable
    result = run_chunk(ledger, [trial(1)], execute=passed, **options)
    assert result["reason"] == "account_guard_unavailable"
    assert "sensitive" not in json.dumps(result)
    assert ledger.totals()["requests"] == 0


def test_checkpoint_failure_prevents_execution_but_keeps_reservation(tmp_path, monkeypatch):
    ledger, options = setup(tmp_path)

    def full_disk(_):
        raise OSError("disk full")

    monkeypatch.setattr(ledger, "export_jsonl", full_disk)
    with pytest.raises(OSError, match="disk full"):
        run_chunk(ledger, [trial(1)], execute=lambda _: pytest.fail("dispatched"), **options)
    assert ledger.reserved_trials()[0]["event"] == "reserved"
    assert ledger.totals()["requests"] == 1


@pytest.mark.parametrize("max_trials", [0, 11, True])
def test_invalid_chunk_size_is_denied(tmp_path, max_trials):
    ledger, options = setup(tmp_path)
    with pytest.raises(ValueError):
        run_chunk(ledger, [trial(1)], execute=passed, max_trials=max_trials, **options)
    assert ledger.totals()["requests"] == 0


def test_deadline_expiring_during_guard_prevents_reservation(tmp_path):
    ledger, options = setup(tmp_path)
    now = [0]

    def slow_guard(_):
        now[0] = 61
        return True

    options.update(account_guard=slow_guard, clock=lambda: now[0])
    result = run_chunk(ledger, [trial(1)], execute=passed, **options)
    assert result["reason"] == "deadline" and ledger.totals()["requests"] == 0


def test_result_persistence_survives_export_failure_without_reexecution(tmp_path, monkeypatch):
    ledger, options = setup(tmp_path)
    export = ledger.export_jsonl
    exports = []

    def fails_after_completion(path):
        exports.append(path)
        if len(exports) == 2:
            raise OSError("disk full after outcome persistence")
        export(path)

    monkeypatch.setattr(ledger, "export_jsonl", fails_after_completion)
    with pytest.raises(OSError):
        run_chunk(ledger, [trial(1)], execute=passed, **options)
    assert ledger.reserved_trials()[0]["event"] == "completed"
    reopened = CampaignLedger(ledger.path, project="p00", campaign_id="batch")
    result = run_chunk(reopened, [trial(1)], execute=lambda _: pytest.fail("repeated"), **options)
    assert result["skipped"] == 1 and result["attempted"] == 0
