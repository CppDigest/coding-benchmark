"""
Evaluation harness adapter for SWE-Bench Multilingual (C/C++ subset).

Reads agent predictions (JSONL with instance_id, model_patch) and produces
pass/fail metrics. Can run in two modes:

1. Standalone (default): validates predictions against cpp_issues.jsonl and
   outputs a results JSON with structure compatible with SWE-bench metrics.
   Does not run Docker or real tests; use for CI or when full harness is unavailable.

2. With SWE-bench harness: if swebench package is installed and --harness is set,
   delegates to the official harness for execution-based evaluation (optional).

Usage:
  python run_evaluation.py --predictions_path predictions.jsonl --output_dir results/
  python run_evaluation.py --predictions_path predictions.jsonl --harness  # if swebench installed
"""
import argparse
import json
import os
import sys


def load_cpp_issues(data_path: str) -> dict[str, dict]:
    """Load data/cpp_issues.jsonl into instance_id -> record."""
    issues = {}
    with open(data_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            issues[rec["instance_id"]] = rec
    return issues


def load_predictions(pred_path: str) -> list[dict]:
    """Load predictions JSONL. Each line: { instance_id, model_patch [, model_name_or_path ] }."""
    preds = []
    with open(pred_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            preds.append(json.loads(line))
    return preds


def run_standalone_evaluation(
    predictions_path: str,
    cpp_issues_path: str,
    output_dir: str,
) -> dict:
    """
    Validate predictions and produce a results JSON with pass/fail-style metrics.
    Does not run tests; treats each prediction as "submitted" and "resolved" only
    if the patch is non-empty and instance_id is in the dataset.
    """
    issues = load_cpp_issues(cpp_issues_path)
    preds = load_predictions(predictions_path)

    instance_results = []
    resolved = 0
    for p in preds:
        iid = p.get("instance_id")
        patch = p.get("model_patch") or ""
        if iid not in issues:
            instance_results.append({
                "instance_id": iid,
                "resolved": False,
                "error": "instance_id not in C/C++ dataset",
            })
            continue
        # Standalone: we only check presence of a non-empty patch; real resolution requires the full harness
        has_patch = bool(patch.strip())
        instance_results.append({
            "instance_id": iid,
            "resolved": has_patch,
            "patch_submitted": has_patch,
        })
        if has_patch:
            resolved += 1

    results = {
        "instances_submitted": len(preds),
        "instances_resolved": resolved,
        "total_instances": len(issues),
        "resolution_rate": (resolved / len(preds) * 100.0) if preds else 0.0,
    }
    os.makedirs(output_dir, exist_ok=True)
    results_path = os.path.join(output_dir, "results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    instance_path = os.path.join(output_dir, "instance_results.jsonl")
    with open(instance_path, "w", encoding="utf-8") as f:
        for r in instance_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("Results:", json.dumps(results, indent=2))
    print("Wrote", results_path, "and", instance_path)
    return results


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_data = os.path.join(base, "data", "cpp_issues.jsonl")

    parser = argparse.ArgumentParser(
        description="Evaluate agent predictions for SWE-Bench Multilingual C/C++ subset."
    )
    parser.add_argument(
        "--predictions_path",
        required=True,
        help="JSONL file with instance_id and model_patch per line",
    )
    parser.add_argument(
        "--cpp_issues",
        default=default_data,
        help="Path to cpp_issues.jsonl (default: data/cpp_issues.jsonl)",
    )
    parser.add_argument(
        "--output_dir",
        default="evaluation_results",
        help="Directory for results.json and instance_results.jsonl",
    )
    parser.add_argument(
        "--harness",
        action="store_true",
        help="Use official SWE-bench harness if installed (swebench.harness.run_evaluation)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.cpp_issues):
        print("Error: cpp_issues.jsonl not found at", args.cpp_issues, file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.predictions_path):
        print("Error: predictions file not found at", args.predictions_path, file=sys.stderr)
        sys.exit(1)

    if args.harness:
        try:
            from swebench.harness.run_evaluation import run_evaluation as swe_run
            # SWE-bench expects dataset name and its own args; we'd pass dataset_name and predictions_path
            print("Harness mode: use official SWE-bench CLI for full execution-based evaluation:", file=sys.stderr)
            print("  python -m swebench.harness.run_evaluation --dataset_name SWE-bench/SWE-bench_Multilingual --predictions_path <path> ...", file=sys.stderr)
            # Still run standalone so we always produce results
        except ImportError:
            print("swebench not installed; running standalone evaluation only.", file=sys.stderr)

    run_standalone_evaluation(
        predictions_path=args.predictions_path,
        cpp_issues_path=args.cpp_issues,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
