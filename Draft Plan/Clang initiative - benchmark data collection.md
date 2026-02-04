### Clang initiative — benchmark data collection spec (v0.1)

This document defines what must be captured to build **replayable benchmark cases** for the C++ Alliance **Clang initiative**, using the general framework in `AI benchmarking.md`.

It is grounded in the repo’s documented workflow: **GitHub-native**, **human-in-the-loop**, AI generates candidate patches/tests, humans review and upstream-ready patches are submitted to LLVM/Clang.

---

### End-to-end process (Clang-specific)
- **Select target outcomes**: bug fixes, C++ feature implementations, test/coverage improvements, review/triage automation.
- **Harvest replayable history** (preferred): LLVM/Clang issues + linked PRs/commits, CI failures that were later fixed, and review conversations.
- **Package each case** pinned to an exact commit with deterministic build/test commands.
- **Verify case**: baseline fails at `base_sha`; gold patch/commit makes it pass (FAIL→PASS with PASS→PASS regression safety).
- **Run baselines** (today’s coding agents/LLMs) under one harness (same environment, budgets, and policies).
- **Publish dataset version + scorecard** so future iterations can be compared.

---

### Scope and goals
- **Primary goal**: benchmark **AI outcomes that matter for Clang** (correctness, tests/coverage, upstream acceptability, review acceleration).
- **Primary focus**: **high-quality C/C++ compiler engineering** (Clang/LLVM coding standards, correctness vs the standard, robust tests, minimal-risk changes).
- **Non-goals**: subjective “helpfulness” without a measurable signal; tasks that require upstream maintainer judgment *as the only* success criterion.

---

### Benchmark suites for Clang (what we will score)
Use multiple suites to avoid ambiguous scoring.

- **Issue-fix (compiler bug) suite**
  - **Input**: issue description + minimal reproducer (or failing test) + pinned `base_sha`.
  - **Success**: regression test added or strengthened *and* all relevant test suites pass (FAIL→PASS and PASS→PASS).

- **Feature/implementation (spec → Clang code) suite**
  - **Input**: short spec/acceptance criteria (often derived from a WG21 paper or a scoped sub-feature) + pinned `base_sha`.
  - **Success**: implementation + tests; build/test passes on target toolchains; no policy violations.

- **Tests/coverage improvement suite**
  - **Input**: target component/file + coverage goal + constraints + pinned `base_sha`.
  - **Success**: coverage increases for the defined scope (file/dir/target) without breaking tests or bloating runtime beyond a budget.
  - **Notes**: aligns with the documented emphasis that added tests should **improve coverage**, and that full-coverage runs can be too slow unless scoped.

- **PR pre-review/report suite (review acceleration)**
  - **Input**: PR diff + CI status + project guidelines.
  - **Success**: generated report matches a labeled set of “review findings” (bugs, missing tests, style violations, risky patterns) with bounded false positives.
  - **Secondary metric**: estimated **time-to-review reduction** (proxy: fewer reviewer iterations; faster “first useful signal”).

- **Triage + duplicate detection suite**
  - **Input**: new issue context.
  - **Success**: retrieved similar issues/PRs match labeled relevant set (top‑k recall/precision/MRR); optional classification into triage buckets.

---

### Data sources (what we harvest)
These map to the “replayable historical work” principle.

- **LLVM/Clang GitHub history**
  - Issues (problem statements, repro steps, discussions)
  - PRs and review comments (decision rationale; what reviewers care about)
  - Merge commits / linked PRs that provide **gold outcomes**

- **CI artifacts**
  - Failing build/test logs for specific commits
  - Coverage reports (full or scoped), when used as success criteria

- **Knowledge capture artifacts (optional but high-leverage)**
  - Interview transcripts / distilled guidance capturing reviewer heuristics and tacit knowledge (used as “policy docs” or rubric references, not as leaked solutions).

---

