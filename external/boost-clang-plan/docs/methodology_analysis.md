# Consolidated Methodology Analysis (Issues 1–5)

This document synthesizes methodology insights from the external benchmark collection (Child Issues 1–5) and identifies common patterns to adapt for the Boost/Clang internal benchmark.

## Summary of Issues 1–5

| Issue | Benchmark | Main artifact | Pattern |
|-------|-----------|---------------|---------|
| 1 | SWE-Bench Multilingual | C/C++ issue subset, Docker harness | Issue→patch; tests must pass; harness runs in container |
| 2 | Defects4C | bug_catalog.json, checkout_bug.py, run_tests.py | Full dataset fetch; one script populates catalog; checkout by bug-id; run tests per bug |
| 3 | BugSwarm | cpp_artifacts.json, download_artifact.py, reproduce_ci.py | Fetch full dataset; filter C/C++; Docker image per artifact; run_failed.sh/run_passed.sh |
| 4 | SWE-PolyBench 500 | polybench_500.jsonl, cpp_subset.jsonl, evaluate.py | HF download; full + filtered JSONL; official eval or wrapper; task_id, prompt, test_cmd, patch |
| 5 | MultiPL-E + HumanEval | cpp_problems.jsonl, humaneval_python.jsonl, sandbox, evaluate_passk.py | HF datasets; task_id, prompt, tests, canonical_solution; sandbox compile/run; pass@k |

## Common Patterns in Benchmark Creation

### 1. Single source of truth for the catalog

- One script (e.g. `download_dataset.py`, `download.py`) fetches from an authoritative source (API, HF, GitHub) and writes a single catalog or JSONL.
- No optional or duplicate scripts that maintain the same data; one pipeline to refresh.

### 2. Schema: identity, reproducibility, gold outcome

- **Identity:** `task_id` / `case_id` / `instance_id` / `image_tag`, plus repo (and optionally library/component).
- **Reproducibility:** `base_sha` / `buggy_commit` / `fail_commit`, and often `fixed_commit` / `pass_commit` / `gold_merge_sha`; `build_cmd`, `test_cmd`, or `evaluation_steps`.
- **Gold outcome:** canonical patch or fixed commit; validation = “run this and it passes.”

### 3. Fail→pass verification

- Every case has a defined failing state (buggy commit / failing job) and a passing state (fixed commit / gold patch). The benchmark harness verifies: baseline fails, gold passes.

### 4. Docker (or pinned environment) for reproducibility

- External benchmarks use containers (BugSwarm per-artifact image; SWE-Bench/MultiPL-E sandbox) or pinned toolchains so that “run these commands” is deterministic.

### 5. Methodology doc as contract

- Each benchmark has a methodology document that answers: where the data comes from, how it was filtered/selected, how to run evaluation, and how to replicate the *pattern* for our own data (Boost/Clang replication plan).

### 6. Evaluation runner returns a clear metric

- Defects4C: run tests → pass/fail per bug. BugSwarm: run_failed/run_passed exit code. SWE-PolyBench: pass rate from official harness. MultiPL-E: pass@1, pass@10, pass@100. Internal plan should define analogous metrics (e.g. pass rate per case, regression safety).

## Patterns Adapted to Boost

- **Catalog:** One JSON (or JSONL) of Boost cases: library, issue_id, buggy_commit, fixed_commit, test_cmd, build_cmd; optional difficulty, category, lines_changed.
- **Harvest:** GitHub Issues (closed, bug-like) + linked PRs/commits; or git history (bug-fix commit patterns). Filter: has test, clear description, patch size in range.
- **Verification:** Build at buggy_commit → test fails; apply fix or checkout fixed_commit → test passes. Docker image with B2/CMake and Boost.Test (or equivalent).
- **Replication insight from issues:** BugSwarm “run_failed/run_passed” → Boost “run test at base_sha (fail), run test at fixed_sha (pass)”. Defects4C “checkout_bug + run_tests” → Boost “checkout repo at commit + build_cmd + test_cmd”.

## Patterns Adapted to Clang

- **Catalog:** JSON/JSONL: component, bug_id, buggy_commit, fixed_commit, test_file or build_target; categories (frontend, sema, codegen, driver).
- **Harvest:** LLVM bug tracker (Bugzilla/GitHub) + git history (commit message patterns, differential revisions). Filter: resolved/fixed, has regression test.
- **Verification:** Build Clang (minimal target); run lit test or targeted check-* at buggy_commit (fail) and fixed_commit (pass). Docker with LLVM/Clang build env.
- **Replication insight:** Same “fail→pass” contract; test infrastructure is lit + FileCheck instead of Boost.Test; build is CMake + Ninja with defined targets.

## Tooling Implications

- **Mining:** Scripts to query GitHub/LLVM (issues, PRs, commits) and output candidate list with metadata.
- **Extraction:** Scripts to extract bug-fix pairs (buggy/fixed commits), test commands, and optional patches.
- **Generation:** Templates to produce test runners or lit tests when not already present.
- **Validation:** Pipeline that checks “buggy fails, fixed passes” and optionally build reproducibility (Docker).
- **Dependencies:** Python 3, Git, Docker; for Boost: B2 or CMake, Boost libs; for Clang: CMake, Ninja, LLVM/Clang build.

## Gaps and Decisions for Internal Plan

- **Scope:** Boost and Clang each need a bounded target (e.g. 100–200 high-quality cases) and clear inclusion criteria (has test, clear description, patch size, library/component spread).
- **Difficulty:** Define levels (e.g. from lines_changed, test complexity, or manual label) and target distribution.
- **Cross-repo (Boost):** Document when a case involves multiple repos (e.g. workspace) and how verification runs.
- **Policy:** Forbidden paths (CI disabling, test skipping) and allowed exceptions must be in the case schema and checked by the harness.
