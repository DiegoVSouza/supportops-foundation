"""Reproduce the phase040 fixture `git add` exit 128 and capture the stderr it hid.

Rebuilds the fixture shape of test_candidate_requires_committed_schema_and_all_
fingerprinted_sources under the phase040 path layout, offline, and varies one
factor at a time: path length and a `.git` component above the work tree.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
PHASE040 = "artifacts/evidence/additional-validation-040/.git/snapshot/lab/projects/p00"
TEMP = "artifacts/evidence/additional-validation-040/pytest-tmp/test_candidate_requires_committe0"
FIXTURE = "lab/projects/p00"


def git(cwd, *arguments):
    result = subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", *arguments],
                            cwd=cwd, capture_output=True, text=True)
    return {"args": list(arguments), "exit_code": result.returncode, "stderr": result.stderr.strip()[:400]}


def attempt(name, base):
    repo = base / FIXTURE
    repo.mkdir(parents=True)
    (repo / "guard.py").write_text("x = 1\n", encoding="utf-8")
    steps = [git(repo, "init"), git(repo, "add", "guard.py")]
    return {"name": name, "repo_path_length": len(str(repo)), "steps": steps}


def main():
    work = OUT / "work"
    report = []
    cases = {
        "phase040_layout_with_dot_git": work / "a/.git/snapshot/lab/projects/p00" / TEMP,
        "same_length_without_dot_git": work / "a/_git/snapshot/lab/projects/p00" / TEMP,
        "short_path_with_dot_git": work / "b/.git/x",
        "short_path_plain": work / "c/x",
    }
    try:
        for name, base in cases.items():
            report.append(attempt(name, base))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    env = {key: os.environ.get(key) for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
    (OUT / "result.json").write_text(json.dumps({"phase040_cwd_suffix": PHASE040, "git_env": env, "cases": report}, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    for case in report:
        print(case["name"], case["repo_path_length"], [step["exit_code"] for step in case["steps"]], case["steps"][-1]["stderr"][:160])


if __name__ == "__main__":
    sys.exit(main())
