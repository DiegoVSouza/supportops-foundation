"""Read-only reconciliation; never initialize a provider or change a campaign."""
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

project = Path(__file__).resolve().parents[4]
live = project / "artifacts/evals/live"
report = {"provider_accessed": False, "credentials_read": False, "campaigns": {}}
with closing(sqlite3.connect((live / "provider-usage.sqlite").as_uri() + "?mode=ro", uri=True)) as db:
    db.row_factory = sqlite3.Row
    provider = [dict(row) for row in db.execute("SELECT * FROM usage_events ORDER BY sequence")]
with closing(sqlite3.connect((live / "ledger.sqlite").as_uri() + "?mode=ro", uri=True)) as db:
    db.row_factory = sqlite3.Row
    logical = [dict(row) for row in db.execute("SELECT * FROM events ORDER BY sequence")]
for directory in sorted(live.iterdir()):
    manifest_path, trials_path = directory / "manifest.json", directory / "trials.jsonl"
    if not manifest_path.is_file():
        continue
    manifest = json.loads(manifest_path.read_text())
    trials = [json.loads(line) for line in trials_path.read_text().splitlines()] if trials_path.exists() else []
    receipts = []
    for trial in trials:
        matched = [r for r in provider if r["attempt_id"] == trial.get("provider_attempt_id") and r["event"] == "completed"]
        assert len(matched) == 1, "missing or duplicate receipt"
        receipt = matched[0]
        assert (receipt["campaign"], receipt["case_id"], receipt["trial"], receipt["call_index"]) == (directory.name, trial["case_id"], trial["trial"], 1)
        if trial["model_evaluated"]:
            assert trial["usage"] == {"input_tokens": receipt["actual_input"], "output_tokens": receipt["actual_output"]}
        matched_logical = [r for r in logical if r["campaign_id"] == directory.name and r["case_id"] == trial["case_id"] and r["trial"] == trial["trial"] and r["event"] == "completed"]
        assert len(matched_logical) == 1
        assert matched_logical[0]["outcome"] == trial["outcome"]
        receipts.append(receipt["attempt_id"])
    report["campaigns"][directory.name] = {
        "candidate_commit": manifest.get("candidate_commit"),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "trials_sha256": hashlib.sha256(trials_path.read_bytes()).hexdigest() if trials_path.exists() else None,
        "recorded": len(trials), "passes": sum(t["passed"] for t in trials),
        "critical": sum(t.get("critical_failure", False) for t in trials),
        "matched_receipts": len(receipts),
    }
report["reservation_count"] = sum(r["event"] == "reserved" for r in provider)
report["completed_count"] = sum(r["event"] == "completed" for r in provider)
report["reserved_slot_attribution_count"] = sum("credential_slot" in json.loads(r["feedback"] or "{}") for r in provider if r["event"] == "reserved")
print(json.dumps(report, indent=2, sort_keys=True))
