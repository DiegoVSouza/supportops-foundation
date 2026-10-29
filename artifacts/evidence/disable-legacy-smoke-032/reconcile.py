import json
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
command = [sys.executable, "scripts/run_live_campaign.py", "--stage", "development", "--dry-run"]
result = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=60)
payload = json.loads(result.stdout) if result.returncode == 0 else {}
candidate = payload.get("candidate", {})
report = {"command": " ".join(command), "cwd": str(project), "exit_code": result.returncode, "fingerprint": candidate.get("candidate_fingerprint_sha256"), "commit": candidate.get("candidate_commit"), "p00_operation_allocation": candidate.get("p00_operation_allocation"), "p00_confirmation_protected": candidate.get("p00_confirmation_protected"), "provider_ledger_usage": candidate.get("provider_ledger_usage"), "provider_accessed": payload.get("provider_accessed"), "credentials_read": payload.get("credentials_read")}
(Path(__file__).resolve().parent / "reconciliation.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps(report, indent=2))
sys.exit(result.returncode)
