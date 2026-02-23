#!/usr/bin/env python3
"""
Checkout a Defects4C bug to a working directory.
Usage: python checkout_bug.py --bug-id PROJECT@SHA [--work-dir DIR] [--fixed] [--repo-url URL]
       python checkout_bug.py --bug-id PROJECT-1   (if catalog has short id)
       For PROJECT@SHA not in catalog, pass --repo-url so the script can clone the repo.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

# Project name must be a single path component and safe (no path traversal)
SAFE_PROJECT_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")


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
        # Short form: PROJECT-1, PROJECT-2, ... (per-project 1-based index from catalog)
        short = f"{b.get('project')}-{b.get('version', '')}".rstrip("-")
        if short == bug_id:
            return b
    return None


def get_repo_url(catalog: dict, project: str) -> str | None:
    info = catalog.get("projects_info") or {}
    return info.get(project, {}).get("repo_url") if isinstance(info.get(project), dict) else None


def is_valid_repo_url(url: str) -> bool:
    """Accept https://, http://, or git@ URLs."""
    u = url.strip()
    return bool(u and (u.startswith("http://") or u.startswith("https://") or u.startswith("git@")))


def sanitize_project(project: str) -> str:
    """Strip path components and restrict to safe chars; raise ValueError if invalid."""
    name = os.path.basename(project)
    if not name or not SAFE_PROJECT_PATTERN.match(name):
        raise ValueError(f"Invalid project name: {project!r}")
    return name


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(base_dir, "data")
    default_work_dir = os.path.join(base_dir, "repos")

    parser = argparse.ArgumentParser(description="Checkout a Defects4C bug (buggy or fixed version)")
    parser.add_argument("--bug-id", required=True, help="Bug ID, e.g. libxml2@commit_sha or PROJECT-1")
    parser.add_argument("--work-dir", default=default_work_dir, help="Parent directory for project clones")
    parser.add_argument("--fixed", action="store_true", help="Checkout fixed version instead of buggy")
    parser.add_argument("--repo-url", default=None, help="Git repo URL (required when bug_id is PROJECT@SHA and project not in catalog)")
    args = parser.parse_args()
    if args.repo_url is not None:
        args.repo_url = args.repo_url.strip() or None

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

    project_raw = bug.get("project")
    if not project_raw:
        print("Catalog entry missing 'project'", file=sys.stderr)
        sys.exit(1)
    try:
        project = sanitize_project(project_raw)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    if args.fixed:
        commit = bug.get("fixed_commit")
        if not commit:
            print("Cannot checkout fixed version: bug entry has no fixed_commit (--fixed requires fixed_commit in catalog).", file=sys.stderr)
            sys.exit(1)
    else:
        commit = bug.get("buggy_commit")
        if not commit:
            print("Catalog entry missing buggy_commit", file=sys.stderr)
            sys.exit(1)

    work_dir = os.path.abspath(args.work_dir)
    os.makedirs(work_dir, exist_ok=True)
    project_dir = os.path.normpath(os.path.join(work_dir, project))
    norm_work = os.path.normpath(work_dir)
    if not (project_dir == norm_work or project_dir.startswith(norm_work + os.sep)):
        print("Path validation failed: project dir would escape work dir", file=sys.stderr)
        sys.exit(1)

    repo_url = get_repo_url(catalog, project_raw)
    if not repo_url and args.repo_url:
        if not is_valid_repo_url(args.repo_url):
            print("Invalid --repo-url: must be an https://, http://, or git@ URL", file=sys.stderr)
            sys.exit(1)
        repo_url = args.repo_url.strip()
    if not repo_url:
        print(f"No repo_url for project '{project}' (not in catalog projects_info). Use --repo-url URL for PROJECT@SHA.", file=sys.stderr)
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
