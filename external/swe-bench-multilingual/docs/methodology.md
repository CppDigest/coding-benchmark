# Methodology: SWE-Bench Multilingual and Replication Plan

This document covers (A) how SWE-Bench mines and constructs benchmark instances, (B) reproducibility controls for our use of the dataset, and (C) a replication plan for building similar benchmarks for Boost and Clang.

---

## A) How SWE-Bench mines issues

SWE-Bench (and by extension SWE-Bench Multilingual) builds benchmarks from real GitHub issues and pull requests. The following describes the general methodology; Multilingual extends it to non-Python repos and multiple languages.

### Issue selection criteria

- **Linked PR:** Only issues that are explicitly resolved by a **merged** pull request are considered.
- **Test relevance:** The fixing PR must modify **test-related files** (or add/change tests), so that success can be measured by test outcomes.
- **Execution-based validation:** Candidate instances are validated by applying the fix and running the test suite: at least one test must transition from fail-to-pass (F2P), and no previously passing test may regress (P2P).

### Repository selection logic

- **Original SWE-bench:** Focused on 12 popular Python repositories.
- **SWE-bench Multilingual:** Expands to 42 repositories across 9 languages (C, C++, Go, Java, JavaScript, TypeScript, PHP, Ruby, Rust), chosen to include real-world, test-heavy projects.

### Bug-to-commit linkage process

