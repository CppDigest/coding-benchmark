#!/usr/bin/env python3
"""
Execute C++ solution for a single HumanEval/MultiPL-E problem in sandbox.
Reads prompt + solution + tests from stdin (JSON), compiles and runs with g++,
prints JSON result: {"status": "OK"|"CompileError"|"Timeout"|"RuntimeError", "stdout", "stderr", "pass": bool}.
Designed to run inside Docker with network disabled.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_SEC = 10
COMPILE_TIMEOUT = 30


def main() -> None:
    try:
        inp = json.load(sys.stdin)
    except Exception as e:
        print(json.dumps({"status": "RuntimeError", "task_id": "unknown", "stderr": str(e), "pass": False}))
        sys.exit(1)
    prompt = inp.get("prompt", "")
    solution = inp.get("solution", inp.get("canonical_solution", ""))
    tests = inp.get("tests", "")
    task_id = inp.get("task_id", "unknown")
    if not prompt and not solution:
        print(json.dumps({"status": "RuntimeError", "task_id": task_id, "stderr": "missing prompt/solution", "pass": False}))
        sys.exit(1)
    full_code = (prompt + "\n" + solution + "\n" + tests).strip()
    with tempfile.TemporaryDirectory(prefix="cpp_") as d:
        path = Path(d) / "main.cpp"
        path.write_text(full_code, encoding="utf-8")
        exe = Path(d) / "main"
        try:
            r = subprocess.run(
                ["g++", "-std=c++17", "-O0", "-o", str(exe), str(path)],
                capture_output=True,
                text=True,
                timeout=COMPILE_TIMEOUT,
                cwd=d,
            )
        except subprocess.TimeoutExpired:
            print(json.dumps({"status": "CompileError", "task_id": task_id, "stderr": "compile timeout", "pass": False}))
            sys.exit(0)
        if r.returncode != 0:
            print(json.dumps({
                "status": "CompileError",
                "task_id": task_id,
                "stdout": r.stdout or "",
                "stderr": r.stderr or "",
                "pass": False,
            }))
            sys.exit(0)
        try:
            run_r = subprocess.run(
                [str(exe)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SEC,
                cwd=d,
            )
        except subprocess.TimeoutExpired:
            print(json.dumps({"status": "Timeout", "task_id": task_id, "stderr": "execution timeout", "pass": False}))
            sys.exit(0)
        passed = run_r.returncode == 0
        print(json.dumps({
            "status": "OK" if passed else "RuntimeError",
            "task_id": task_id,
            "stdout": run_r.stdout or "",
            "stderr": run_r.stderr or "",
            "pass": passed,
            "exit_code": run_r.returncode,
        }))


if __name__ == "__main__":
    main()
