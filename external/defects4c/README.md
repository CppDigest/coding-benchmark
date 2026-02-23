# Defects4C integration (Child Issue 2)

Wrappers and catalog for the [Defects4C](https://github.com/defects4c/defects4c) C/C++ program repair benchmark. Same pattern as SWE-Bench (Child Issue 1): **fetch full dataset** into `data/`, then checkout and run tests.

## Quick start

```bash
# 1) Fetch full dataset (cve.list.csv + per-project bugs_list_new.json from upstream GitHub)
python scripts/download_dataset.py

# Or run full setup (clone upstream + download dataset)
bash scripts/setup.sh

# 2) Checkout a bug (full id: PROJECT@SHA, or short id: PROJECT-1, PROJECT-2, ...)
python scripts/checkout_bug.py --bug-id PROJECT@SHA
# Or: python scripts/checkout_bug.py --bug-id ARMmbed___mbedtls-1

# 3) Run tests for that bug
python evaluation/run_tests.py --bug-id PROJECT@SHA
# Or: python evaluation/run_tests.py --bug-id ARMmbed___mbedtls-1
```

## Layout

| Path | Purpose |
|------|--------|
| `scripts/setup.sh` | Clone upstream + run download_dataset.py to fill catalog |
| `scripts/download_dataset.py` | **Fetch full dataset** from Defects4C GitHub (cve.list.csv + bugs_list_new.json per project) → `data/bug_catalog.json` |
| `scripts/checkout_bug.py` | Checkout buggy (or fixed) version by `--bug-id PROJECT@SHA` or **`PROJECT-1`** (short id) |
| `data/bug_catalog.json` | Bug catalog: project, buggy_commit, fixed_commit, test_cmd, build_cmd |
| `evaluation/run_tests.py` | Run tests for a bug (`test_cmd` from catalog); accepts `--bug-id PROJECT@SHA` or **`PROJECT-1`** |
| `docker/Dockerfile` | Slim image with git, build tools, and scripts |
| `docs/methodology.md` | Defects4C methodology and Boost/Clang replication plan |

## Docker

From repo root:

```bash
docker build -f external/defects4c/docker/Dockerfile external/defects4c -t defects4c-env
docker run --rm -it -v "$(pwd)/external/defects4c/repos:/repos" defects4c-env bash
# Then inside: python /app/scripts/checkout_bug.py --bug-id PROJECT@SHA --work-dir /repos
# Or: python /app/scripts/checkout_bug.py --bug-id PROJECT-1 --work-dir /repos
```

## Bug ID format

- **Full id:** `project@commit_sha` (e.g. `curl___curl@1890d59905414ab84a35892b2e45833654aa5c13`).
- **Short id:** `PROJECT-N` where N is the 1-based index for that project in the catalog (e.g. `ARMmbed___mbedtls-1`, `libgd___libgd-3`). Enables the acceptance criterion: checkout and run tests with a single `--bug-id PROJECT-1` style command.

Populate `data/bug_catalog.json` by running `python scripts/download_dataset.py` (or `bash scripts/setup.sh`). The catalog includes a `version` field per bug so short ids work.

## Environment

- **checkout_bug.py** works on Windows and Linux (requires `git`).
- **run_tests.py** runs `test_cmd`/`build_cmd` from the catalog (e.g. `make check`). On Windows you need a Unix-like environment (e.g. Git Bash with make, WSL, or use the Docker image).
