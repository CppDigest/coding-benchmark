#!/usr/bin/env python3
"""
Fetch full BugSwarm dataset from the REST API, write full list, then filter for C/C++.

Default: fetch ALL reproducible artifacts from the API (reproduce_successes > 0), then filter.
1. Fetch full reproducible-artifact list (no limit; entire dataset).
2. Write full dataset to data/full_artifacts.json (normalized).
3. Filter in Python for C/C++: lang in ("C", "C++", "C/C++", "Cpp") or
   build_system in ("CMake", "Makefile", "make") when --include-build-system.
4. Write C/C++ subset to data/cpp_artifacts.json.

Use --max-pages N to fetch only the first N pages from the API (avoids rate limit when no token).
Use --input-json only when you cannot call the API (e.g. CI); then the script only runs the filter on the file.

Usage:
  python download_dataset.py [--output PATH] [--token TOKEN] [--include-build-system] [--skip-log-fetch]
  BUGSWARM_API_TOKEN=xxx python download_dataset.py
  python download_dataset.py --skip-log-fetch   # faster; no per-artifact log URL fetch
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import base64
from urllib.error import HTTPError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

# BugSwarm REST API (Eve-style: paginated with _items and _links.next). Filter uses MongoDB-style JSON.
BUGSWARM_ARTIFACTS_BASE = os.environ.get(
    "BUGSWARM_API_BASE", "http://www.api.bugswarm.org"
).rstrip("/")
ARTIFACTS_FILTER = '{"reproduce_successes":{"$gt":0}}'
# Request only C/C++ from the API (fewer results, one small request when using --max-pages)
ARTIFACTS_FILTER_CPP = '{"reproduce_successes":{"$gt":0},"lang":{"$in":["C","C++","C/C++","Cpp","cpp"]}}'


def fetch_artifacts_limited_pages(
    max_pages: int,
    token: str = "",
    api_filter: str | None = None,
) -> list[dict] | None:
    """Fetch up to the first max_pages pages of artifacts from the API. Returns list of raw artifact dicts or None on error."""
    filter_str = api_filter or ARTIFACTS_FILTER
    results = []
    url = f"{BUGSWARM_ARTIFACTS_BASE}/v1/artifacts?where={quote(filter_str)}"
    headers = {"Accept": "application/json"}
    if token:
        auth = base64.b64encode(f"{token}:".encode()).decode()
        headers["Authorization"] = f"Basic {auth}"

    for page_num in range(max_pages):
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
        except HTTPError as e:
            print(f"API error: {e.code} {e.reason}", file=sys.stderr)
            if e.code == 429:
                print("Rate limited. Use BUGSWARM_API_TOKEN or --max-pages 1 and retry later.", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Request error: {e}", file=sys.stderr)
            return None

        items = data.get("_items") or []
        results.extend(items)
        print(f"Page {page_num + 1}: got {len(items)} artifacts (total so far: {len(results)}).", file=sys.stderr)
        if not items:
            break
        try:
            next_href = data["_links"]["next"]["href"]
            url = urljoin(url, next_href)
        except (KeyError, TypeError):
            break

    return results


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
    parser.add_argument(
        "--skip-log-fetch",
        action="store_true",
        help="Do not fetch build log URLs (faster run; fail_log_path will be empty)",
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        default=None,
        help="Use this JSON file (array of raw artifact dicts) instead of API; for CI/reproducible run without token",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        metavar="N",
        help="Fetch only first N pages from API (e.g. 1 to avoid rate limit without token); default is all pages",
    )
    parser.add_argument(
        "--filter-cpp-api",
        action="store_true",
        help="Ask API for C/C++ artifacts only (lang in C/C++/Cpp); fewer results, no Python filter needed for lang",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    bugswarm_root = script_dir.parent
    default_output = bugswarm_root / "data" / "cpp_artifacts.json"
    out_path = args.output or default_output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    api = None
    if args.input_json is not None:
        # Reproducible run from fixture (no API)
        path = args.input_json if args.input_json.is_absolute() else (script_dir / args.input_json)
        if not path.exists():
            print(f"Input file not found: {path}", file=sys.stderr)
            return 1
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        all_artifacts = data if isinstance(data, list) else data.get("artifacts", data.get("data", []))
        print(f"Loaded {len(all_artifacts)} artifacts from {path} (no API call).", file=sys.stderr)
    elif args.max_pages is not None and args.max_pages >= 1:
        # Fetch only first N pages (fewer requests, avoids rate limit)
        token = (args.token or "").strip()
        api_filter = ARTIFACTS_FILTER_CPP if args.filter_cpp_api else None
        all_artifacts = fetch_artifacts_limited_pages(
            max_pages=args.max_pages,
            token=token,
            api_filter=api_filter,
        )
        if all_artifacts is None:
            return 1
        kind = "C/C++" if args.filter_cpp_api else "reproducible"
        print(f"Fetched {len(all_artifacts)} {kind} artifacts (first {args.max_pages} page(s)).", file=sys.stderr)
    else:
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
        api_filter = ARTIFACTS_FILTER_CPP if args.filter_cpp_api else ARTIFACTS_FILTER
        if args.filter_cpp_api:
            print("Fetching C/C++ artifacts from API (lang in C/C++/Cpp)...", file=sys.stderr)
        else:
            print("Fetching full BugSwarm artifact list (reproduce_successes > 0)...", file=sys.stderr)
        try:
            all_artifacts = api.filter_artifacts(api_filter)
        except Exception as e:
            print(f"API error: {e}", file=sys.stderr)
            return 1
        kind = "C/C++" if args.filter_cpp_api else "reproducible"
        print(f"Fetched {len(all_artifacts)} {kind} artifacts.", file=sys.stderr)

    # 2. Write full dataset (normalized) to data/full_artifacts.json
    full_path = bugswarm_root / "data" / "full_artifacts.json"
    full_path.parent.mkdir(parents=True, exist_ok=True)
    use_api = api if (api is not None and not args.skip_log_fetch) else None
    normalize = lambda a: normalize_artifact(a, use_api)
    full_list = [normalize(a) for a in all_artifacts]
    full_list.sort(key=lambda x: (x.get("repo", ""), x.get("image_tag", "")))
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": "BugSwarm REST API (all reproducible artifacts)",
            "artifact_count": len(full_list),
            "artifacts": full_list,
        }, f, indent=2)
    print(f"Wrote full dataset ({len(full_list)} artifacts) to {full_path}", file=sys.stderr)

    # 3. Filter for C/C++ in Python (case-insensitive; lang is C/C++/Cpp or build is CMake/make)
    def is_cpp(a: dict) -> bool:
        lang = (a.get("lang") or "").strip()
        build = (a.get("build_system") or "").strip().lower()
        if lang:
            lu = lang.upper()
            if lu in ("C", "C++", "C/C++", "CPP") or "c++" in lang.lower() or lang.lower() == "cpp":
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
        artifacts.append(normalize(a))

    artifacts.sort(key=lambda x: (x.get("repo", ""), x.get("image_tag", "")))

    if len(artifacts) == 0:
        from collections import Counter
        langs = Counter((a.get("lang") or "?") for a in all_artifacts)
        builds = Counter((a.get("build_system") or "?") for a in all_artifacts)
        print("No C/C++ artifacts matched.", file=sys.stderr)
        print("Langs in dataset (top 20): %s" % dict(langs.most_common(20)), file=sys.stderr)
        print("Build systems in dataset (top 20): %s" % dict(builds.most_common(20)), file=sys.stderr)
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
    if api is None:
        return ""
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
