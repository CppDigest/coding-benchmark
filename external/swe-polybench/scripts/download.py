#!/usr/bin/env python3
"""
Download SWE-PolyBench 500 subset from Hugging Face and write JSONL.

The official SWE-PolyBench_500 dataset contains only Java, JavaScript,
TypeScript, and Python (125 per language). There are no C/C++ issues.
No C/C++ subset is produced; use other benchmarks in this repo for C/C++.

1. Load AmazonScience/SWE-PolyBench_500 (500 instances).
2. Write full 500 to data/polybench_500.jsonl (one JSON object per line).

Required: pip install datasets

Usage:
  python download.py [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def row_to_record(row, columns: list) -> dict:
    """Convert a dataset row to our JSONL record with required fields."""
    d = {}
    for col in columns:
        if col not in row:
            continue
        v = row[col]
        if hasattr(v, "tolist"):  # numpy etc.
            v = v.tolist()
        d[col] = v
    # Ensure required fields for acceptance criteria
    out = {
        "language": d.get("language", ""),
        "repo": d.get("repo", ""),
        "issue_text": d.get("problem_statement", ""),
        "test_cmd": d.get("test_command", ""),
        "expected_patch": d.get("patch", ""),
    }
    out["instance_id"] = d.get("instance_id", "")
    out["base_commit"] = d.get("base_commit", "")
    out["F2P"] = d.get("F2P", "")
    out["P2P"] = d.get("P2P", "")
    out["task_category"] = d.get("task_category", "")
    out["patch"] = d.get("patch", "")
    out["problem_statement"] = d.get("problem_statement", "")
    out["test_command"] = d.get("test_command", "")
    if "Dockerfile" in d:
        out["Dockerfile"] = d["Dockerfile"]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Download SWE-PolyBench 500 and write JSONL")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: data/ under repo root)",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="AmazonScience/SWE-PolyBench_500",
        help="Hugging Face dataset name",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent
    out_dir = args.output_dir or (root / "data")
    out_dir.mkdir(parents=True, exist_ok=True)
    path_500 = out_dir / "polybench_500.jsonl"

    try:
        from datasets import load_dataset
        from datasets.exceptions import DatasetNotFoundError
    except ImportError:
        print("Install datasets: pip install datasets", file=sys.stderr)
        return 1

    print(f"Loading {args.dataset_name} from Hugging Face...", file=sys.stderr)
    try:
        ds = load_dataset(args.dataset_name, split="test")
    except (OSError, ValueError, DatasetNotFoundError) as e:
        print(f"Failed to load dataset: {e}", file=sys.stderr)
        return 1

    columns = list(ds.column_names)
    records = [row_to_record(ds[i], columns) for i in range(len(ds))]
    print(f"Loaded {len(records)} instances.", file=sys.stderr)

    with open(path_500, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {path_500} ({len(records)} instances).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
