#!/usr/bin/env python3
"""
Download MultiPL-E C++ subset and HumanEval Python reference from Hugging Face.

1. Load nuprl/MultiPL-E config "humaneval-cpp" -> data/cpp_problems.jsonl
2. Load openai/openai_humaneval (Python) -> data/humaneval_python.jsonl

Required: pip install datasets

Usage:
  python download.py [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def to_record(record: dict, task_id_key: str = "task_id", prompt_key: str = "prompt",
              test_key: str = "test", canonical_key: str = "canonical_solution") -> dict:
    """Normalize to task_id, prompt, tests, canonical_solution."""
    task_id = record.get(task_id_key) or record.get("name") or ""
    prompt = record.get(prompt_key) or ""
    tests = record.get(test_key) or record.get("tests") or ""
    canonical = record.get(canonical_key) or record.get("canonical_solution") or ""
    if hasattr(task_id, "tolist"):
        task_id = str(task_id) if not hasattr(task_id, "tolist") else task_id
    if hasattr(prompt, "tolist"):
        prompt = str(prompt)
    if hasattr(tests, "tolist"):
        tests = str(tests)
    if hasattr(canonical, "tolist"):
        canonical = str(canonical)
    return {"task_id": task_id, "prompt": prompt, "tests": tests, "canonical_solution": canonical}


def main() -> int:
    parser = argparse.ArgumentParser(description="Download MultiPL-E C++ and HumanEval Python")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent
    out_dir = args.output_dir or (root / "data")
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from datasets import load_dataset
    except ImportError:
        print("Install datasets: pip install datasets", file=sys.stderr)
        return 1

    # MultiPL-E C++
    print("Loading nuprl/MultiPL-E (humaneval-cpp)...", file=sys.stderr)
    try:
        ds_cpp = load_dataset("nuprl/MultiPL-E", "humaneval-cpp", split="test")
    except Exception as e:
        print(f"Failed to load MultiPL-E C++: {e}", file=sys.stderr)
        return 1
    cpp_records = []
    for i in range(len(ds_cpp)):
        row = ds_cpp[i]
        r = to_record(dict(row), task_id_key="name" if "name" in row else "task_id",
                      test_key="tests" if "tests" in row else "test")
        cpp_records.append(r)
    cpp_path = out_dir / "cpp_problems.jsonl"
    with open(cpp_path, "w", encoding="utf-8") as f:
        for r in cpp_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(cpp_records)} C++ problems to {cpp_path}", file=sys.stderr)

    # HumanEval Python reference
    print("Loading openai/openai_humaneval (Python)...", file=sys.stderr)
    try:
        ds_py = load_dataset("openai/openai_humaneval", split="test")
    except Exception as e:
        print(f"Failed to load HumanEval Python: {e}", file=sys.stderr)
        return 1
    py_records = []
    for i in range(len(ds_py)):
        row = ds_py[i]
        r = to_record(dict(ds_py[i]))
        py_records.append(r)
    py_path = out_dir / "humaneval_python.jsonl"
    with open(py_path, "w", encoding="utf-8") as f:
        for r in py_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(py_records)} Python problems to {py_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
