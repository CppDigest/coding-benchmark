#!/usr/bin/env python3
"""
Fetch full Defects4C dataset from upstream GitHub (same pattern as SWE-Bench Child Issue 1).
Downloads cve.list.csv and per-project bugs_list_new.json, builds data/bug_catalog.json.
Run from external/defects4c or repo root. Requires: requests (pip install requests).
"""
import csv
import json
import os
import re
import sys
try:
    import requests
except ImportError:
    requests = None

BASE_URL = "https://raw.githubusercontent.com/defects4c/defects4c/master/defectsc_tpl/projects"
# project name (owner___repo) -> repo URL for clone
REPO_URL_MAP = {
    "ARMmbed___mbedtls": "https://github.com/ARMmbed/mbedtls.git",
    "CauldronDevelopmentLLC___cbang": "https://github.com/CauldronDevelopmentLLC/cbang.git",
    "ClusterLabs___libqb": "https://github.com/ClusterLabs/libqb.git",
    "DaveGamble___cJSON": "https://github.com/DaveGamble/cJSON.git",
    "OpenIDC___cjose": "https://github.com/OpenIDC/cjose.git",
    "PCRE2Project___pcre2": "https://github.com/PCRE2Project/pcre2.git",
    "VirusTotal___yara": "https://github.com/VirusTotal/yara.git",
    "Yeraze___ytnef": "https://github.com/Yeraze/ytnef.git",
    "bblanchon___ArduinoJson": "https://github.com/bblanchon/ArduinoJson.git",
    "curl___curl": "https://github.com/curl/curl.git",
    "dlundquist___sniproxy": "https://github.com/dlundquist/sniproxy.git",
    "jqlang___jq": "https://github.com/jqlang/jq.git",
    "libgd___libgd": "https://github.com/libgd/libgd.git",
    "libuv___libuv": "https://github.com/libuv/libuv.git",
    "lua___lua": "https://github.com/lua/lua.git",
    "mdadams___jasper": "https://github.com/mdadams/jasper.git",
    "mongodb___mongo-c-driver": "https://github.com/mongodb/mongo-c-driver.git",
    "nginx___njs": "https://github.com/nginx/njs.git",
    "php___php-src": "https://github.com/php/php-src.git",
    "redis___hiredis": "https://github.com/redis/hiredis.git",
    "redis___redis": "https://github.com/redis/redis.git",
    "sqlite___sqlite": "https://github.com/sqlite/sqlite.git",
    "the-tcpdump-group___tcpdump": "https://github.com/the-tcpdump-group/tcpdump.git",
    "uriparser___uriparser": "https://github.com/uriparser/uriparser.git",
    "webmproject___libvpx": "https://github.com/webmproject/libvpx.git",
    "wez___atomicparsley": "https://github.com/wez/atomicparsley.git",
    "yhirose___cpp-peglib": "https://github.com/yhirose/cpp-peglib.git",
    "znc___znc": "https://github.com/znc/znc.git",
}


def project_from_github_url(url: str) -> str | None:
    """Convert https://github.com/owner/repo/commit/sha -> owner___repo"""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/", url)
    if m:
        return f"{m.group(1)}___{m.group(2)}"
    return None


def main():
    if not requests:
        print("pip install requests", file=sys.stderr)
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, "bug_catalog.json")

    catalog = {
        "source": "https://github.com/defects4c/defects4c",
        "bug_id_format": "project@commit_sha",
        "projects_info": {},
        "bugs": [],
    }
    seen_bug_ids = set()

    # 1) Fetch CVE list CSV
    print("Fetching cve.list.csv...")
    try:
        r = requests.get(f"{BASE_URL}/cve.list.csv", timeout=30)
        r.raise_for_status()
        text = r.text
    except Exception as e:
        print(f"Failed to fetch cve.list.csv: {e}", file=sys.stderr)
    else:
        for row in csv.DictReader(text.splitlines()):
            url = (row.get("url") or "").strip()
            if not url:
                continue
            # url = https://github.com/owner/repo/commit/SHA
            m = re.match(r".*/([0-9a-f]{40})$", url)
            if not m:
                continue
            sha = m.group(1)
            proj = project_from_github_url(url)
            if not proj:
                continue
            bug_id = f"{proj}@{sha}"
            if bug_id in seen_bug_ids:
                continue
            seen_bug_ids.add(bug_id)
            catalog["bugs"].append({
                "bug_id": bug_id,
                "project": proj,
                "buggy_commit": sha,
                "fixed_commit": sha,
                "test_cmd": "make test" if "curl" in proj else "make check",
                "build_cmd": "./configure && make",
            })
            if proj not in catalog["projects_info"] and proj in REPO_URL_MAP:
                catalog["projects_info"][proj] = {"repo_url": REPO_URL_MAP[proj], "build_system": "autotools"}

    # 2) List project dirs and fetch bugs_list_new.json for each
    print("Fetching project bug lists...")
    try:
        r = requests.get("https://api.github.com/repos/defects4c/defects4c/contents/defectsc_tpl/projects", timeout=30)
        r.raise_for_status()
        entries = r.json()
    except Exception as e:
        print(f"Failed to list projects: {e}", file=sys.stderr)
        entries = []
    for ent in entries:
        name = ent.get("name", "")
        if not name or name.startswith(".") or not ent.get("type") == "dir":
            continue
        if name in ("cve.list.csv", "d.py", "workflow_tpl.jinja", "workflow_cmake_rebuild_tpl.jinja"):
            continue
        proj = name
        try:
            r2 = requests.get(f"{BASE_URL}/{proj}/bugs_list_new.json", timeout=15)
            if r2.status_code != 200:
                continue
            bugs_list = r2.json()
        except Exception:
            continue
        if not isinstance(bugs_list, list):
            continue
        for b in bugs_list:
            commit_before = b.get("commit_before")
            commit_after = b.get("commit_after")
            if not commit_after:
                continue
            bug_id = f"{proj}@{commit_after}"
            if bug_id in seen_bug_ids:
                continue
            seen_bug_ids.add(bug_id)
            catalog["bugs"].append({
                "bug_id": bug_id,
                "project": proj,
                "buggy_commit": commit_before,
                "fixed_commit": commit_after,
                "test_cmd": "make test" if "curl" in proj else "make check",
                "build_cmd": "./configure && make",
            })
        if proj not in catalog["projects_info"] and proj in REPO_URL_MAP:
            catalog["projects_info"][proj] = {"repo_url": REPO_URL_MAP[proj], "build_system": "autotools"}

    # Ensure we have projects_info for any project that appears in bugs
    for b in catalog["bugs"]:
        p = b.get("project")
        if p and p not in catalog["projects_info"] and p in REPO_URL_MAP:
            catalog["projects_info"][p] = {"repo_url": REPO_URL_MAP[p], "build_system": "autotools"}

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
    print(f"Wrote {len(catalog['bugs'])} bugs to {out_path}")
    print(f"Projects: {len(catalog['projects_info'])}")


if __name__ == "__main__":
    main()
