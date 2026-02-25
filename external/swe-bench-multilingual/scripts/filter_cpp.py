"""
Filter SWE-Bench Multilingual raw data to C/C++ issues only and write
external/swe-bench-multilingual/data/cpp_issues.jsonl.

Each line is a JSON object with: repo_url, commit_base, issue_text, gold_patch,
test_command, plus instance_id, fail_to_pass, pass_to_pass for the evaluation harness.

Run after download.py. Reads from data/raw/*.parquet (all splits).
"""
import argparse
import json
import os
import re

try:
    import pyarrow.parquet as pq
except ImportError:
    raise SystemExit("Install pyarrow: pip install pyarrow") from None

# File extensions that indicate C/C++ in a diff path (exclude .ch, .ts, .cs, .html, etc.)
CPP_EXT_RE = re.compile(
    r"\.(c|cc|cpp|cxx|h|hpp|hxx)\b",
    re.IGNORECASE,
)


def is_cpp_patch(patch: str) -> bool:
    """True if the unified diff touches at least one C/C++ file."""
    if not patch:
        return False
    # Look for diff --git a/path b/path or +++ b/path
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            # e.g. "diff --git a/src/foo.c b/src/foo.c"
            if CPP_EXT_RE.search(line):
                return True
        if line.startswith("+++ ") or line.startswith("--- "):
            if CPP_EXT_RE.search(line):
                return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Filter raw parquet to C/C++ issues as JSONL.")
    parser.add_argument(
        "--raw-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "raw"),
        help="Directory containing *.parquet from download.py",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "cpp_issues.jsonl"),
        help="Output JSONL path",
    )
    args = parser.parse_args()

    raw_dir = os.path.abspath(args.raw_dir)
    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    rows = []
    for name in sorted(os.listdir(raw_dir)):
        if not name.endswith(".parquet"):
            continue
        path = os.path.join(raw_dir, name)
        table = pq.read_table(path)
        required = ("repo", "base_commit", "patch", "problem_statement", "instance_id")
        missing = [c for c in required if c not in table.column_names]
        if missing:
            raise SystemExit(
                f"Missing required columns in {path}: {missing}. "
                f"Available: {sorted(table.column_names)}."
            ) from None
        repo_col = table.column("repo")
        base_commit_col = table.column("base_commit")
        patch_col = table.column("patch")
        problem_col = table.column("problem_statement")
        instance_id_col = table.column("instance_id")
        hints_col = table.column("hints_text") if "hints_text" in table.column_names else None
        fail_to_pass = table.column("FAIL_TO_PASS") if "FAIL_TO_PASS" in table.column_names else None
        pass_to_pass = table.column("PASS_TO_PASS") if "PASS_TO_PASS" in table.column_names else None

        for i in range(table.num_rows):
            patch_val = patch_col[i].as_py() if hasattr(patch_col[i], "as_py") else str(patch_col[i])
            if not is_cpp_patch(patch_val):
                continue
            repo = repo_col[i].as_py() if hasattr(repo_col[i], "as_py") else str(repo_col[i])
            base_commit = base_commit_col[i].as_py() if hasattr(base_commit_col[i], "as_py") else str(base_commit_col[i])
            problem = problem_col[i].as_py() if hasattr(problem_col[i], "as_py") else str(problem_col[i])
            instance_id = instance_id_col[i].as_py() if hasattr(instance_id_col[i], "as_py") else str(instance_id_col[i])
            hints = hints_col[i].as_py() if hints_col is not None else ""
            if hints:
                issue_text = f"{problem}\n\n{hints}".strip()
            else:
                issue_text = problem

            fail_list = []
            if fail_to_pass is not None:
                f = fail_to_pass[i]
                if f is not None and hasattr(f, "as_py"):
                    fail_list = f.as_py() or []
            pass_list = []
            if pass_to_pass is not None:
                p = pass_to_pass[i]
                if p is not None and hasattr(p, "as_py"):
                    pass_list = p.as_py() or []

            test_command = (
                "Run the repository test suite. "
                "Use fail_to_pass and pass_to_pass for the tests used in SWE-bench evaluation."
            )
            record = {
                "instance_id": instance_id,
                "repo_url": f"https://github.com/{repo}",
                "repo": repo,
                "commit_base": base_commit,
                "issue_text": issue_text,
                "gold_patch": patch_val,
                "test_command": test_command,
                "fail_to_pass": fail_list or [],
                "pass_to_pass": pass_list or [],
            }
            rows.append(record)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} C/C++ issues to {output_path}")


if __name__ == "__main__":
    main()
