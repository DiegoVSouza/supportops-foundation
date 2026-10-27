"""Run the real offline product gate and report optional service checks honestly."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENV = os.environ | {"LLM_MODE": "fake"}


def run(label: str, command: list[str], *, optional: bool = False) -> bool:
    print(f"\n== {label}: {' '.join(command)} ==", flush=True)
    result = subprocess.run(
        command,
        check=False,
        cwd=ROOT,
        env=ENV,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    print(f"EXIT_CODE={result.returncode}")
    return result.returncode == 0 or optional


def main() -> int:
    (ROOT / "artifacts/tmp").mkdir(parents=True, exist_ok=True)
    pytest_basetemp = os.environ.get("P00_PYTEST_BASETEMP", "artifacts/tmp/pytest")
    if "P00_PYTEST_BASETEMP" in os.environ:
        requested = pathlib.Path(pytest_basetemp)
        if not requested.is_absolute():
            requested = ROOT / requested
        requested = requested.resolve()
        allowed = (ROOT / "artifacts/evidence/private-review-ui").resolve()
        if requested == allowed or not requested.is_relative_to(allowed):
            print("Invalid P00_PYTEST_BASETEMP: path must stay under private-review-ui evidence")
            return 2
        pytest_basetemp = requested.relative_to(ROOT).as_posix()
    if not run("fast", [sys.executable, "scripts/check_fast.py"]):
        return 1
    if not run(
        "lint",
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "supportops_foundation",
            "demo",
            "scripts",
            "tests",
        ],
    ):
        return 1
    if not run(
        "format",
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--check",
            "supportops_foundation",
            "demo",
            "scripts",
            "tests",
        ],
    ):
        return 1
    if not run(
        "compile",
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "supportops_foundation",
            "demo",
            "scripts",
            "tests",
        ],
    ):
        return 1
    if not run("tests", [sys.executable, "-m", "pytest", "-q", f"--basetemp={pytest_basetemp}"]):
        return 1
    if not run(
        "dataset-contract",
        [
            sys.executable,
            "-c",
            (
                "from supportops_foundation import __version__; "
                "from supportops_foundation.testkit import dataset_sha256, generate_dataset; "
                "a=generate_dataset(seed=42); b=generate_dataset(seed=42); "
                "assert len(a.customers)==40 and len(a.tickets)==200 and len(a.articles)==30 and len(a.invoices)==80; "
                "assert len(a.golden_cases)==60 and dataset_sha256(a)==dataset_sha256(b); "
                "print(f'version={__version__} customers=40 tickets=200 golden=60 digest={dataset_sha256(a)}')"
            ),
        ],
    ):
        return 1
    docker = shutil.which("docker")
    if docker:
        run(
            "compose-config",
            [docker, "compose", "-f", "docker-compose.base.yml", "config", "--quiet"],
            optional=True,
        )
    else:
        print("\n== compose-config ==\nINCOMPLETE: Docker CLI unavailable\nEXIT_CODE=INCOMPLETE")
    print("\nPRODUCT_CHECK=PASS; OPTIONAL_SERVICE_E2E=INCOMPLETE unless separately executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