### Case definition (required fields for Clang cases)
Follow the general schema in `AI benchmarking.md`; the minimum Clang-required fields below ensure replayability and fair scoring.

- **Identity and provenance**
  - `case_id`, `suite`, `title`, `labels` (e.g., `Sema`, `CodeGen`, `AST`, `Driver`, `Modules`), `difficulty`
  - `repo_url` (e.g., fork or upstream mirror), `base_sha`
  - `created_from` (issue/PR IDs, CI run IDs), `dataset_version`

- **Task input**
  - `prompt_markdown` (issue text/spec/log excerpt)
  - `context_hints` (key files, targets like `ninja check-clang`, repro commands)

- **Reproducibility**
  - `environment`: OS + compiler toolchain versions + CMake/Ninja + required deps
  - `setup_steps`, `repro_steps`, `evaluation_steps`

- **Constraints / policies**
  - `forbidden_paths` (default: CI/workflow files and broad test deletions; allow exceptions per-case)
  - `allowed_paths` (explicitly whitelisted edits when needed)
  - `time_budget_minutes` (per case)

- **Gold outcome**
  - `gold_merge_sha` (preferred) or `gold_patch` pointer
  - `gold_validation` proof (log snippet + command transcript) that gold passes `evaluation_steps`

- **Scoring hooks**
  - `success_criteria` as machine-checkable as possible (tests/targets/coverage deltas)
  - `penalties` (e.g., skipped tests, weakened assertions, disabling checks)

---

### Success criteria (Clang-specific guidance)
- **Prefer built-in signals**: `ninja check-*`, lit tests, and targeted suites that upstream uses.
- **Regression safety is mandatory**: PASS→PASS checks must run for the defined scope.
- **Coverage scoring must be scoped**: file/dir/target coverage deltas are acceptable; avoid 30‑minute full coverage as the *only* loop signal.
- **Upstream acceptability is a constraint**: enforce LLVM formatting/style rules and discourage sprawling diffs (track diff size as a secondary metric).

---

### Anti-gaming / guardrails (Clang)
- **Protected paths (default)**:
  - CI workflow files
  - broad test deletions or blanket “skip” mechanisms
- **Disallowed “fixes”**:
  - disabling failing checks rather than fixing code (unless the case is explicitly “fix CI config”)
  - weakening assertions or deleting coverage-increasing checks
- **Allowed exceptions**:
  - test edits/additions are expected for issue-fix cases, but must be regression-sound and (where applicable) improve coverage.

---

### Baseline scoring plan (Clang dataset)
Once the dataset slice exists:
- Run **Pass@1** baselines for:
  - a “single-shot patch” baseline (no tool use)
  - a “tool-using agent” baseline (build/test loop, repo navigation)
  - MCP on/off variants if retrieval is in scope
- Capture artifacts per run: patch/diff, build/test logs, violations, wall-clock time, attempts.
- Produce `baseline_scorecard.md` with per-suite resolved rate and top failure modes (compile failures, wrong target selection, missing tests, policy violations).

---

### Deliverable definition (dataset v0.1 for Clang)
A reasonable first release should be small but representative:
- **N=30** total cases, for example:
  - 10 issue-fix (with tests)
  - 8 implementation (small scoped features)
  - 7 tests/coverage tasks (scoped coverage signal)
  - 3 PR pre-review/report tasks
  - 2 triage/duplicate detection tasks

Every case must include:
- pinned `base_sha`
- a verified gold outcome
- deterministic evaluation steps
- explicit constraints (allowed/forbidden paths)

---

### Open questions to track (do not block v0.1)
- **Which repos are authoritative for evaluation**: `cppalliance/clang` fork vs an upstream mirror of `llvm/llvm-project`.
- **Coverage tooling**: which coverage system and how to define scoped coverage deltas so they are stable and cheap.
- **“Time-to-review” measurement**: whether we treat it as a benchmark suite (labeled findings) or an offline metric computed from review iterations.

