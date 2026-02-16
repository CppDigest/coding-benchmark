#!/usr/bin/env python3
"""
Checkout a Defects4C bug to a working directory.
Usage: python checkout_bug.py --bug-id PROJECT@SHA [--work-dir DIR] [--fixed]
       python checkout_bug.py --bug-id PROJECT-1   (if catalog has short id)
"""
import argparse
import json
import os
import subprocess
import sys


def load_catalog(data_dir: str) -> dict:
    path = os.path.join(data_dir, "bug_catalog.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Catalog not found: {path}. Run setup.sh first.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_bug(catalog: dict, bug_id: str) -> dict | None:
    for b in catalog.get("bugs", []):
        if b.get("bug_id") == bug_id:
            return b
        # Allow short form e.g. libxml2-1 if we add numeric ids later
        short = f"{b.get('project')}-{b.get('version', '')}".rstrip("-")
        if short == bug_id:
            return b
    return None


def get_repo_url(catalog: dict, project: str) -> str | None:
    info = catalog.get("projects_info") or {}
    return info.get(project, {}).get("repo_url") if isinstance(info.get(project), dict) else None


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(base_dir, "data")
    default_work_dir = os.path.join(base_dir, "repos")

    parser = argparse.ArgumentParser(description="Checkout a Defects4C bug (buggy or fixed version)")
    parser.add_argument("--bug-id", required=True, help="Bug ID, e.g. libxml2@commit_sha or PROJECT-1")
    parser.add_argument("--work-dir", default=default_work_dir, help="Parent directory for project clones")
    parser.add_argument("--fixed", action="store_true", help="Checkout fixed version instead of buggy")
    args = parser.parse_args()

    catalog = load_catalog(data_dir)
    bug = find_bug(catalog, args.bug_id)
    if not bug:
        # If bug_id looks like project@sha, use it directly
        if "@" in args.bug_id:
            project, sha = args.bug_id.split("@", 1)
            bug = {
                "bug_id": args.bug_id,
                "project": project,
                "buggy_commit": sha,
                "fixed_commit": None,
                "test_cmd": "",
                "build_cmd": "",
            }
        else:
            print(f"Bug not found in catalog: {args.bug_id}", file=sys.stderr)
            sys.exit(1)

    project = bug.get("project")
    if not project:
        print("Catalog entry missing 'project'", file=sys.stderr)
        sys.exit(1)

    commit = bug["fixed_commit"] if args.fixed else bug.get("buggy_commit")
    if not commit:
        commit = bug.get("buggy_commit")
    if not commit:
        print("Catalog entry missing buggy_commit", file=sys.stderr)
        sys.exit(1)

    work_dir = os.path.abspath(args.work_dir)
    os.makedirs(work_dir, exist_ok=True)
    project_dir = os.path.join(work_dir, project)

    repo_url = get_repo_url(catalog, project)
    if not repo_url:
        print(f"No repo_url for project '{project}' in catalog (projects_info)", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(os.path.join(project_dir, ".git")):
        print(f"Cloning {project}...")
        subprocess.run(["git", "clone", repo_url, project_dir], check=True, cwd=work_dir)
    else:
        print(f"Fetching {project}...")
        subprocess.run(["git", "fetch", "origin"], check=True, cwd=project_dir)

    subprocess.run(["git", "checkout", commit], check=True, cwd=project_dir)
    print(f"Checked out {project} at {commit} ({'fixed' if args.fixed else 'buggy'})")
    print(f"Work dir: {project_dir}")


if __name__ == "__main__":
    main()
