"""Prepare a fresh offline snapshot without running the finite full gate."""
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
LAB = PROJECT.parents[1]
TARGET = OUT / "snapshot-attempt2" / "lab"
WORK = TARGET / "projects/p00"


def tracked(root):
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True
    )
    return [Path(p.decode("utf-8")) for p in result.stdout.split(b"\0") if p]


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


if TARGET.exists():
    raise SystemExit("fresh snapshot required")
TARGET.mkdir(parents=True)
records = []
for rel in tracked(LAB):
    if (LAB / rel).is_file():
        copy_file(LAB / rel, TARGET / rel)

result = subprocess.run(
    ["git", "-c", f"safe.directory={PROJECT.as_posix()}/.git", "clone",
     "--no-hardlinks", "--no-checkout", str(PROJECT), str(WORK)],
    capture_output=True, text=True,
)
records.append({"command": result.args, "exit_code": result.returncode,
                "output": result.stdout + result.stderr})
if result.returncode:
    (OUT / "snapshot-preparation-failure.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8"
    )
    raise SystemExit("snapshot clone failed")
for rel in tracked(PROJECT):
    if (PROJECT / rel).is_file():
        copy_file(PROJECT / rel, WORK / rel)

# SQLite backup includes committed WAL transactions without copying live sidecars.
for owner in [LAB / ".runtime/llm-live-readiness", *[
    LAB / "projects" / name / "artifacts/evals/live"
    for name in ("p00", "p01", "p02", "p03", "p04", "p05")
]]:
    for source in owner.glob("*.sqlite"):
        target = TARGET / source.relative_to(LAB)
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as src:
            with sqlite3.connect(target) as dst:
                src.backup(dst)
        records.append({"sqlite_backup": source.relative_to(LAB).as_posix()})
registry = Path(".runtime/llm-live-readiness/ledger-references.json")
copy_file(LAB / registry, TARGET / registry)
(OUT / "snapshot-preparation.json").write_text(
    json.dumps({"status": "PREPARED", "gate_executed": False,
                "provider_accessed": False, "snapshot": str(TARGET),
                "records": records}, indent=2) + "\n", encoding="utf-8"
)
print("snapshot prepared; full gate not executed")
