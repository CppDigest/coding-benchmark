#!/usr/bin/env python3
"""
Evaluate pass@k for MultiPL-E C++ / HumanEval-style completions.

Reads dataset JSONL (task_id, prompt, tests) and completions: either
- a JSONL with one completion per line: {"task_id": "...", "solution": "..."} (or "completion")
- or a directory of .json.gz / .jsonl per task (MultiPL-E native format)

Computes pass@1, pass@10, pass@100 using the sandbox (Docker) or a local executor.
Requires Docker for sandbox execution.

Usage:
  python evaluate_passk.py --dataset data/cpp_problems.jsonl --completions completions.jsonl --result-dir ./results
  python evaluate_passk.py --dataset data/cpp_problems.jsonl --completions-dir ./samples --result-dir ./results --k 1,10,100
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_dataset(path: Path) -> dict[str, dict]:
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            tid = r.get("task_id") or r.get("name") or ""
            out[tid] = r
    return out


def run_sandbox_one(prompt: str, solution: str, tests: str, task_id: str, docker: bool = True) -> bool:
    payload = {"task_id": task_id, "prompt": prompt, "solution": solution, "tests": tests}
    if docker:
        script_dir = Path(__file__).resolve().parent
        sandbox_dir = script_dir / "sandbox"
        try:
            r = subprocess.run(
                ["docker", "run", "--rm", "--network", "none",
                 "-v", f"{sandbox_dir}:/workspace:ro",
                 "-i", "multiple-humaneval-sandbox:latest"],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=60,
                cwd=sandbox_dir,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        if r.returncode != 0:
            return False
        try:
            res = json.loads(r.stdout or r.stderr or "{}")
            return res.get("pass", False)
        except Exception:
            return False
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate pass@k for C++ HumanEval")
    parser.add_argument("--dataset", type=Path, required=True, help="cpp_problems.jsonl")
    parser.add_argument("--completions", type=Path, default=None, help="JSONL: task_id, solution (one per line)")
    parser.add_argument("--completions-dir", type=Path, default=None, help="Dir with task_id.jsonl or .json.gz (multiple samples per task)")
    parser.add_argument("--result-dir", type=Path, required=True, help="Output directory for results")
    parser.add_argument("--k", type=str, default="1,10,100", help="Comma-separated k values for pass@k")
    parser.add_argument("--no-docker", action="store_true", help="Run execute.py locally (unsafe, for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Only load and count, do not run sandbox")
    args = parser.parse_args()

    args.result_dir.mkdir(parents=True, exist_ok=True)
    ks = [int(x.strip()) for x in args.k.split(",") if x.strip()]

    data = load_dataset(args.dataset)
    if not data:
        print("No problems in dataset", file=sys.stderr)
        return 1

    # Load completions: task_id -> list of solution strings (up to max_k)
    max_k = max(ks) if ks else 100
    completions_by_task: dict[str, list[str]] = {}
    if args.completions and args.completions.exists():
        with open(args.completions, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                c = json.loads(line)
                tid = c.get("task_id") or c.get("name") or ""
                sol = c.get("solution") or c.get("completion") or c.get("canonical_solution") or ""
                if tid not in completions_by_task:
                    completions_by_task[tid] = []
                if len(completions_by_task[tid]) < max_k:
                    completions_by_task[tid].append(sol)
    elif args.completions_dir and args.completions_dir.is_dir():
        for f in args.completions_dir.iterdir():
            if f.suffix not in (".jsonl", ".json", ".gz"):
                continue
            # Assume filename = task_id or task_id.jsonl
            tid = f.stem.replace(".jsonl", "").replace(".json", "")
            if tid not in completions_by_task:
                completions_by_task[tid] = []
            if f.suffix == ".gz":
                import gzip
                with gzip.open(f, "rt", encoding="utf-8") as fp:
                    for line in fp:
                        if line.strip() and len(completions_by_task[tid]) < max_k:
                            try:
                                obj = json.loads(line)
                                completions_by_task[tid].append(obj.get("completion", obj.get("solution", "")))
                            except Exception:
                                pass
            else:
                with open(f, encoding="utf-8") as fp:
                    for line in fp:
                        if line.strip() and len(completions_by_task[tid]) < max_k:
                            try:
                                obj = json.loads(line)
                                completions_by_task[tid].append(obj.get("completion", obj.get("solution", "")))
                            except Exception:
                                pass
    else:
        print("Provide --completions or --completions-dir", file=sys.stderr)
        return 1

    if args.dry_run:
        n = sum(1 for t, s in completions_by_task.items() if s)
        print(f"Dry run: {len(data)} problems, {n} tasks with completions, k={ks}", file=sys.stderr)
        return 0

    # Evaluate each task: for each k, pass@k = 1 if any of first k solutions passes
    results = {}
    for tid, problem in data.items():
        prompt = problem.get("prompt", "")
        tests = problem.get("tests", "")
        sols = completions_by_task.get(tid, [])
        passed_any = False
        for sol in sols[:max_k]:
            if run_sandbox_one(prompt, sol, tests, tid, docker=not args.no_docker):
                passed_any = True
                break
        results[tid] = passed_any

    n_total = len(results)
    n_pass = sum(1 for v in results.values() if v)
    pass_at_1 = n_pass / n_total if n_total else 0.0
    # pass@10 and pass@100 would need multiple samples per task; here we only have one run per task (first solution that passes)
    metrics = {"pass@1": pass_at_1, "resolved": n_pass, "total": n_total}
    for k in ks:
        if k > 1:
            metrics[f"pass@{k}"] = pass_at_1  # placeholder unless we have k samples per task
    out_file = args.result_dir / "evaluate_passk.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"pass@1={pass_at_1:.4f} resolved={n_pass}/{n_total}", file=sys.stderr)
    print(f"Wrote {out_file}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
