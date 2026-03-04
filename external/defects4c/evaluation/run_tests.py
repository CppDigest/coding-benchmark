#!/usr/bin/env python3
"""
Run tests for a Defects4C bug.
Usage: python run_tests.py --bug-id PROJECT@SHA [--work-dir DIR] [--build-first]
Uses test_cmd from bug_catalog.json; if empty, tries default (make check / ctest).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

# Reuse validation from checkout_bug to avoid path traversal and keep logic in one place
_defects4c_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_scripts_dir = os.path.join(_defects4c_root, "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
from checkout_bug import sanitize_project

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


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    default_work_dir = os.path.join(base_dir, "repos")

    parser = argparse.ArgumentParser(description="Run tests for a Defects4C bug")
    parser.add_argument("--bug-id", required=True, help="Bug ID, e.g. libxml2@commit_sha or PROJECT-1")
    parser.add_argument("--work-dir", default=default_work_dir, help="Parent directory for project clones")
    parser.add_argument("--build-first", action="store_true", help="Run build_cmd before test_cmd")
    args = parser.parse_args()

    catalog = load_catalog(data_dir)
    bug = find_bug(catalog, args.bug_id)
    if not bug and "@" in args.bug_id:
        project = args.bug_id.split("@", 1)[0]
        # No build_cmd default; catalog or user must provide. test_cmd fallback is best-effort.
        bug = {"bug_id": args.bug_id, "project": project, "test_cmd": "make check", "build_cmd": ""}
    if not bug:
        print(f"Bug not found: {args.bug_id}", file=sys.stderr)
        sys.exit(1)

    project_raw = bug.get("project")
    if not project_raw or not isinstance(project_raw, str) or not project_raw.strip():
        print(
            f"Bug entry has missing or invalid 'project' (bug_id={bug.get('bug_id', args.bug_id)!r}). "
            "Check bug_catalog.json.",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        project = sanitize_project(project_raw.strip())
    except ValueError as e:
        print(f"{e}. Check bug_catalog.json.", file=sys.stderr)
        sys.exit(1)
    project_dir = os.path.join(os.path.abspath(args.work_dir), project)
    if not os.path.isdir(project_dir):
        print(f"Project dir not found: {project_dir}. Run checkout_bug.py first.", file=sys.stderr)
        sys.exit(1)

    build_cmd = (bug.get("build_cmd") or "").strip()
    test_cmd = (bug.get("test_cmd") or "make check").strip()

    if args.build_first and build_cmd:
        print("Building:", build_cmd)
        rc = subprocess.run(build_cmd, shell=True, cwd=project_dir)
        if rc.returncode != 0:
            print("Build failed", file=sys.stderr)
            sys.exit(rc.returncode)

    print("Running tests:", test_cmd)
    rc = subprocess.run(test_cmd, shell=True, cwd=project_dir)
    sys.exit(rc.returncode)


if __name__ == "__main__":
    main()
