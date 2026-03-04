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


from catalog import load_catalog, find_bug


def get_repo_url(catalog: dict, project: str) -> str | None:
    info = catalog.get("projects_info") or {}
    return info.get(project, {}).get("repo_url") if isinstance(info.get(project), dict) else None


def is_valid_repo_url(url: str) -> bool:
    """Accept https:// or git@ URLs (no plain http://)."""
    u = url.strip()
    return bool(u and (u.startswith("https://") or u.startswith("git@")))


def sanitize_project(project: str) -> str:
    """Strip path components and restrict to safe chars; raise ValueError if invalid."""
    name = os.path.basename(project)
    if not name or name == "." or name == ".." or not SAFE_PROJECT_PATTERN.match(name):
        raise ValueError(f"Invalid project name: {project!r}")
    return name


def run_git(cmd_args: list[str], cwd: str, timeout: int = 300) -> None:
    """Run git with the given args; on timeout or non-zero exit, print message and exit 1."""
    try:
        subprocess.run(["git"] + cmd_args, check=True, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"git {' '.join(cmd_args[:2])}... timed out after {timeout}s", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"git {' '.join(cmd_args[:2])}... failed: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"git ...: not found or not executable: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"git ...: {e}", file=sys.stderr)
        sys.exit(1)


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

    try:
        catalog = load_catalog(data_dir)
        bug = find_bug(catalog, args.bug_id)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        catalog = {}
        bug = None
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
    # Validate that commit looks like a Git SHA (7-40 hex chars) before checkout.
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", str(commit)):
        print(f"Invalid commit SHA in catalog for bug_id={bug.get('bug_id')!r}: {commit!r}", file=sys.stderr)
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
        repo_url = args.repo_url.strip()
    if not repo_url:
        print(f"No repo_url for project '{project}' (not in catalog projects_info). Use --repo-url URL for PROJECT@SHA.", file=sys.stderr)
        sys.exit(1)
    if not is_valid_repo_url(repo_url):
        print("Invalid repo_url: only https:// or git@ URLs are allowed.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(os.path.join(project_dir, ".git")):
        print(f"Cloning {project}...")
        run_git(["clone", repo_url, project_dir], work_dir)
    else:
        print(f"Fetching {project}...")
        run_git(["fetch", "origin"], project_dir)

    run_git(["checkout", commit], project_dir)
    print(f"Checked out {project} at {commit} ({'fixed' if args.fixed else 'buggy'})")
    print(f"Work dir: {project_dir}")


if __name__ == "__main__":
    main()
