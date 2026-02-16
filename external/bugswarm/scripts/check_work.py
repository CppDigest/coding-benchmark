#!/usr/bin/env python3
"""Self-check: validate data and script invocations. Run from external/bugswarm or repo root."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent
    data_file = root / "data" / "cpp_artifacts.json"
    errors = []

    # 1. data/cpp_artifacts.json exists and is valid
    if not data_file.exists():
        errors.append(f"Missing {data_file}")
    else:
        try:
            with open(data_file, encoding="utf-8") as f:
                catalog = json.load(f)
            if "artifacts" not in catalog or "artifact_count" not in catalog:
                errors.append("cpp_artifacts.json missing 'artifacts' or 'artifact_count'")
            elif catalog["artifact_count"] != len(catalog["artifacts"]):
                errors.append("artifact_count != len(artifacts)")
            else:
                for i, a in enumerate(catalog["artifacts"]):
                    for key in ("image_tag", "repo", "fail_commit", "pass_commit"):
                        if key not in a:
                            errors.append(f"artifacts[{i}] missing '{key}'")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")

    # 2. Scripts run without crash (help)
    for name, argv in [
        ("download_dataset.py", [sys.executable, str(script_dir / "download_dataset.py"), "--help"]),
        ("download_artifact.py", [sys.executable, str(script_dir / "download_artifact.py"), "--help"]),
        ("reproduce_ci.py", [sys.executable, str(root / "evaluation" / "reproduce_ci.py"), "--help"]),
    ]:
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=10, cwd=root)
            if r.returncode != 0:
                errors.append(f"{name} --help exited {r.returncode}: {r.stderr[:200]}")
        except Exception as e:
            errors.append(f"{name}: {e}")

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    print("Self-check OK: data valid, scripts run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
