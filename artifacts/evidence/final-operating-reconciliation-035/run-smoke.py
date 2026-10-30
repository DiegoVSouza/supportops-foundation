"""One fresh current-source synthetic operation; persist only sanitized metadata."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project))
from scripts.campaign_execution import fingerprint, require_committed_sources
from scripts.local_live import run_operation

out = Path(__file__).resolve().parent
binding = project / "artifacts/evals/live/local-live-operation-v1/current-035-binding.json"
assert not binding.exists(), "Never overwrite an operational binding or replay this wrapper"
files = fingerprint(project, project.parents[1] / "shared/policies/groq-free-campaign.json")
candidate = require_committed_sources(project, files)
value = {"candidate": candidate, "files_sha256": files,
         "fingerprint": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
         "request_id": "fixture-current-035", "synthetic_only": True, "paid_usd": 0}
binding.parent.mkdir(parents=True, exist_ok=True)
binding.write_text(json.dumps(value, indent=2) + "\n", newline="\n")
# Commit the exact binding before model startup; source files were already frozen.
for command in (["git", "add", "--", str(binding.relative_to(project))],
                ["git", "diff", "--cached", "--check"],
                ["git", "commit", "-m", "docs(p00): freeze final current operational smoke binding"]):
    result = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, "binding commit failed before dispatch"
assert fingerprint(project, project.parents[1] / "shared/policies/groq-free-campaign.json") == files
os.environ["LLM_MODE"] = "live"
try:
    result = run_operation(project, value["request_id"], "Synthetic local smoke: return a short greeting for a support agent. No real account, customer, refund or external action.")
    report = {"status": result.get("status"), "model": result.get("model"), "attempt_id": result.get("attempt_id"),
              "usage": result.get("usage"), "finish_reason": result.get("finish_reason"),
              "candidate": candidate, "fingerprint": value["fingerprint"], "request_id": value["request_id"],
              "raw_response_persisted": False}
    code = 0 if result.get("status") == "ok" else 2
except Exception:
    report = {"status": "INCOMPLETE", "reason": "stopped_without_replay", "request_id": value["request_id"],
              "candidate": candidate, "fingerprint": value["fingerprint"]}
    code = 2
(out / "live-smoke.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps(report))
sys.exit(code)
