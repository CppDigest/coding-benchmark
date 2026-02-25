# BugSwarm C/C++ CI Subset

Tooling and data for the **BugSwarm** benchmark filtered to **C/C++ CI artifacts**: reproducible fail–pass build pairs in Docker.

**Important — no C/C++ subset at present:** The BugSwarm REST API dataset is **Java- and Python-focused**. There are **no C/C++ artifacts** in the API today. Therefore `data/cpp_artifacts.json` will always have **`artifact_count: 0`** and **`artifacts: []`** when you run the script. The acceptance criteria below mention "50+ C/C++ artifacts" as a **target when the API provides them**; that target is not met with the current dataset. This repo provides the tooling and schema so that when BugSwarm (or a future source) adds C/C++ artifacts, we can fetch and use them.

## Layout

- **scripts/**
  - `download_dataset.py` — Fetch full BugSwarm dataset (reproducible artifacts), filter for C/C++ in Python, write `data/cpp_artifacts.json`. Same pattern as Child 1/2: one Python script fetches and filters the dataset.
  - `download_artifact.py` — Pull Docker image for one artifact: `--artifact-id <image_tag>`.
- **data/**
  - `full_artifacts.json` — Full dataset (all reproducible artifacts from API). Written by `python3 scripts/download_dataset.py`.
  - `cpp_artifacts.json` — C/C++ subset (filtered from full). **Currently always 0 artifacts**; same script writes both.
- **evaluation/**
  - `reproduce_ci.py` — Reproduce fail or pass job in container: `--artifact-id <id> --job fail|pass`.
- **docs/**
  - `methodology.md` — Research Q&A, Docker structure, replication plan.

## Quick start (Python + download dataset)

**Default behavior: fetch all from the BugSwarm REST API, then filter for C/C++.** The script does not limit the number of artifacts fetched; it requests every reproducible artifact (`reproduce_successes > 0`) and then filters that full list in Python.

```bash
cd external/bugswarm
pip install -r scripts/requirements.txt
python3 scripts/download_dataset.py --include-build-system
```

Use `--skip-log-fetch` for a faster run (skips per-artifact log URL fetches; `fail_log_path` will be empty). **Fetch only C/C++ from API:** add `--filter-cpp-api` so the API returns only artifacts with `lang` in C/C++/Cpp (one small request, no Python lang filter). **Without a token:** use `--max-pages 1` (and optionally `--filter-cpp-api`) to avoid rate limit. Optional: `BUGSWARM_API_TOKEN=xxx` for full fetch without rate limit.

This fetches the BugSwarm dataset and writes:
- `data/full_artifacts.json` — all reproducible artifacts (or first N pages with `--max-pages`)
- `data/cpp_artifacts.json` — C/C++ subset; **currently 0** because the API has no C/C++ artifacts

**Confirming the result:** Re-run the script to verify. If you see `artifact_count: 0` in `cpp_artifacts.json`, the script will print the **lang** and **build_system** distribution from the API (top 20) so you can confirm there are no C/C++ artifacts in the current dataset. The BugSwarm REST API dataset is currently Java/Python-focused; C/C++ count will stay 0 until such artifacts exist in the API.

**Optional — run without API (fixture only):** If you cannot call the API (no token, rate-limited, or CI), you can use `--input-json` with a small fixture. This **does not** fetch from the API; it only runs the filter on the given JSON. For the real pipeline you must run **without** `--input-json` so the script fetches all artifacts from the API and then filters. Fixture example:

```bash
cd external/bugswarm
python scripts/download_dataset.py --input-json fixtures/sample_artifacts.json
```

Expected: `Loaded 5 artifacts from ... (no API call).` → `Wrote full dataset (5 artifacts)` → `No C/C++ artifacts matched.` → `Langs in dataset (top 20): {'Java': 3, 'Python': 2}` → `Wrote 0 C/C++ artifacts to data/cpp_artifacts.json`. The file `data/cpp_artifacts.json` will have `"artifact_count": 0` and `"artifacts": []`.

Then pull and run an artifact:

```bash
python3 scripts/download_artifact.py --artifact-id <image_tag>
python3 evaluation/reproduce_ci.py --artifact-id <image_tag> --job fail
```

## Acceptance criteria (Child Issue 3)

- **50+ C/C++ artifacts** in `data/cpp_artifacts.json` is the **target when the API provides C/C++**. **Right now there is no C/C++ subset:** the BugSwarm API has 0 C/C++ artifacts (dataset is Java/Python only), so `cpp_artifacts.json` will always have `artifact_count: 0`. Run `python3 scripts/download_dataset.py --max-pages 1 --filter-cpp-api --skip-log-fetch` to confirm; the script reports 0 C/C++ from the API.
- **Pull:** `python3 scripts/download_artifact.py --artifact-id <id>`.
- **Reproduce:** `python3 evaluation/reproduce_ci.py --artifact-id <id> --job fail` (or `--job pass`).
- **Metadata:** each artifact has `image_tag`, `repo`, `fail_commit`, `pass_commit`, `fail_log_path` (see `download_dataset.py`).

## Docker

Images: **bugswarm/cached-images** on Docker Hub; tag = artifact `image_tag`. Override: `BUGSWARM_IMAGE_REPO` or `--image-repo`.

## References

- [BugSwarm](https://www.bugswarm.org/) · [REST API](https://www.bugswarm.org/docs/toolset/bugswarm-rest-api/) · [Anatomy of an artifact](https://www.bugswarm.org/docs/dataset/anatomy-of-an-artifact/)
