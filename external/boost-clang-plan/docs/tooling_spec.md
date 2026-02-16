# Tooling Specifications (Boost/Clang Benchmark)

This document lists all required tools, dependencies, and environment specifications for implementing the Boost and Clang benchmark creation plans.

---

## 1. Core (shared by both Boost and Clang)

| Tool | Version (min) | Purpose |
|------|----------------|--------|
| **Python** | 3.9+ | Mining scripts, validation runner, lit (Clang) |
| **Git** | 2.x | Clone, checkout by commit, log/blame for mining |
| **Docker** | 20.x+ (Engine + Compose optional) | Reproducible build and test environment |
| **GitHub CLI** (`gh`) | 2.x | Optional; issue/PR listing and run logs |
| **curl / wget** | Any | Download artifacts, API calls if not using Python `requests` |

### Python dependencies (for mining and validation scripts)

- `requests` — HTTP for GitHub/Bugzilla APIs  
- `PyGithub` (optional) — GitHub API wrapper for issue/PR mining  
- For Clang: Python 3 used by **lit** (LLVM test runner); no extra pip deps for lit if using LLVM tree  

Suggested `requirements.txt` (for scripts in `scripts/`):

```
requests>=2.28.0
PyGithub>=2.0.0
```

---

## 2. Boost-specific

| Tool | Version (min) | Purpose |
|------|----------------|--------|
| **B2 (Boost.Build)** | 4.x | Build and run Boost tests for B2-based libs |
| **CMake** | 3.16+ | Build and test for CMake-based Boost libs |
| **C++ compiler** | GCC 10+ or Clang 10+ or MSVC 2019+ | Build Boost (match CI where possible) |
| **Make or Ninja** | — | CMake generator; Ninja recommended |

### Environment

- **Boost source:** Full Boost tree (e.g. `boostorg/boost`) or boost.workspace-style layout so that `libs/<name>` and B2/CMake find dependencies.
- **Optional:** Pre-installed Boost (e.g. system or vcpkg) for libs that support it; document in each case’s `build_cmd` if used.

### Docker (Boost)

- Base image: e.g. `ubuntu:22.04` or `ubuntu:24.04`.
- Packages: `build-essential`, `cmake`, `ninja-build`, `python3`, `git`. For B2: include Boost.Build (e.g. from Boost tree or install script).
- Document compiler (e.g. `gcc-11`) and B2/CMake versions in the Dockerfile or image tag.

---

## 3. Clang-specific

| Tool | Version (min) | Purpose |
|------|----------------|--------|
| **CMake** | 3.20+ | Configure LLVM/Clang |
| **Ninja** | 1.10+ | Build LLVM/Clang (recommended) |
| **C++ compiler** | GCC 9+ or Clang 10+ | Host compiler for building LLVM/Clang |
| **Python 3** | 3.6+ | Required by lit (LLVM test runner) |
| **lit** | (bundled in LLVM) | Run `clang/test/` tests; use from LLVM tree |
| **FileCheck** | (bundled in LLVM) | Used by lit tests; built with LLVM |

### Environment

- **LLVM monorepo:** e.g. `llvm/llvm-project`. Clone (full or sparse) so that `clang/`, `llvm/`, and `cmake/` are present.
- **Build:** Out-of-tree build; document `LLVM_ENABLE_PROJECTS=clang` and any `LLVM_TARGETS_TO_BUILD` used.

### Docker (Clang)

- Base image: e.g. `ubuntu:22.04`.
- Packages: `cmake`, `ninja-build`, `build-essential`, `python3`, `git`.
- No need to pre-install LLVM; clone and build inside container (or mount) per validation script.

---

## 4. APIs and external services

| Service | Use | Auth |
|---------|-----|------|
| **GitHub REST API** | List issues, PRs, commits, workflow runs | Token for higher rate limits (optional for small repos) |
| **GitHub GraphQL** | Same; use if needed for complex queries | Token |
| **LLVM Bugzilla** | Query bugs (product=clang, status=RESOLVED/FIXED) | None for read-only |
| **reviews.llvm.org (Phabricator)** | Historical; commit messages reference Differential Revisions | Read-only |

---

## 5. Script templates (in `scripts/`)

The following templates are provided; implementers fill in placeholders and add logic as in the Boost/Clang plans.

| Script | Depends on | Purpose |
|--------|------------|---------|
| `mine_github_issues.py.template` | Python, `requests` or `PyGithub`, Git | Query GitHub for closed issues (e.g. label=bug), link to PRs/commits; output candidate list (e.g. CSV/JSONL). |
| `extract_bug_fixes.py.template` | Python, Git | Scan git history for fix commits (message patterns); output buggy_commit, fixed_commit pairs; optional test behavior check. |
| `generate_test_cases.py.template` | Python, optional B2/CMake/lit | From a list of (repo, buggy_commit, fixed_commit), derive test_cmd/build_cmd or test_file/build_target; output records matching dataset schema. |

All scripts should be runnable with the core tooling above; Boost- or Clang-specific steps (B2, lit) only when generating Boost/Clang cases.

---

## 6. Validation runner (not a template; to be implemented)

- **Input:** Dataset (JSONL or JSON) of cases.
- **Actions:** For each case, checkout `buggy_commit`, run build + test → expect fail; checkout `fixed_commit`, run build + test → expect pass.
- **Depends on:** Git, Docker (or pinned host), and either Boost (B2/CMake) or Clang (CMake + Ninja + lit) as appropriate.
- **Output:** Per-case pass/fail and summary (e.g. “buggy fails / fixed passes” rate).

---

## 7. Summary checklist

- [ ] Python 3.9+, Git, Docker
- [ ] Boost: B2 and/or CMake, C++ compiler, Boost source tree
- [ ] Clang: CMake, Ninja, C++ compiler, LLVM monorepo (with lit)
- [ ] Optional: GitHub CLI, PyGithub, Bugzilla access
- [ ] Script templates filled and wired to dataset schema
- [ ] Dockerfiles for Boost and Clang validation environments
