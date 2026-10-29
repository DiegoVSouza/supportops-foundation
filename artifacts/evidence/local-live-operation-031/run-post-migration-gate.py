import json
import os
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
evidence = Path(__file__).resolve().parent
environment = os.environ.copy()
environment["LLM_MODE"] = "fake"
environment["PYTEST_ADDOPTS"] = "--basetemp=artifacts/evidence/funded-candidate-continuation/local-live-operation-031/tmp-post-migration"
command = [sys.executable, "scripts/check_full.py"]
result = subprocess.run(command, cwd=project, env=environment, capture_output=True, text=True, timeout=300)
report = {"command": "uv run --locked python scripts/check_full.py", "cwd": str(project), "mode": "fake", "exit_code": result.returncode, "output": result.stdout + result.stderr}
(evidence / "post-migration-gate.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(report["output"])
sys.exit(result.returncode)
