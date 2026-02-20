# Boost Benchmark Creation Plan

## 1. Repository Analysis

### 1.1 List of Boost libraries to include

Start with libraries that have clear CI, tests, and active maintenance. Suggested initial set (configurable):

- **Core/utilities:** Boost.Algorithm, Boost.Utility, Boost.ThrowException  
- **Containers/iterators:** Boost.Container, Boost.Iterator  
- **Asio/Beast:** Boost.Asio, Boost.Beast (CI and test coverage)  
- **JSON:** Boost.JSON  
- **Optional/ Variant/ Any:** Boost.Optional, Boost.Variant, Boost.Any  

Expand using the same criteria: has GitHub repo (or well-defined subtree), CI (GitHub Actions or other), and test suite (Boost.Test or similar).

**Concrete command to list candidate libraries (from Boost super-project or manifest):**

```bash
# From boostorg/boost or boost-workspace–style layout
git clone --depth 1 https://github.com/boostorg/boost.git boost.repo
ls boost.repo/libs/
# Or use boostdep / manifest to list libraries and dependencies
```

### 1.2 GitHub repository structure

- **Layout:** Most Boost libraries live under `https://github.com/boostorg/<library>`. Some use a single super-project with `libs/<name>`.
- **Relevant paths:** `libs/<name>/`, `.github/workflows/`, `test/` or `tests/`, `example/`. Build: often B2 (`Jamfile`, `Jamfile.v2`) and/or CMake (`CMakeLists.txt`).
- **Convention:** Issues and PRs on GitHub; fixes often land via PR with linked issue.

### 1.3 CI/CD pipeline analysis (GitHub Actions, etc.)

- **Discovery:** Per-repo `.github/workflows/*.yml`. Identify jobs that run tests (e.g. matrix: compiler, OS).
- **Artifacts to capture:** Workflow run ID, job name(s), failing step, log excerpt, `base_sha`, and the commit/PR that fixed it (`gold_merge_sha`).
- **Example query (GitHub CLI):**

```bash
gh run list --repo boostorg/beast --limit 50
gh run view <run-id> --repo boostorg/beast --log-failed
```

- **Pattern:** Find runs with `conclusion: failure`, then find a later run or PR that fixes the same branch → defines a fail→pass pair.

## 2. Issue Mining Strategy

### 2.1 GitHub Issues

- **API queries:** Use GitHub REST/GraphQL or `gh` to list closed issues with labels like `bug`, `bugfix`, or no label but with “fix” in title/body.
- **Link issues to PRs/commits:** Via “merged” PRs that reference the issue (`Fixes #N`, `Closes #N`) or that are linked in the issue.
- **Filtering criteria:**
  - Has an associated merged PR (or clear fix commit).
  - Description is sufficient to understand the bug (no “fixed” with no context).
  - Prefer issues where the PR adds or modifies a test (so we have a test_cmd or test target).
- **Example (Python with PyGithub):**

```python
# Pseudocode
repo = g.get_repo("boostorg/beast")
issues = repo.get_issues(state="closed", labels=["bug"])
for i in issues:
    prs = [pr for pr in i.get_timeline_events() if pr.event == "closed" and pr.commit_id]
    if prs and has_test_change(prs[0]):
        candidates.append({"issue_id": i.number, "pr": prs[0], "repo": repo.full_name})
```

### 2.2 Git history analysis

- **Bug-fix commit patterns:** Commits with messages like “Fix …”, “Fixes #123”, “Resolve …”, “Correct …”.
- **Parent–child pairs:** For each such commit `C`, treat `C^` (parent) as buggy and `C` as fixed. Optionally restrict to commits that touch at least one test file or that are linked to an issue.
- **Verify test behavior:** For each pair, run test_cmd (or the test target used in CI) at `C^` (expect fail) and at `C` (expect pass). Discard pairs where this does not hold.

**Example:**

```bash
git log --oneline --grep="Fix" -- libs/beast/
git show <commit>^:libs/beast/test/...
```

## 3. Test Case Extraction

- **Boost.Test framework:** Tests use `BOOST_TEST`, `BOOST_CHECK_*`, etc. Locate test files (e.g. under `test/` or `tests/`) and the runner (single binary or per-suite).
- **Identifying tests added with bug fixes:** Diff the fix commit vs parent: new or modified `*test*.cpp` or `*Test*.cpp`; parse or heuristically extract the test binary/target from B2 or CMake.
- **Standalone test runners:** For each case, record the minimal command that runs the relevant test (e.g. `b2 libs/beast/test/<target>` or `ctest -R <test_name>`). Prefer one command per case for reproducibility.

