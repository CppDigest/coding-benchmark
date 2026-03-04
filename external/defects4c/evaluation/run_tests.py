#!/usr/bin/env python3
"""
Run tests for a Defects4C bug.
Usage: python run_tests.py --bug-id PROJECT@SHA [--work-dir DIR] [--build-first] [--trusted]
Uses test_cmd from bug_catalog.json; if empty, tries default (make check / ctest).
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys

# Reuse validation from checkout_bug to avoid path traversal and keep logic in one place.
_defects4c_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_scripts_dir = os.path.join(_defects4c_root, "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
from checkout_bug import sanitize_project
from catalog import load_catalog, find_bug

DEFAULT_TIMEOUT = 60


def _run_cmd(cmd: str, cwd: str, trusted: bool, label: str) -> int:
    """Run a build or test command with optional shell=True and a timeout."""
    if not cmd:
        print(f"{label} command is empty", file=sys.stderr)
        return 1
    try:
        if trusted:
            # Trusted mode: allow shell=True but still enforce a timeout.
            result = subprocess.run(cmd, shell=True, cwd=cwd, timeout=DEFAULT_TIMEOUT)
            return result.returncode
        # Default: run with shell=False using shlex.split for quoted args.
        argv = shlex.split(cmd)
        if not argv:
            print(f"{label} command is empty after parsing", file=sys.stderr)
            return 1
        result = subprocess.run(argv, cwd=cwd, timeout=DEFAULT_TIMEOUT)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"{label} timed out after {DEFAULT_TIMEOUT}s", file=sys.stderr)
        return 124


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    default_work_dir = os.path.join(base_dir, "repos")

    parser = argparse.ArgumentParser(description="Run tests for a Defects4C bug")
    parser.add_argument("--bug-id", required=True, help="Bug ID, e.g. libxml2@commit_sha or PROJECT-1")
    parser.add_argument("--work-dir", default=default_work_dir, help="Parent directory for project clones")
    parser.add_argument("--build-first", action="store_true", help="Run build_cmd before test_cmd")
    parser.add_argument(
        "--trusted",
        action="store_true",
        help="Allow executing catalog build_cmd/test_cmd with shell=True; otherwise run with shell=False and a timeout.",
    )
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
        rc = _run_cmd(build_cmd, project_dir, args.trusted, "Build")
        if rc != 0:
            print("Build failed", file=sys.stderr)
            sys.exit(rc)

    print("Running tests:", test_cmd)
    rc = _run_cmd(test_cmd, project_dir, args.trusted, "Test")
    sys.exit(rc)


if __name__ == "__main__":
    main()