1. **Scraping:** Collect merged pull requests from the target repositories.
2. **Issue–PR link:** Retain only PRs that reference and close a specific issue (e.g. “Fixes #123”).
3. **Commit pairing:** For each such PR:
   - **Base (buggy) state:** The parent commit of the merge (or the commit before the fix is applied).
   - **Fix state:** The merge commit (or the commit containing the fix).
4. **Gold patch:** The diff between base and fix is the **gold patch** stored in the dataset.

### How gold patches are generated

- Gold patches are the **unified diffs** produced by the version control system (e.g. `git diff base_commit fix_commit` or equivalent from the merged PR).
- They are stored in the `patch` field of each instance and used as reference; evaluation is primarily test-based (F2P/P2P), not patch-equality-based.

---

## B) Reproducibility controls

### Installation and environment setup

Use a Python virtual environment (venv) so dependencies are isolated and reproducible.

**Prerequisites**

- **Python:** 3.10 or newer (`python --version`).
- **Git:** For cloning the repo and (for replication) mining commits.
- **Internet:** Required for downloading the dataset and pip packages.

**Windows (PowerShell)**

From the project root (e.g. `coding-benchmark`):

```powershell
# Create venv in repo root (or under external/swe-bench-multilingual if working only there)
python -m venv .venv

# Activate the venv
.\.venv\Scripts\Activate.ps1
```

If script execution is blocked:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then install dependencies:

```powershell
pip install --upgrade pip
pip install -r external/swe-bench-multilingual/requirements.txt
# Or explicitly:
# pip install datasets huggingface_hub pyarrow
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
pip install --upgrade pip
pip install -r external/swe-bench-multilingual/requirements.txt
```

**Verify**

```powershell
python -c "import datasets, pyarrow; print('OK')"
```

After setup, run scripts with the venv activated so that `python` and `pip` refer to the venv. See the project README for download and filter commands.

### Commit pinning and dataset version

- **Dataset:** We do **not** use the `main` branch of the Hugging Face dataset. We pin a specific **revision (commit hash)** and record it in the table below.
- **Download script:** `download.py` requires `--revision <commit_hash>` so every run fetches the same dataset snapshot.
- **Manifest:** Each download produces a `manifest.json` with `dataset_id`, `revision`, `downloaded_at_utc`, and `splits`, so the exact snapshot is traceable.

**Dataset version pinning (record the revision you use):**

| Field | Value |
|-------|--------|
| **DATASET_ID** | `SWE-bench/SWE-bench_Multilingual` |
| **DATASET_REVISION** | e.g. `2b7aced941b4873e9cad3e76abbae93f481d1beb` (from Hugging Face → Files and versions) |
| **DATE_SELECTED** | YYYY-MM-DD |
| **DOWNLOADED_BY** | (your name) |

**How to obtain and use a revision:** Open [SWE-bench/SWE-bench_Multilingual](https://huggingface.co/datasets/SWE-bench/SWE-bench_Multilingual) on Hugging Face → **Files and versions** or **History** → copy the full commit hash. Run the download script with that revision (from repo root, venv activated): `python external\swe-bench-multilingual\scripts\download.py --revision <commit_hash>`.

### Environment assumptions

- **Python:** 3.10+.
- **Dependencies:** `datasets`, `huggingface_hub`, `pyarrow` (see `requirements.txt` in this repo).
- **OS:** Instructions are written for Windows (PowerShell); the script itself is cross-platform.
- **Network:** One-time download from Hugging Face; no manual clicking once the revision is chosen and the script is run.

### Determinism guarantees

- **Download:** For a given `--revision`, `load_dataset(... revision=args.revision)` returns the same data. Parquet files and manifest are deterministic for that revision.
- **Dataset authors:** Any determinism guarantees of the benchmark (e.g. test order, container image) are documented by the SWE-bench project; we rely on their evaluation harness and container setup for run-to-run consistency when running evaluations (out of scope for Child Issue 1).

---

## C) Replication plan for Boost and Clang

The following is a step-by-step plan so another engineer can replicate a SWE-bench-style benchmark for **Boost** and **Clang** without further coordination.

---

### Boost

**Goal:** Produce a set of instances (issue, base commit, fix commit, gold patch, test info) for the Boost libraries.

1. **Mine closed issues labeled “bug”**
   - Source: GitHub (e.g. `boostorg/<library>`) or Boost’s Trac/Jira if still in use.
   - Filter: closed issues with a “bug” (or equivalent) label.

2. **Identify fixing commits**
   - For each closed bug, find the PR or commit that closed it (e.g. “Fixes #N” or reference in commit message).
   - Use `git log --all --oneline --grep="issue\|fix\|#N"` and/or GitHub API to link issue → merge commit.

3. **Extract parent (buggy) and fix commit**
   - **Base commit:** Parent of the fixing commit (or the commit before the fix branch was merged).
   - **Fix commit:** The commit that contains the fix (e.g. merge commit or tip of the PR branch).
   - Store: `base_commit`, `fix_commit`, and `gold_patch = git diff base_commit fix_commit`.

4. **Confirm tests exist**
   - Ensure the fix is covered by existing tests or that the fixing commit adds/updates tests.
   - If no test changes and no failing test becomes passing, the instance may be unsuitable for execution-based evaluation.

5. **Record build and test commands**
   - Per repo or per library: document how to configure and build (e.g. `b2`, CMake) and how to run the test suite (e.g. `b2 test`, `ctest`, or library-specific runner).
   - Store in a machine-readable form (e.g. YAML/JSON) with fields: `repo`, `build_cmd`, `test_cmd`, `env` (e.g. compiler, C++ standard).

**Deliverables:** Table or dataset of (instance_id, repo, base_commit, fix_commit, gold_patch, problem_statement, build_cmd, test_cmd).

---

### Clang (LLVM/Clang)

**Goal:** Produce a set of instances for Clang (and optionally other LLVM subprojects), linking bugs to fixing commits and regression tests.

1. **Mine bug tracker or GitHub issues**
   - **LLVM/Clang:** bugs.llvm.org (Bugzilla) and/or GitHub issues (e.g. `llvm/llvm-project`).
   - Filter: resolved bugs that have an associated code fix (patch or commit).

2. **Link issue to fixing commit**
   - In Bugzilla: use “Commit” field or “Reviews” to find the commit that fixed the bug.
   - On GitHub: use “Fixes llvm/llvm-project#N” and branch/PR → main to get the fixing commit.
   - Store: `issue_id`, `fixing_commit`, and optionally `review_url`.

3. **Extract regression test additions**
   - Many Clang fixes add or modify tests under `clang/test/` (or similar). Identify added/updated test files and the test command (e.g. `lit`, or specific run lines in tests).
   - **Base commit:** Parent of the fixing commit. **Gold patch:** diff from base to fixing commit.
   - Record which tests are fail-to-pass (new or previously failing tests that pass after the fix).

4. **Record build and test commands**
   - **Build:** Document how to build LLVM/Clang (e.g. CMake + ninja, specific configure options). Pin compiler and CMake version if possible.
   - **Test:** Document how to run the relevant tests (e.g. `ninja check-clang`, or `lit` on a subset of tests). Per-instance test lists can be stored for efficiency.
   - Store: `build_cmd`, `test_cmd`, `test_list` (optional), `env`.

**Deliverables:** Table or dataset of (instance_id, component, base_commit, fix_commit, gold_patch, problem_statement, test_files_added_or_modified, build_cmd, test_cmd).

---

### Cross-cutting for both

- **Schema:** Align with SWE-bench-style fields where possible (`instance_id`, `repo`/`component`, `base_commit`, `problem_statement`, `patch`, build/test metadata) so that the same evaluation harness or a small adapter can be used.
- **Version pinning:** Pin repo revision (and optionally submodules) when exporting instances so that “download at revision X” is reproducible.
- **Documentation:** For each project (Boost, Clang), maintain a short doc similar to `schema.md` (what each field means, how success is defined, known limitations).

This replication plan is intended to be self-contained so that another engineer can execute it without coordination.
