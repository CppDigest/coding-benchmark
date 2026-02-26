"""
Evaluation harness adapter for SWE-Bench Multilingual (C/C++ subset).

Reads agent predictions (JSONL with instance_id, model_patch) and produces
pass/fail metrics. Can run in two modes:

1. Standalone (default): validates predictions against cpp_issues.jsonl and
   outputs a results JSON with structure compatible with SWE-bench metrics.
   Does not run Docker or real tests; use for CI or when full harness is unavailable.

2. --harness: when set, only prints guidance for using the official SWE-bench
   harness; evaluation still uses standalone (patch-comparison) mode.

Usage:
  python run_evaluation.py --predictions_path predictions.jsonl --output_dir results/
  python run_evaluation.py --predictions_path predictions.jsonl --harness  # prints harness usage guidance
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


def normalize_patch(patch: str) -> str:
    """Normalize patch for comparison: line endings and trailing whitespace per line."""
    if not patch:
        return ""
    text = patch.replace("\r\n", "\n").replace("\r", "\n").strip()
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def run_standalone_evaluation(
    predictions_path: str,
    cpp_issues_path: str,
    output_dir: str,
) -> dict:
    """
    Validate predictions and produce a results JSON with pass/fail-style metrics.
    Standalone mode: compares model_patch to gold_patch after normalization (line
    endings, trailing whitespace). resolved = True only when the normalized patches
    match. For execution-based evaluation use --harness with the official SWE-bench
    harness when available.
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
                "patch_submitted": bool(patch.strip()),
                "error": "instance_id not in C/C++ dataset",
            })
            continue
        rec = issues[iid]
        gold = (rec.get("gold_patch") or "").strip()
        has_patch = bool(patch.strip())
        # Resolved only if we have a gold patch to compare and normalized patches match
        if not gold:
            is_resolved = False
        else:
            is_resolved = has_patch and (
                normalize_patch(patch) == normalize_patch(gold)
            )
        instance_results.append({
            "instance_id": iid,
            "resolved": is_resolved,
            "patch_submitted": has_patch,
        })
        if is_resolved:
            resolved += 1

    total_instances = len(issues)
    results = {
        "instances_submitted": len(preds),
        "instances_resolved": resolved,
        "total_instances": total_instances,
        "resolution_rate": (resolved / total_instances * 100.0) if total_instances else 0.0,
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
        help="Print instructions for official SWE-bench harness (does NOT run it; standalone evaluation still runs)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.cpp_issues):
        print("Error: cpp_issues.jsonl not found at", args.cpp_issues, file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.predictions_path):
        print("Error: predictions file not found at", args.predictions_path, file=sys.stderr)
        sys.exit(1)

    if args.harness:
        print("Harness mode: use official SWE-bench CLI for full execution-based evaluation:", file=sys.stderr)
        print("  python -m swebench.harness.run_evaluation --dataset_name SWE-bench/SWE-bench_Multilingual --predictions_path <path> ...", file=sys.stderr)

    run_standalone_evaluation(
        predictions_path=args.predictions_path,
        cpp_issues_path=args.cpp_issues,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
