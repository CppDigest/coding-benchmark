# BugSwarm C/C++ CI Subset

Tooling and data for the **BugSwarm** benchmark filtered to **C/C++ CI artifacts**: reproducible fail–pass build pairs in Docker.

## Layout

- **scripts/**
  - `download_dataset.py` — Fetch full BugSwarm dataset (reproducible artifacts), filter for C/C++ in Python, write `data/cpp_artifacts.json`. Same pattern as Child 1/2: one Python script fetches and filters the dataset.
  - `download_artifact.py` — Pull Docker image for one artifact: `--artifact-id <image_tag>`.
- **data/**
  - `full_artifacts.json` — Full dataset (all reproducible artifacts from API). Written by `python3 scripts/download_dataset.py`.
  - `cpp_artifacts.json` — C/C++ subset (filtered from full). Same script writes both.
- **evaluation/**
  - `reproduce_ci.py` — Reproduce fail or pass job in container: `--artifact-id <id> --job fail|pass`.
- **docs/**
  - `methodology.md` — Research Q&A, Docker structure, replication plan.

## Quick start (Python + download dataset)

```bash
cd external/bugswarm
pip install -r scripts/requirements.txt
python3 scripts/download_dataset.py --include-build-system
```

This fetches the full BugSwarm dataset and writes:
- `data/full_artifacts.json` — all reproducible artifacts
- `data/cpp_artifacts.json` — filtered C/C++ subset (currently 0; API is Java/Python-focused)

Optional: `BUGSWARM_API_TOKEN=xxx` for higher rate limit.

Then pull and run an artifact:

```bash
python3 scripts/download_artifact.py --artifact-id <image_tag>
python3 evaluation/reproduce_ci.py --artifact-id <image_tag> --job fail
```

## Acceptance criteria (Child Issue 3)

- **50+ C/C++ artifacts** in `data/cpp_artifacts.json` when the API provides them.
- **Pull:** `python3 scripts/download_artifact.py --artifact-id <id>`.
- **Reproduce:** `python3 evaluation/reproduce_ci.py --artifact-id <id> --job fail` (or `--job pass`).
- **Metadata:** each artifact has `image_tag`, `repo`, `fail_commit`, `pass_commit`, `fail_log_path` (see `download_dataset.py`).

## Docker

Images: **bugswarm/cached-images** on Docker Hub; tag = artifact `image_tag`. Override: `BUGSWARM_IMAGE_REPO` or `--image-repo`.

## References

- [BugSwarm](https://www.bugswarm.org/) · [REST API](https://www.bugswarm.org/docs/toolset/bugswarm-rest-api/) · [Anatomy of an artifact](https://www.bugswarm.org/docs/dataset/anatomy-of-an-artifact/)
