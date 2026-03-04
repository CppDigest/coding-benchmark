#!/usr/bin/env python3
"""
Evaluation runner for SWE-PolyBench: compute accuracy/pass-rate from predictions.

NOTE: SWE-PolyBench 500 has no C/C++ issues (Java, JS, TS, Python only).
Use data/polybench_500.jsonl for evaluation.

Expects a predictions JSONL with instance_id and model_patch per line.
Optionally delegates to the official SWE-PolyBench harness (run_evaluation.py)
if --use-official and repo path are provided; otherwise computes pass rate
from a results file or placeholder.

Usage:
  python evaluate.py --dataset-path data/polybench_500.jsonl --predictions-path predictions.jsonl --result-path ./eval_results
  python evaluate.py --dataset-path data/polybench_500.jsonl --predictions-path predictions.jsonl --result-path ./eval_results --use-official --polybench-repo /path/to/SWE-PolyBench
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="SWE-PolyBench evaluation: accuracy/pass-rate")
    parser.add_argument("--dataset-path", type=Path, required=True, help="Path to dataset JSONL (e.g. polybench_500.jsonl)")
    parser.add_argument("--predictions-path", type=Path, required=True, help="Path to model predictions JSONL (instance_id, model_patch)")
    parser.add_argument("--result-path", type=Path, required=True, help="Directory for instance-level results and summary")
    parser.add_argument("--use-official", action="store_true", help="Run official SWE-PolyBench run_evaluation.py (requires --polybench-repo)")
    parser.add_argument("--polybench-repo", type=Path, default=None, help="Path to cloned amazon-science/SWE-PolyBench repo for official eval")
    parser.add_argument("--num-threads", type=int, default=1, help="Threads for official evaluator")
    parser.add_argument("--repo-path", type=Path, default=None, help="Repository path passed to official evaluator (optional)")
    args = parser.parse_args()

    args.result_path.mkdir(parents=True, exist_ok=True)

    if args.use_official and not args.polybench_repo:
        print("--polybench-repo is required when --use-official is set.", file=sys.stderr)
        return 1

    if args.use_official and args.polybench_repo:
        repo_dir = args.polybench_repo.resolve()
        if not repo_dir.is_dir():
            print(f"--polybench-repo is not an existing directory: {args.polybench_repo}", file=sys.stderr)
            return 1
        run_script = repo_dir / "src" / "poly_bench_evaluation" / "run_evaluation.py"
        if not run_script.is_file():
            print(f"Official evaluator not found: {run_script}", file=sys.stderr)
            return 1
        cmd = [
            sys.executable,
            str(run_script),
            "--dataset-path", str(args.dataset_path.resolve() if args.dataset_path.is_file() else args.dataset_path),
            "--predictions-path", str(args.predictions_path.resolve()),
            "--result-path", str(args.result_path.resolve()),
            "--num-threads", str(args.num_threads),
            "--delete-image",
        ]
        if args.repo_path is not None:
            cmd.extend(["--repo-path", str(args.repo_path.resolve())])
        # subprocess.run uses shell=False; cwd and script path are operator-controlled.
        try:
            subprocess.run(cmd, cwd=str(repo_dir), check=True)
        except subprocess.CalledProcessError as e:
            return e.returncode
        # Official script writes result.json and prints pass rate
        result_file = repo_dir / "result.json"
        summary = {}
        if result_file.exists():
            try:
                with open(result_file, encoding="utf-8") as f:
                    summary = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error reading {result_file!r}: {e}", file=sys.stderr)
                summary = {"pass_rate": None}
        print("Pass rate / resolved:", summary.get("pass_rate"), summary.get("resolved", ""))
        return 0

    # Lightweight path: validate dataset, then count predictions and optionally aggregate existing results
    if not args.dataset_path.exists():
        print(f"Dataset file not found: {args.dataset_path}", file=sys.stderr)
        return 1
    try:
        with open(args.dataset_path, encoding="utf-8") as f:
            _ = [json.loads(line) for line in f if line.strip()]
    except OSError as e:
        print(f"Cannot read dataset: {args.dataset_path}: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Invalid JSONL in dataset {args.dataset_path}: {e}", file=sys.stderr)
        return 1

    if not args.predictions_path.exists():
        print(f"Predictions file not found: {args.predictions_path}", file=sys.stderr)
        return 1
    try:
        with open(args.predictions_path, encoding="utf-8") as f:
            preds = [json.loads(line) for line in f if line.strip()]
        for p in preds:
            if "model_patch" not in p and "patch" in p:
                p["model_patch"] = p["patch"]
    except OSError as e:
        print(f"Error reading predictions file {args.predictions_path!r}: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in predictions file {args.predictions_path!r}: {e}", file=sys.stderr)
        return 1
    if not all("instance_id" in p and "model_patch" in p for p in preds):
        print("Predictions must have instance_id and model_patch (or patch) per line", file=sys.stderr)
        return 1
    summary = {
        "num_predictions": len(preds),
        "pass_rate": None,
        "resolved": None,
        "note": "Run with --use-official --polybench-repo /path/to/SWE-PolyBench for full pass-rate evaluation.",
    }
    out_summary = args.result_path / "evaluate_summary.json"
    try:
        with open(out_summary, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
    except OSError as e:
        print(f"Error writing {out_summary!r}: {e}", file=sys.stderr)
        return 1
    print(f"Wrote {out_summary}. {len(preds)} predictions. Use --use-official for pass-rate.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
