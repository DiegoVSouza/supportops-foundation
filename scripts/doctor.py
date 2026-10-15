"""Report actual local runtime/service availability; does not start services."""

from __future__ import annotations

import importlib.metadata
import pathlib
import shutil
import socket
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PORTS = {"postgres": 5432, "redis": 6379, "localstack": 4566}


def command_version(name: str, args: list[str]) -> str:
    executable = shutil.which(name)
    if not executable:
        return "UNAVAILABLE"
    result = subprocess.run(
        [executable, *args], check=False, capture_output=True, text=True, timeout=10
    )
    return (
        (result.stdout or result.stderr).splitlines()[0]
        if result.returncode == 0
        else f"ERROR(exit={result.returncode})"
    )


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.25):
            return True
    except OSError:
        return False


def main() -> int:
    print(f"python={sys.version.split()[0]}")
    print(f"uv={command_version('uv', ['--version'])}")
    print(f"docker={command_version('docker', ['--version'])}")
    if shutil.which("docker"):
        print(f"docker_compose={command_version('docker', ['compose', 'version', '--short'])}")
    print(f"supportops_foundation={importlib.metadata.version('supportops-foundation')}")
    incomplete = False
    for name, port in PORTS.items():
        available = port_open(port)
        print(f"{name}_127.0.0.1:{port}={'AVAILABLE' if available else 'UNAVAILABLE'}")
        incomplete |= not available
    print(
        f"compose_file={'PRESENT' if (ROOT / 'docker-compose.base.yml').is_file() else 'MISSING'}"
    )
    print("services are observed only; doctor does not start containers")
    return 1 if incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main())
