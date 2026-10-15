#!/usr/bin/env python3
"""Fast structural and deterministic contract checks."""

import json
import pathlib
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
required = [
    "harness.yaml",
    "AGENTS.md",
    ".harness/modules.lock",
    ".planning/phases/001-domain-testkit/SPEC.md",
    ".planning/phases/001-domain-testkit/PLAN.md",
    ".planning/phases/001-domain-testkit/VERIFY.md",
    "supportops_foundation/llm/__init__.py",
]
missing = [name for name in required if not (ROOT / name).is_file()]
errors = []
try:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    if project["name"] != "supportops-foundation":
        errors.append("unexpected distribution name")
    json.loads((ROOT / "docs/harness/sources.lock.json").read_text(encoding="utf-8"))
except (OSError, KeyError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
    errors.append(f"metadata parse failure: {exc}")
try:
    from supportops_foundation import __version__
    from supportops_foundation.testkit import dataset_sha256, generate_dataset

    first, second = generate_dataset(seed=42), generate_dataset(seed=42)
    if dataset_sha256(first) != dataset_sha256(second):
        errors.append("seeded dataset digest is not deterministic")
    if len(first.tickets) != 200 or len(first.golden_cases) != 60:
        errors.append("dataset size contract failed")
    if __version__ != project["version"]:
        errors.append(
            f"package version mismatch: module={__version__} project={project['version']}"
        )
except (ImportError, AttributeError, KeyError, ValueError) as exc:
    errors.append(f"domain import/contract failure: {exc}")

for name in missing:
    errors.append(f"required file missing: {name}")
print("check-fast:", "OK" if not errors else "FAIL")
for error in errors:
    print("error:", error)
sys.exit(bool(errors))
