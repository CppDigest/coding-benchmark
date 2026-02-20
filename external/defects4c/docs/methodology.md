# Defects4C methodology and replication plan

This document covers (A) how Defects4C is built and used, (B) how to run our wrappers and Docker, and (C) a replication plan for Boost and Clang.

---

## Research questions answered (Child Issue 2)

| Question | Answer |
|----------|--------|
| **What is the official source for Defects4C?** | **GitHub:** [https://github.com/defects4c/defects4c](https://github.com/defects4c/defects4c). Docs: [https://defects4c.github.io](https://defects4c.github.io). |
| **How many bugs/projects are included?** | **248** verified buggy functions, **102** vulnerable functions, **9M+** bug-relevant commits. Multiple C/C++ projects including libxml2, openssl, curl, nginx, apache (and others in the full benchmark). |
| **What is the structure of each bug entry?** | Each entry has: **buggy version** = commit SHA (buggy state); **fixed version** = commit or patch that fixes it; **test cases** = project test suite or specific test command. Our catalog uses: `bug_id`, `project`, `buggy_commit`, `fixed_commit`, `test_cmd`, `build_cmd`. |
| **How do I checkout a specific buggy/fixed version programmatically?** | Run: `python scripts/checkout_bug.py --bug-id PROJECT@SHA` (buggy) or add `--fixed` for the fixed version. Script clones the project repo and runs `git checkout <commit>`. See § B) Checkout a bug. |
| **What build systems are used?** | **Make** (and Autotools: `./configure && make`), **CMake**, and project-specific config (e.g. OpenSSL, nginx). Per-project `build_system` and `build_cmd` are in `data/bug_catalog.json` (`projects_info` and per-bug `build_cmd`). |
| **What command-line interface does Defects4C provide?** | **Upstream:** HTTP API (list defects, get defect, build patch, run fix verification). **This repo:** Python CLI — `download_dataset.py` (fetch full catalog from GitHub), `checkout_bug.py` (checkout by bug-id), `run_tests.py` (run tests by bug-id). |
| **How do I run the test suite for a specific bug to verify fixes?** | Run: `python evaluation/run_tests.py --bug-id PROJECT@SHA`. Use `--build-first` to run `build_cmd` before `test_cmd`. Tests are defined per bug in the catalog (`test_cmd`). See § B) Run tests. |
| **What are the system requirements?** | **Compilers:** gcc/clang; **build:** make, CMake (for some projects), Autotools (configure); **runtime:** git, Python 3; **optional:** Docker for reproducible environment. See § System requirements below. |
| **Is there a Docker image available?** | **Yes.** (1) **Upstream:** Defects4C repo has `docker_dirs/Dockerfile` (oss-fuzz-style base, compilers, deps). (2) **This repo:** `external/defects4c/docker/Dockerfile` — slim image with git, build-essential, Python, and our scripts. Build: `docker build -f external/defects4c/docker/Dockerfile external/defects4c`. |

---

## A) Defects4C benchmark

### Official source

