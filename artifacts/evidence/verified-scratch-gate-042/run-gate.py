"""Run exactly the newly authorized P00 fake gate in the prepared snapshot."""
import json
import os
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
WORK = PROJECT.parents[1] / ".runtime/.git/p00-gate-042/lab/projects/p00"
MARKER = OUT / "attempt.json"
if MARKER.exists() or not WORK.is_dir():
    raise SystemExit("attempt consumed or snapshot missing")
env = {k: v for k, v in os.environ.items() if not k.startswith("GROQ_API_KEY")}
env.update(LLM_MODE="fake", UV_OFFLINE="1", VIRTUAL_ENV=str(PROJECT / ".venv"),
           PYTHONPATH=str(WORK), PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
           P00_PYTEST_BASETEMP="artifacts/evidence/funded-candidate-continuation/gate-042/pytest")
requested = (WORK / env["P00_PYTEST_BASETEMP"]).resolve()
allowed = (WORK / "artifacts/evidence/funded-candidate-continuation").resolve()
if not requested.is_relative_to(allowed) or requested == allowed:
    raise SystemExit("unsafe scratch path; gate not consumed")
(WORK / env["P00_PYTEST_BASETEMP"]).parent.mkdir(parents=True, exist_ok=True)
command = ["uv", "run", "--locked", "--no-sync", "--active", "python", "scripts/check_full.py"]
with MARKER.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump({"historical": "3/3", "phase038_exception": "1/1",
               "phase039_exception": "1/1", "phase040_exception": "1/1",
               "phase041_exception": "1/1", "phase042_exception": "1/1", "state": "CONSUMED",
               "command": command, "cwd": str(WORK)}, stream)
    stream.flush()
    os.fsync(stream.fileno())
try:
    result = subprocess.run(command, cwd=WORK, env=env, capture_output=True,
                            encoding="utf-8", errors="replace", timeout=300)
    record = {"exit_code": result.returncode, "output": result.stdout + result.stderr}
except Exception as error:
    record = {"exit_code": None, "error_type": type(error).__name__}
record.update(command=command, cwd=str(WORK), provider_accessed=False)
(OUT / "gate-result.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"exit_code": record["exit_code"], "provider_accessed": False}))
raise SystemExit(record["exit_code"] if record["exit_code"] is not None else 2)
