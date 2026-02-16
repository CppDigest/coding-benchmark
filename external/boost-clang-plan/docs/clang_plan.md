# Clang Benchmark Creation Plan

## 1. Repository Analysis

### 1.1 LLVM monorepo structure

- **Single repo:** LLVM is a monorepo (e.g. `llvm-project` on GitHub: `llvm/llvm-project`). Clang lives under `clang/` (frontend, driver, libraries). Other components: `llvm/`, `lld/`, etc.
- **Clone (shallow for speed):**

```bash
git clone --depth 1 https://github.com/llvm/llvm-project.git
# Or: git clone --filter=blob:none --sparse https://github.com/llvm/llvm-project.git
# git sparse-checkout set clang llvm cmake
```

### 1.2 Clang-specific directories

- **Paths:** `clang/` (driver, frontend), `clang/lib/` (libraries, e.g. Basic, Lex, Parse, Sema, CodeGen), `clang/test/` (lit tests). Headers under `clang/include/clang/`.
- **Components:** Frontend (parsing, AST), Sema (semantic analysis), CodeGen (IR generation), Driver (invocation). Use these as `component` or `category` in the dataset.

### 1.3 Test infrastructure (lit, FileCheck)

- **lit:** LLVM’s test runner; tests live in `clang/test/` with `.c`, `.cpp`, `.m` and `RUN:` lines. Run with `lit` (e.g. `python path/to/llvm/utils/lit/lit.py clang/test/...`).
- **FileCheck:** Many tests use `FileCheck` to validate output (e.g. `// RUN: %clang_cc1 ... | FileCheck %s`). The test “passes” if the RUN line succeeds and FileCheck matches.
- **Targets:** `ninja check-clang`, `ninja check-clang-frontend`, `ninja check-clang-sema`, etc. Use these as `build_target` or in `test_cmd` for reproducibility.

## 2. Issue Mining Strategy

### 2.1 LLVM Bug tracker

- **Bugzilla:** [bugs.llvm.org](https://bugs.llvm.org). Query: Product = `clang`, Status = `RESOLVED` or `FIXED`, Component = Clang (or subcomponents). Export or use API to get bug IDs and summaries.
- **GitHub Issues:** `llvm/llvm-project` has GitHub Issues; filter by labels (e.g. `bug`, `clang`) and state `closed`. Prefer issues that reference a commit or PR that fixed them.
- **Linking:** Many bugs are closed with a commit message “Fix PR12345” or “Fixes https://bugs.llvm.org/show_bug.cgi?id=12345”. Use that to get (bug_id, fix_commit) pairs.

### 2.2 Git history analysis

- **Commit message patterns:** `git log --grep="Fix" --grep="Fixes" --grep="PR" --oneline -- clang/`. Identify commits that reference a bug ID or PR.
- **Differential (Phabricator):** Historical reviews are on reviews.llvm.org; commits often have “Differential Revision: https://…”. Use commit message and diff to get buggy vs fixed state (parent vs commit).
- **Release notes:** LLVM release notes list bug fixes; use them to get bug IDs and then find the fixing commit.

**Example:**

```bash
git log --oneline --all -- clang/ | head -100
git show <fix_commit>^ --stat   # parent = buggy
git show <fix_commit> --stat    # fixed
```

## 3. Test Case Extraction

- **lit format:** Tests under `clang/test/` use `RUN:` to specify command (e.g. `%clang_cc1`, `%clang`). Extract the path to the test file and the lit invocation (or the `ninja check-clang-*` target that runs it).
- **FileCheck:** No change to extraction; the test is the `.cpp`/`.c` file plus RUN/FileCheck. The “test case” for the benchmark is “run this lit test” (or the subset of tests added/modified in the fix).
- **Regression tests added with fixes:** For each fix commit, diff test directory: new or modified files in `clang/test/` are the regression tests. Record `test_file` (path) and the minimal lit target or `ninja` target that runs it.

**Example:**

```bash
ninja check-clang-sema  # runs Sema tests
# Or run a single test:
lit clang/test/Sema/array.c
```

## 4. Build System Handling

- **CMake:** LLVM/Clang uses CMake. Standard configure and build:

```bash
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DLLVM_ENABLE_PROJECTS=clang ../llvm
ninja -C build
```

- **Ninja:** Use Ninja for fast incremental builds. Document the exact CMake options (e.g. `LLVM_ENABLE_PROJECTS=clang`, optional `LLVM_TARGETS_TO_BUILD=host`).
- **Minimal build targets:** To speed iteration, build only what’s needed for the tests (e.g. `ninja clang check-clang-sema`). In the dataset, record the minimal target set (e.g. `check-clang-sema` or a specific test path) so the validation pipeline doesn’t build the entire project unnecessarily (or document a “minimal” config that still runs the chosen tests).

## 5. Dataset Format

- **JSON schema (aligned with other benchmarks):** One object per case; store as JSONL or JSON array.

Required fields:

- `component` — e.g. `frontend`, `sema`, `codegen`, `driver`
- `bug_id` — LLVM bug ID (e.g. issue number or “PR12345”) or string id
- `buggy_commit` — SHA where the bug is present (parent of fix, or pre-fix)
- `fixed_commit` — SHA that fixes the bug
- `test_file` — path to the lit test file (e.g. `clang/test/Sema/array.c`) or the test name
- `build_target` — ninja target that runs the test (e.g. `check-clang-sema`) or the lit path

Metadata:

- `category` — `frontend` | `sema` | `codegen` | `driver` (or finer)
- `repo` — e.g. `llvm/llvm-project`
- `difficulty` — optional
- `lines_changed` — optional

**Example:**

```json
{
  "component": "sema",
  "bug_id": "12345",
  "buggy_commit": "abc123",
  "fixed_commit": "def456",
  "test_file": "clang/test/Sema/cxx-sizeof.cpp",
  "build_target": "check-clang-sema",
  "repo": "llvm/llvm-project",
  "category": "sema"
}
```

## 6. Validation Pipeline

- **lit integration:** For each case, checkout `buggy_commit`, configure and build (minimal target), run the test (e.g. `ninja <build_target>` or `lit <test_file>`) → expect failure. Checkout `fixed_commit`, same steps → expect pass.
- **Build verification:** Ensure the configured build (CMake + Ninja) succeeds at both commits for the required target. Document compiler and CMake version in the Docker spec.
- **Docker:** Provide a Dockerfile (or image) with LLVM/Clang build environment (CMake, Ninja, compiler). Example:

```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y cmake ninja-build build-essential python3 git
WORKDIR /workspace
# Clone llvm-project (or mount); then cmake + ninja as above
```

- **Harness contract:** Evaluation runner takes a case, checks out `buggy_commit`, runs the test target → expect fail; checks out `fixed_commit`, runs the same → expect pass. Report pass/fail per case.

## 7. Estimated Counts

- **Target:** 100–200 high-quality issues for the first release.
- **Distribution across components:** Aim for coverage of frontend, Sema, CodeGen, and driver (e.g. 25–50 each). Prefer issues that have a clear regression test.
- **Complexity distribution:** Mix of one-file fixes (easy), multi-file or multi-component (medium), and subtle or build-related (hard). Plan to mine 2–3× candidates and filter to 100–200 after validation (buggy fails / fixed passes and test stability).