- **Repository:** [https://github.com/defects4c/defects4c](https://github.com/defects4c/defects4c)
- **Documentation / API:** [https://defects4c.github.io](https://defects4c.github.io), [API docs](https://defects4c.github.io/api.html)
- **Scale:** 248 verified buggy functions, 102 vulnerable functions, 9M+ bug-relevant commits (training). Real C/C++ projects (e.g. libxml2, openssl, curl, nginx, apache).

### Bug mining process

- **Source of bugs:** Real-world C/C++ repositories and CVE-related fixes.
- **Selection:** Human-validated buggy (and vulnerable) functions with associated test cases so that:
  - The buggy version fails at least one test (reproducible failure).
  - The fixed version passes the same tests (fix verification).
- **Fix granularity:** Single-line, single-hunk, or single-function fixes; used for repair and infill-style evaluation.

### Bug–fix pair extraction

- Each entry links:
  - **Buggy version:** Commit (or function snapshot) that exhibits the defect.
  - **Fixed version:** Commit (or patch) that fixes it.
- Defects4C uses a **bug_id** format: `project@commit_sha` (e.g. `libxml2@a1b2c3d...`). The commit is the buggy state; the fix is either a sibling commit or a patch applied on top.

### Test case requirements (reproducibility)

- A bug is **reproducible** when:
  1. There is a defined **test command** (e.g. `make check`, project test suite).
  2. On the **buggy** version, at least one test **fails**.
  3. On the **fixed** version, that test **passes** and no previously passing test regresses.
- Defects4C provides test cases (or references to project test suites) so that repair tools can be evaluated by running these tests before and after applying a fix.

### Build system handling

- Projects use different build systems (Make, Autotools, CMake, project-specific config).
- Defects4C documents or encodes **build_cmd** and **test_cmd** per project/bug so that:
  - The same commands can be run in a container or host environment.
  - Our catalog stores `build_cmd` and `test_cmd` in `bug_catalog.json` for each bug (or project default).

### CLI and API

- **API:** Defects4C offers an HTTP API (e.g. list defects, get defect info, build patch, run fix verification). See `http_tutorial.py` in the upstream repo.
- **Local use:** We provide Python wrappers: `download_dataset.py` (fetch full catalog from upstream GitHub), `checkout_bug.py` (checkout buggy/fixed version), and `run_tests.py` (run test command).

### Docker

- Upstream provides a Docker setup under `docker_dirs/` (based on oss-fuzz-style images, with compilers and dependencies).
- We provide a **slim Dockerfile** under `external/defects4c/docker/` that includes git, build tools, and our scripts so you can run checkout and tests inside a container. For full Defects4C pipeline (e.g. API services), use the upstream repository and Docker instructions.

### System requirements

- **Compilers:** gcc and/or clang (project-dependent).
- **Build tools:** make; for some projects: CMake, Autotools (`autoconf`, `automake`, `libtool`), or project-specific config (e.g. OpenSSL’s `Configure`, nginx’s `configure`).
- **Version control:** git (for cloning and checking out buggy/fixed commits).
- **Python:** Python 3 for our scripts (`download_dataset.py`, `checkout_bug.py`, `run_tests.py`); `requests` for download_dataset.py.
- **Reproducible runs:** Use the provided Docker image so compilers and dependencies match; upstream’s full image includes LLVM/Clang and other toolchain pieces when needed.

---

## B) Using this wrapper

### Setup

```bash
# From repo root
cd external/defects4c
bash scripts/setup.sh
```

This clones the Defects4C repo and optionally refreshes `data/bug_catalog.json` from the API. The catalog must contain at least `project`, `buggy_commit`, and (for fixed checkout) `fixed_commit`; `test_cmd` and `build_cmd` can be set per bug or left to defaults.

### Checkout a bug

```bash
python scripts/checkout_bug.py --bug-id PROJECT@SHA
# Or short form if in catalog: --bug-id PROJECT-1
# Fixed version: --bug-id PROJECT@SHA --fixed
```

This clones the project (if needed) into `repos/<project>` and checks out the given commit.

### Run tests

```bash
python evaluation/run_tests.py --bug-id PROJECT@SHA
# Optional: --build-first to run build_cmd before test_cmd
```

Uses `test_cmd` from the catalog (or default `make check`).

### Docker

Build (from repo root):

```bash
docker build -f external/defects4c/docker/Dockerfile external/defects4c -t defects4c-env
```

Run with a volume for cloned repos:

```bash
docker run --rm -it -v "$(pwd)/external/defects4c/repos:/repos" defects4c-env bash
# Inside container:
python /app/scripts/checkout_bug.py --bug-id PROJECT@SHA --work-dir /repos
python /app/evaluation/run_tests.py --bug-id PROJECT@SHA --work-dir /repos
```

---

## C) Replication plan for Boost and Clang

### Boost

1. **Identify bug-fixing commits**  
   For each Boost library (e.g. `boostorg/<library>`): use `git log` (and optionally GitHub API) to find commits that fix bugs (e.g. “Fixes #N”, “fix bug”, “resolve issue”).

2. **Extract parent (buggy) and child (fixed) commits**  
   - **Buggy:** Parent of the fixing commit (or the commit before the fix is applied).  
   - **Fixed:** The fixing commit.  
   Store `buggy_commit` and `fixed_commit` (and optionally `gold_patch = git diff buggy_commit fixed_commit`).

3. **Verify test existence**  
   Ensure the library has tests that:
   - **Fail** on `buggy_commit`.
   - **Pass** on `fixed_commit`.  
   If the fix does not touch tests, confirm at least one existing test is failing on the buggy version and passing on the fixed version.

4. **Document build and test commands**  
   Per library (or per bug): record `build_cmd` (e.g. `b2`, CMake, or library-specific) and `test_cmd` (e.g. `b2 test`, `ctest`). Store in a catalog (e.g. JSON) with fields: `project`, `bug_id`, `buggy_commit`, `fixed_commit`, `test_cmd`, `build_cmd`.

**Deliverable:** A Boost bug catalog and scripts (or integration with this wrapper) so that `checkout_bug.py` and `run_tests.py` can run for Boost entries.

---

### Clang (LLVM/Clang)

1. **Mine LLVM bug tracker**  
   Use [bugs.llvm.org](https://bugs.llvm.org) (Bugzilla) and/or GitHub issues (e.g. `llvm/llvm-project`) to find **resolved** bugs that have an associated code fix (commit or patch).

2. **Link bug reports to fixing commits**  
   From Bugzilla: use the “Commit” field or “Reviews” to get the commit that fixed the bug. From GitHub: use “Fixes llvm/llvm-project#N” and the merged PR to get the fixing commit.

3. **Extract regression tests**  
   Many Clang fixes add or change tests under `clang/test/`. Record which tests were added or modified and how to run them (e.g. `lit`, or specific `ninja check-clang` targets).

4. **Document LLVM/Clang build and test**  
   Record:
   - **Build:** How to build LLVM/Clang (e.g. CMake + ninja, required options). Pin compiler/CMake versions if possible.
   - **Test:** How to run the relevant tests (e.g. `ninja check-clang`, or `lit` on a subset).  
   Store in a catalog with `buggy_commit`, `fixed_commit`, `test_cmd`, `build_cmd`, and optionally `test_list` or test paths.

**Deliverable:** A Clang bug catalog and integration with this wrapper so that each Clang bug can be checked out and tested with a single command.

---

### Cross-cutting

- **Catalog schema:** Use the same shape as Defects4C where possible: `project`, `bug_id`, `buggy_commit`, `fixed_commit`, `test_cmd`, `build_cmd`. That allows reuse of `checkout_bug.py` and `run_tests.py` with a shared catalog format.
- **Version pinning:** Pin repository and submodule revisions when exporting bugs so that “checkout at revision X” is reproducible.
- **Documentation:** For Boost and Clang, keep a short doc (like this one) that describes how bugs were mined, how tests are run, and any known limitations.

This replication plan is intended to be self-contained so that another engineer can execute it without coordination.
