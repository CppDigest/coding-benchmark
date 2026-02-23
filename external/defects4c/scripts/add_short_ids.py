#!/usr/bin/env python3
"""
Add or refresh per-project short ids (version 1, 2, 3, ...) in data/bug_catalog.json.
Enables checkout and run_tests with: --bug-id PROJECT-1, PROJECT-2, etc.
Run from external/defects4c or repo root. Idempotent.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    path = os.path.join(base_dir, "data", "bug_catalog.json")
    if not os.path.isfile(path):
        print(f"Not found: {path}", flush=True)
        return
    with open(path, encoding="utf-8") as f:
        catalog = json.load(f)
    bugs = catalog.get("bugs", [])
    version_per_project: dict[str, int] = defaultdict(int)
    for b in bugs:
        p = b.get("project", "")
        version_per_project[p] += 1
        b["version"] = version_per_project[p]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
    print(f"Added short ids to {len(bugs)} bugs in {path}", flush=True)


if __name__ == "__main__":
    main()
