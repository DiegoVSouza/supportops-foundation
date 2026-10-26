from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from threading import Barrier

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from scripts.campaign_runtime import CampaignBlocked, CampaignLease, CampaignLedger

CAPS = {
    "requests": 2,
    "input_tokens": 1000,
    "output_tokens": 500,
    "estimated_cost_usd": Decimal("0.02"),
}


def ledger(tmp_path):
    return CampaignLedger(tmp_path / "ledger.sqlite", project="p00", campaign_id="campaign-test")


def reserve(target, *, case_id="case-1", trial=1, cost=Decimal("0.01")):
    target.reserve(
        case_id=case_id,
        trial=trial,
        input_tokens=400,
        output_tokens=200,
        estimated_cost_usd=cost,
        caps=CAPS,
    )


def test_reservation_is_durable_and_uncertain_trials_are_never_repeated(tmp_path):
    target = ledger(tmp_path)
    reserve(target)

    recovered = ledger(tmp_path)
    assert recovered.totals() == {
        "requests": 1,
        "input_tokens": 400,
        "output_tokens": 200,
        "estimated_cost_usd": Decimal("0.01"),
    }
    with pytest.raises(CampaignBlocked, match="will not be rerun"):
        reserve(recovered)
    assert recovered.reserved_trials() == [
        {
            "case_id": "case-1",
            "trial": 1,
            "event": "reserved",
            "outcome": None,
            "error_class": None,
        }
    ]


def test_completion_reconciles_usage_without_deleting_reservation(tmp_path):
    target = ledger(tmp_path)
    reserve(target)
    target.complete(
        case_id="case-1",
        trial=1,
        actual_input_tokens=250,
        actual_output_tokens=90,
        actual_cost_usd=Decimal("0.004"),
        outcome="failed",
        error_class="output_schema",
    )

    assert target.totals() == {
        "requests": 1,
        "input_tokens": 250,
        "output_tokens": 90,
        "estimated_cost_usd": Decimal("0.004"),
    }
    with pytest.raises(CampaignBlocked, match="will not be rerun"):
        reserve(target)


def test_missing_usage_keeps_the_full_reservation_and_exports_no_prompt(tmp_path):
    target = ledger(tmp_path)
    reserve(target)
    target.complete(
        case_id="case-1",
        trial=1,
        actual_input_tokens=None,
        actual_output_tokens=None,
        actual_cost_usd=None,
        outcome="provider_error",
        error_class="Timeout",
    )
    export = tmp_path / "ledger.jsonl"
    target.export_jsonl(export)

    assert target.totals()["input_tokens"] == 400
    assert target.totals()["output_tokens"] == 200
    assert target.totals()["estimated_cost_usd"] == Decimal("0.01")
    assert "prompt" not in export.read_text(encoding="utf-8").lower()
    assert "Timeout" in export.read_text(encoding="utf-8")


def test_cumulative_caps_block_before_appending_another_reservation(tmp_path):
    target = ledger(tmp_path)
    reserve(target, case_id="case-1")
    caps = {**CAPS, "requests": 1}
    with pytest.raises(CampaignBlocked, match="cap would be exceeded"):
        target.reserve(
            case_id="case-2",
            trial=1,
            input_tokens=400,
            output_tokens=200,
            estimated_cost_usd=Decimal("0.01"),
            caps=caps,
        )
    assert target.totals()["requests"] == 1


def test_concurrent_reservations_cannot_race_past_a_cumulative_cap(tmp_path):
    first = ledger(tmp_path)
    second = ledger(tmp_path)
    barrier = Barrier(2)
    caps = {**CAPS, "requests": 1}

    def attempt(target, case_id):
        barrier.wait()
        try:
            target.reserve(
                case_id=case_id,
                trial=1,
                input_tokens=400,
                output_tokens=200,
                estimated_cost_usd=Decimal("0.01"),
                caps=caps,
            )
            return "reserved"
        except CampaignBlocked:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(lambda pair: attempt(*pair), [(first, "case-a"), (second, "case-b")])
        )
    assert sorted(results) == ["blocked", "reserved"]
    assert first.totals()["requests"] == 1


def test_cumulative_accounting_does_not_reset_for_a_new_campaign_id(tmp_path):
    path = tmp_path / "p00-account-ledger.sqlite"
    first = CampaignLedger(path, project="p00", campaign_id="campaign-one")
    second = CampaignLedger(path, project="p00", campaign_id="campaign-two")
    reserve(first, case_id="case-one")

    with pytest.raises(CampaignBlocked, match="cap would be exceeded"):
        second.reserve(
            case_id="case-two",
            trial=1,
            input_tokens=400,
            output_tokens=200,
            estimated_cost_usd=Decimal("0.01"),
            caps={**CAPS, "requests": 1},
        )
    assert second.totals()["requests"] == 1


def test_ledger_rejects_mutation_and_deletion(tmp_path):
    target = ledger(tmp_path)
    reserve(target)
    import sqlite3

    with sqlite3.connect(target.path) as db, pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE events SET outcome='passed'")
    with sqlite3.connect(target.path) as db, pytest.raises(sqlite3.IntegrityError):
        db.execute("DELETE FROM events")


def test_machine_lease_blocks_an_independent_launcher_and_releases(tmp_path):
    lock_path = tmp_path / "lab-wide.lock"
    with CampaignLease(lock_path, "first"):
        code = """
from pathlib import Path
from scripts.campaign_runtime import CampaignLease, CampaignBlocked
import sys
try:
    CampaignLease(Path(sys.argv[1]), 'second').acquire()
except CampaignBlocked:
    print('blocked')
else:
    raise SystemExit(3)
"""
        result = subprocess.run(
            [sys.executable, "-c", code, str(lock_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "blocked"
    metadata = json.loads(lock_path.read_text(encoding="utf-8"))
    assert metadata["campaign_id"] == "first"
    assert set(metadata) == {"pid", "host", "campaign_id", "acquired_at_utc"}

    with CampaignLease(lock_path, "after-release"):
        pass
    metadata = json.loads(lock_path.read_text(encoding="utf-8"))
    assert metadata["campaign_id"] == "after-release"
