import json
import os
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
environment = os.environ.copy()
environment["LLM_MODE"] = "live"
command = [sys.executable, "-m", "scripts.local_live", "--request-id", "local-smoke-20261028-01", "--synthetic-text", "Synthetic support ticket: where can I see my invoice status?"]
result = subprocess.run(command, cwd=project, env=environment, capture_output=True, text=True, timeout=90)
try:
    payload = json.loads(result.stdout)
    safe = {key: payload[key] for key in ("status", "reason", "model") if key in payload and isinstance(payload[key], str)}
except (ValueError, TypeError):
    safe = {"status": "INCOMPLETE", "reason": "unparseable_or_missing_output"}
report = {"command": "LLM_MODE=live python -m scripts.local_live --request-id local-smoke-20261028-01 --synthetic-text <synthetic ticket>", "cwd": str(project), "exit_code": result.returncode, "result": safe, "stdout_redacted": True, "stderr_redacted": True}
(Path(__file__).resolve().parent / "live-smoke-01.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps(report, indent=2))
sys.exit(result.returncode)
