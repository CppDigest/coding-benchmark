#!/usr/bin/env python3
"""
Fetch full BugSwarm dataset from the REST API, write full list, then filter for C/C++.

1. Fetch full reproducible-artifact list (reproduce_successes > 0).
2. Write full dataset to data/full_artifacts.json (normalized).
3. Filter in Python for C/C++: lang in ("C", "C++", "C/C++") or
   build_system in ("CMake", "Makefile", "make") when --include-build-system.
4. Write C/C++ subset to data/cpp_artifacts.json.

Usage:
  python download_dataset.py [--output PATH] [--token TOKEN] [--include-build-system]
  BUGSWARM_API_TOKEN=xxx python download_dataset.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Download C/C++ BugSwarm artifact list to cpp_artifacts.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: data/cpp_artifacts.json under script repo root)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=os.environ.get("BUGSWARM_API_TOKEN", ""),
        help="BugSwarm API token for higher rate limit (optional)",
    )
    parser.add_argument(
        "--include-build-system",
        action="store_true",
        help="Also include artifacts with C/C++-related build systems (e.g. CMake) if lang filter yields few results",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    bugswarm_root = script_dir.parent
    default_output = bugswarm_root / "data" / "cpp_artifacts.json"
    out_path = args.output or default_output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from bugswarm.common.rest_api.database_api import DatabaseAPI
    except ImportError:
        print("Install bugswarm-common: pip install bugswarm-common", file=sys.stderr)
        return 1

    token = (args.token or "").strip()
    if token:
        api = DatabaseAPI(token=token)
    else:
        api = DatabaseAPI()  # unauthenticated (rate limited)

    # 1. Fetch full dataset (all reproducible artifacts)
    print("Fetching full BugSwarm artifact list (reproduce_successes > 0)...", file=sys.stderr)
    try:
        all_artifacts = api.filter_artifacts('{"reproduce_successes":{"$gt":0}}')
    except Exception as e:
        print(f"API error: {e}", file=sys.stderr)
        return 1
    print(f"Fetched {len(all_artifacts)} reproducible artifacts.", file=sys.stderr)

    # 2. Write full dataset (normalized) to data/full_artifacts.json
    full_path = bugswarm_root / "data" / "full_artifacts.json"
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_list = [normalize_artifact(a, api) for a in all_artifacts]
    full_list.sort(key=lambda x: (x.get("repo", ""), x.get("image_tag", "")))
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": "BugSwarm REST API (all reproducible artifacts)",
            "artifact_count": len(full_list),
            "artifacts": full_list,
        }, f, indent=2)
    print(f"Wrote full dataset ({len(full_list)} artifacts) to {full_path}", file=sys.stderr)

    # 3. Filter for C/C++ in Python (case-insensitive; lang contains C or build is CMake/make)
    def is_cpp(a: dict) -> bool:
        lang = (a.get("lang") or "").strip()
        build = (a.get("build_system") or "").strip().lower()
        if lang and (lang.upper() in ("C", "C++", "C/C++") or "c++" in lang.lower()):
            return True
        if args.include_build_system and build in ("cmake", "makefile", "make"):
            return True
        return False

    artifacts = []
    seen: set[str] = set()
    for a in all_artifacts:
        if not is_cpp(a):
            continue
        image_tag = (a.get("image_tag") or a.get("current_image_tag") or "").strip()
        if not image_tag or image_tag in seen:
            continue
        seen.add(image_tag)
        artifacts.append(normalize_artifact(a, api))

    artifacts.sort(key=lambda x: (x.get("repo", ""), x.get("image_tag", "")))

    if len(artifacts) == 0:
        from collections import Counter
        langs = Counter((a.get("lang") or "?") for a in all_artifacts)
        builds = Counter((a.get("build_system") or "?") for a in all_artifacts)
        print("No C/C++ artifacts matched. Langs in dataset: %s" % dict(langs.most_common(15)), file=sys.stderr)
        print("Build systems in dataset: %s" % dict(builds.most_common(15)), file=sys.stderr)
        print("(BugSwarm dataset is currently Java/Python-focused; C/C++ catalog will populate when such artifacts exist.)", file=sys.stderr)

    catalog = {
        "source": "BugSwarm REST API (fetch all reproducible, filter for C/C++)",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
    print(f"Wrote {len(artifacts)} C/C++ artifacts to {out_path}")
    return 0


def get_failure_log_path(api, failed_job_id: str) -> str:
    """Return failure log URL/path for a job via API get_build_log, or canonical BugSwarm log URL."""
    job_id = (failed_job_id or "").strip()
    if not job_id:
        return ""
    try:
        resp = api.get_build_log(job_id)
        if getattr(resp, "ok", False) and getattr(resp, "url", None):
            return resp.url
        # Fallback: canonical BugSwarm log URL
        return f"https://www.bugswarm.org/artifact-logs/{job_id}/"
    except Exception:
        return f"https://www.bugswarm.org/artifact-logs/{job_id}/"


def normalize_artifact(raw: dict, api) -> dict:
    """Produce a single artifact entry with required fields for our harness."""
    failed = raw.get("failed_job") or {}
    passed = raw.get("passed_job") or {}
    image_tag = (raw.get("image_tag") or raw.get("current_image_tag") or "").strip()
    repo = (raw.get("repo") or "").strip()
    failed_job_id = str(failed.get("job_id") or "")
    return {
        "image_tag": image_tag,
        "repo": repo,
        "lang": raw.get("lang") or "Unknown",
        "build_system": raw.get("build_system") or "NA",
        "fail_commit": failed.get("trigger_sha") or failed.get("base_sha") or "",
        "pass_commit": passed.get("trigger_sha") or passed.get("base_sha") or "",
        "failed_job_id": failed_job_id,
        "passed_job_id": str(passed.get("job_id") or ""),
        "fail_log_path": get_failure_log_path(api, failed_job_id),
        "reproduce_successes": raw.get("reproduce_successes"),
        "reproducibility_status": (raw.get("reproducibility_status") or {}).get("status"),
        "ci_service": raw.get("ci_service") or "travis",
    }


if __name__ == "__main__":
    sys.exit(main())
