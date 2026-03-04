#!/usr/bin/env python3
from __future__ import annotations

import json
import os


def load_catalog(data_dir: str) -> dict:
    """Load bug_catalog.json from the given data directory."""
    path = os.path.join(data_dir, "bug_catalog.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Catalog not found: {path}. Run setup.sh first.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_bug(catalog: dict, bug_id: str) -> dict | None:
    """Find a bug by full bug_id or short form PROJECT-N."""
    for b in catalog.get("bugs", []):
        if b.get("bug_id") == bug_id:
            return b
        short = f"{b.get('project')}-{b.get('version', '')}".rstrip("-")
        if short == bug_id:
            return b
    return None