**B2 example:**

```bash
cd /path/to/boost
./b2 libs/beast/test/beast/unit/http/parser  # or the specific test target
```

**CMake example:**

```bash
cd build && ctest -R "Beast.*Http.*Parser" -V
```

## 4. Build System Handling

- **B2 (Boost.Build):** Default for many Boost libs. Document the minimal `b2` invocation (e.g. `b2 -j4 libs/<lib>/test/...` or a specific target). Use a fixed toolchain (e.g. `gcc`, `msvc`) in the spec.
- **CMake:** Newer or dual-build libs. Document `cmake -B build`, `cmake --build build`, and how to run tests (`ctest` or the test binary). Specify generator (Ninja recommended).
- **Dependency management:** If a library depends on other Boost libs, use a full Boost checkout or a manifest (e.g. boost.workspace) so that the same revisions are used in Docker and in the dataset spec.

## 5. Dataset Format

- **JSON schema (per case):** One JSON object per case; store as JSONL for streaming or a single JSON array.

Required fields:

- `library` — e.g. `beast`, `json`, `algorithm`
- `issue_id` — GitHub issue number or a string id
- `buggy_commit` — SHA of the commit where the bug exists (parent of fix, or pre-PR merge)
- `fixed_commit` — SHA of the commit that fixes the bug (merge commit or fix commit)
- `test_cmd` — Command(s) to run the relevant test (string or list of strings)
- `build_cmd` — Command(s) to build the library/test target (optional if test_cmd builds and runs)

Metadata (optional but recommended):

- `difficulty` — e.g. `easy` | `medium` | `hard` (from lines_changed or manual)
- `category` — e.g. `bug`, `regression`, `ci`
- `lines_changed` — number of lines in the fix patch
- `repo` — full repo name, e.g. `boostorg/beast`
- `pr_number` — PR that fixed the issue

**Example minimal JSON:**

```json
{
  "library": "beast",
  "issue_id": "1234",
  "buggy_commit": "abc123",
  "fixed_commit": "def456",
  "test_cmd": "cd $BOOST_ROOT && ./b2 -j4 libs/beast/test/beast/unit/http/parser",
  "build_cmd": "./b2 -j4 libs/beast/test/beast/unit/http/parser",
  "repo": "boostorg/beast",
  "difficulty": "medium",
  "lines_changed": 15
}
```

## 6. Validation Pipeline

- **Automated verification:** For each case in the catalog:
  1. Checkout repo at `buggy_commit`, run `build_cmd` then `test_cmd` → must fail (or tests fail).
  2. Checkout repo at `fixed_commit`, run `build_cmd` then `test_cmd` → must pass.
- **Build reproducibility:** Run the same steps inside a Docker image (same OS, compiler, B2/CMake version) and record success/failure. Optionally run multiple times to detect flakiness.
- **Docker environment:** Provide a Dockerfile (or image name) that includes Boost (or boost.workspace), B2, and optionally CMake. Document compiler and version (e.g. gcc-11, clang-14). Example:

```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y build-essential cmake ninja-build python3 git
# Clone Boost or mount; install b2 if needed
WORKDIR /workspace
```

- **Harness contract:** The evaluation runner accepts a case (from the JSON), checks out `buggy_commit`, runs test_cmd → expect non-zero exit or “fail”; checks out `fixed_commit`, runs test_cmd → expect zero exit. Report pass/fail per case.

## 7. Estimated Counts

- **Target:** 100–200 high-quality issues for the first release. Prefer quality (clear repro, test, and fix) over volume.
- **Distribution across libraries:** Aim for at least 3–5 libraries in the first batch (e.g. Beast, JSON, Algorithm, Container, Asio) with 20–50 issues each, then expand.
- **Difficulty distribution:** Roughly 40% easy (small, localized fix), 40% medium (multi-file or non-trivial), 20% hard (subtle or build/test changes). Adjust after mining.
- **Validation:** Plan to mine 2–3× the target (e.g. 300–500 candidates), then filter by “buggy fails / fixed passes” and clarity to reach 100–200.
