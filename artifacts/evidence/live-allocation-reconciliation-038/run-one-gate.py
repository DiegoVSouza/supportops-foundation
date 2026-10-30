"""Consume exactly the explicitly authorized additional P00 fake gate."""
import json
import os
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
if (OUT / "additional-gate-attempt.json").exists():
    raise SystemExit("additional gate already consumed; replay prohibited")
PROJECT = OUT.parents[2]
WORK = OUT / "snapshot-attempt2/lab/projects/p00"
COMMAND = ["uv", "run", "--locked", "--no-sync", "--active", "python", "scripts/check_full.py"]
env = dict(os.environ, LLM_MODE="fake", VIRTUAL_ENV=str(PROJECT / ".venv"),
           PYTHONPATH=str(WORK), PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
env["P00_PYTEST_BASETEMP"] = "artifacts/evidence/funded-candidate-continuation/exception-038/pytest"
(WORK / env["P00_PYTEST_BASETEMP"]).parent.mkdir(parents=True, exist_ok=True)
for key in list(env):
    if key == "GROQ_API_KEY" or key.startswith("GROQ_API_KEY_"):
        del env[key]
with (OUT / "additional-gate-attempt.json").open("x", encoding="utf-8") as stream:
    json.dump({"historical_attempts": "3/3", "additional_attempt": "1/1",
               "state": "CONSUMED", "command": COMMAND, "cwd": str(WORK)}, stream)
record = {"command": COMMAND, "cwd": str(WORK), "provider_accessed": False}
try:
    result = subprocess.run(COMMAND, cwd=WORK, env=env, capture_output=True,
                            encoding="utf-8", errors="replace", timeout=300)
    record.update(exit_code=result.returncode, output=result.stdout + result.stderr)
except Exception as exc:
    record.update(exit_code=None, status="INCOMPLETE", error_type=type(exc).__name__)
(OUT / "additional-gate-result.json").write_text(
    json.dumps(record, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps({k: v for k, v in record.items() if k != "output"}))
raise SystemExit(record.get("exit_code") or (2 if record.get("status") else 0))
