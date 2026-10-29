"""Provider-free current-source allocation reconciliation, without storing content."""
import json
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
command = [sys.executable, "-m", "scripts.run_live_campaign", "--stage", "development", "--dry-run"]
result = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=60)
payload = json.loads(result.stdout) if result.returncode == 0 else {}
candidate = payload.get("candidate", {})
report = {"command": command, "cwd": str(project), "exit_code": result.returncode,
          "fingerprint": candidate.get("candidate_fingerprint_sha256"), "commit": candidate.get("candidate_commit"),
          "p00_operation": candidate.get("p00_operation_allocation"), "p01_operation": candidate.get("p01_operation_allocation"),
          "other_operations": candidate.get("other_operation_allocations"),
          "p00_confirmation": candidate.get("p00_confirmation_protected"),
          "global_remaining": candidate.get("global_remaining"),
          "p00_primary": candidate.get("remaining_capacity_by_project", {}).get("p00"),
          "provider_accessed": payload.get("provider_accessed"), "credentials_read": payload.get("credentials_read"),
          "output": result.stdout + result.stderr if result.returncode else "sanitized report only"}
(Path(__file__).resolve().parent / "reconciliation.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps(report, indent=2))
sys.exit(result.returncode)
