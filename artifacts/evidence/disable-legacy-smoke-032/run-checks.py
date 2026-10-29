import json
import os
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
env = os.environ.copy()
env["LLM_MODE"] = "fake"
command = [sys.executable, "scripts/check_full.py"]
result = subprocess.run(command, cwd=project, env=env, capture_output=True, text=True, timeout=300)
report = {"command": "uv run --locked python scripts/check_full.py", "cwd": str(project), "exit_code": result.returncode, "output": result.stdout + result.stderr}
(Path(__file__).resolve().parent / "full-attempt3.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print("full gate exit", result.returncode)
sys.exit(result.returncode)
