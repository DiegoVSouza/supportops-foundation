import json
import os
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
evidence = Path(__file__).resolve().parent
environment = os.environ.copy()
environment["LLM_MODE"] = "fake"
commands = [
    [sys.executable, "scripts/run_live_campaign.py", "--stage", "development", "--dry-run"],
    [sys.executable, "-m", "pytest", "-q", "tests/test_live_campaign_preparation.py", "--basetemp=artifacts/evidence/funded-candidate-continuation/local-live-operation-031/tmp-reconciliation"],
]
reports = []
for command in commands:
    result = subprocess.run(command, cwd=project, env=environment, capture_output=True, text=True, timeout=180)
    reports.append({"command": " ".join(command), "cwd": str(project), "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    print(command[1], "exit", result.returncode)
(evidence / "post-smoke-reconciliation.json").write_text(json.dumps(reports, indent=2) + "\n", newline="\n")
sys.exit(any(report["exit_code"] for report in reports))
