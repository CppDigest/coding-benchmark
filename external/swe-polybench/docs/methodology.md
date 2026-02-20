# SWE-PolyBench 500 Subset: Methodology

**SWE-PolyBench 500 is not a C/C++ dataset.** It contains only Java, JavaScript, TypeScript, and Python. This document answers the research questions for Child Issue 4 and describes issue selection, language coverage, difficulty, test generation, and the replication plan for Boost/Clang.

## Research questions

### What is SWE-PolyBench and how does it differ from SWE-Bench?

- **SWE-PolyBench** is a **multi-language**, **repository-level** benchmark for evaluating coding agents. It contains curated issues (bug fixes, features, refactoring) from real GitHub repos, with per-instance Dockerfiles and test commands. It covers **Java, JavaScript, TypeScript, and Python** (no C/C++ in the current release).
- **SWE-Bench** is **Python-focused**, issue-to-patch benchmark with a single language and different task sourcing. SWE-PolyBench generalizes the idea to multiple languages and adds stratified subsets (500, Verified) and retrieval-oriented metrics (file/node precision/recall).

### Where is the official dataset/repository hosted?

- **Datasets:** Hugging Face — `AmazonScience/SWE-PolyBench` (full 2,110), `AmazonScience/SWE-PolyBench_500` (500 subset), `AmazonScience/SWE-PolyBench_Verified` (394 verified).
- **Code and evaluation:** GitHub — [amazon-science/SWE-PolyBench](https://github.com/amazon-science/SWE-PolyBench). Evaluation script: `src/poly_bench_evaluation/run_evaluation.py`.
- **Documentation / leaderboard:** [amazon-science.github.io/SWE-PolyBench](https://amazon-science.github.io/SWE-PolyBench).

### What languages are included in the 500 subset?

- **Four languages:** Java, JavaScript, TypeScript, Python. **125 instances per language** (500 total). The benchmark does **not** currently include C/C++; the C/C++ filtered subset (`cpp_subset.jsonl`) will be non-empty only if the dataset is extended.

### How many C/C++ issues are in the 500 subset?

- **Zero** in the current release. The 500 subset is stratified across Java, JavaScript, TypeScript, and Python only. Our download script still produces `cpp_subset.jsonl` (filtered by `language` in C/C++) so the pipeline is ready when/if C/C++ instances are added.

### What is the task format? (issue description, expected output, tests)

- **Per instance:** `instance_id`, `repo`, `base_commit`, `problem_statement` (issue title + body), `patch` (gold patch), `test_patch`, `test_command`, `F2P` (fail-to-pass tests), `P2P` (pass-to-pass tests), `language`, `task_category` (Bug Fix / Feature / Refactoring), `Dockerfile` (instance-level). Our JSONL uses `issue_text` = `problem_statement`, `test_cmd` = `test_command`, `expected_patch` = `patch`.

### Is there an official evaluation script?

- **Yes.** In the GitHub repo: `src/poly_bench_evaluation/run_evaluation.py`. It takes `--dataset-path` (Hugging Face dataset name), `--predictions-path` (JSONL with `instance_id`, `model_patch`), `--result-path`, and optional `--evaluate-gold`, `--num-threads`, `--repo-path`, `--delete-image`, etc. It runs instance-level Docker builds/tests and outputs pass rate and instance-level results. Our `evaluation/evaluate.py` can call this when `--use-official --polybench-repo` are provided.

### What repositories/projects are sources for the issues?

- Issues are drawn from **21 repositories** across the four languages (see the paper/dataset). Repos are identified by the `repo` field (e.g. GitHub owner/name). The full dataset lists them; the 500 subset is a stratified sample from the full set.

### How are issues validated for correctness?

- **Gold patch:** The solution patch comes from the merged PR that resolved the issue. **Tests:** F2P (tests that were failing and are fixed by the PR) and P2P (tests that must remain passing). The official evaluator runs the test command inside an instance-specific Docker image and checks F2P/P2P outcomes. The **Verified** subset (394 instances) has additional curation and updated Dockerfiles for a 100% gold pass rate.

### What difficulty levels or categories exist?

- **Task categories:** Bug Fix, Feature, Refactoring (in the 500 subset roughly 40% Bug Fix, 40% Feature, 20% Refactoring). The dataset also includes retrieval-related flags (`is_func_only`, `is_class_only`, `num_func_changes`, etc.) used for file/node-level difficulty and metric computation.

## Methodology documentation requirements

### Issue selection (how were the 500 issues selected?)

- The 500 subset is a **stratified sample** from the full SWE-PolyBench (2,110 instances): 125 instances per language (Java, JavaScript, TypeScript, Python) and a balanced distribution of task categories (40% Bug Fix, 40% Feature, 20% Refactoring). So selection is by language balance and task-type balance from the full set.

### Multi-language coverage

- Language balance was achieved by **stratified sampling**: exactly 125 instances from each of the four languages in the full benchmark, so the 500 subset is language-balanced by design.

### Difficulty calibration

- Difficulty is reflected by **task category** (Bug Fix, Feature, Refactoring) and by retrieval-oriented fields (e.g. function-only vs class-level changes, number of changed nodes). The benchmark does not publish a single numeric difficulty rating; difficulty is inferred from category and retrieval metrics.

### Test generation

- **Tests** are tied to the merged PR: F2P tests are those that failed before and pass after the fix; P2P tests must pass before and after. The `test_patch` and `test_command` come from the solution PR. The official evaluator runs the instance Docker image and executes the test command to validate F2P/P2P; the Verified subset has Dockerfiles that achieve 100% gold pass rate.

## Replication plan for Boost/Clang

### Selection criteria for Boost issues

- Must have **clear issue description** (e.g. on GitHub).
- Must have an **associated test case** (failing test that the fix resolves).
- **Patch size:** target 1–100 lines (configurable).
- **Coverage:** span **different Boost libraries** (e.g. Beast, Asio, JSON, etc.).

### Selection criteria for Clang issues

- **Source:** LLVM bug tracker (e.g. Bugzilla, GitHub issues).
- **Scope:** include **frontend, optimizer, and backend** issues.
- Must have a **regression test** (e.g. lit test or reduced case).
- **Difficulty:** cover different difficulty levels (e.g. one-line fixes vs multi-file changes).

### Application

- For **Boost**, we would collect issues that meet the above criteria, then produce a catalog (e.g. JSONL) with `repo`, `issue_text`, `test_cmd`, `expected_patch`, and optional difficulty/category, and run evaluation via a Boost-specific harness (build + run tests).
- For **Clang**, we would collect LLVM/Clang issues with regression tests, catalog them similarly, and evaluate with a Clang test harness (e.g. `ninja check-clang` or targeted lit tests). The *structure* (issue, test command, gold patch, pass/fail) mirrors SWE-PolyBench; the *environment* (Boost/Clang repos and test runners) is domain-specific.

## Summary

| Topic | Answer |
|-------|--------|
| SWE-PolyBench vs SWE-Bench | Multi-language, repo-level; SWE-Bench is Python-focused |
| Hosting | Hugging Face (AmazonScience/SWE-PolyBench_500); GitHub (evaluation code) |
| Languages in 500 | Java, JavaScript, TypeScript, Python (125 each) |
| C/C++ in 500 | 0 in current release; pipeline ready via cpp_subset.jsonl |
| Task format | instance_id, repo, problem_statement, patch, test_command, F2P, P2P, language, task_category, Dockerfile |
| Official evaluation | run_evaluation.py in repo; our evaluate.py can delegate with --use-official |
| Issue sources | 21 repos across 4 languages |
| Validation | Gold patch from PR; F2P/P2P tests; Verified subset has curated Dockerfiles |
| Categories | Bug Fix, Feature, Refactoring (40-40-20 in 500) |
| Replication Boost/Clang | Selection criteria above; same catalog + harness pattern |
