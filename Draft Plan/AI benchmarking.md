### End-to-end benchmark process (reusable for any new AI feature)
- **Define the outcome you’re shipping**: what “good” looks like (e.g., fix build failures, implement a feature, refactor safely, improve retrieval quality, produce review comments).
- **Choose benchmark suites** that make success unambiguous (build/test signals beat “looks right”).
- **Create benchmark cases** from replayable history (issues/PRs/CI failures) and/or newly authored tasks, each pinned to an exact repo state.
- **Verify every case** (repro steps, failing baseline, known-good “gold” outcome, determinism).
- **Run baselines on today’s coding agents/LLMs** under a standardized harness (same tool budget, same environment, same rules).
- **Report + version**: publish dataset version, harness version, and baseline scorecard; rerun on every feature iteration and compare deltas.

This plan borrows heavily from established “issue → patch → tests” benchmarks (e.g., SWE-bench Verified-style evaluation), multilingual issue-resolution work that includes C/C++ (e.g., Multi-SWE-bench), and contamination-aware evaluation practices (e.g., time-sliced benchmarks like LiveCodeBench).

---

### Goals and scope
- **Primary goal**: a **repeatable process** to build benchmark data for *any* upcoming AI capability in this framework, not just Clang/CI fixes.
- **Primary focus area**: **high-quality C/C++ engineering outcomes** (correctness, buildability, portability, toolchain hygiene, and maintainability).
- **Non-goals** (for the benchmark itself): measuring “chat quality” or subjective helpfulness unless it is tied to an objective signal (tests/build/linters/review policy adherence).

---

### Benchmark design principles (what “good” looks like)
- **Replayable and pinned**: every case pins **repo + base commit SHA + exact commands** and expected signals.
- **Outcome-based scoring**: prefer **FAIL→PASS** transitions with full regression checks (tests that were passing must stay passing).
- **Gold outcome exists**: for historical cases, use merged PRs / known fix commits as references; for authored cases, include a maintainer-approved reference patch.
- **Deterministic evaluation**: cases must run in a controlled environment (container/toolchain pinning) and produce consistent results.
- **Anti-gaming**: protect paths and apply policy checks so “fixing by weakening tests” or disabling CI is scored as failure or penalized.
- **Minimal necessary context**: include enough context to be solvable without leaking the answer; avoid tasks where discussion text contains the solution.
- **Versioned dataset + harness**: treat the dataset as a product with releases (e.g., `v0.1`, `v0.2`) and changelogs.

---

### Benchmark suites (recommended taxonomy)
Split into suites so each has a crisp success definition and comparable metrics.

- **Build/CI-fix suite (binary + diagnostics)**  
  - **Input**: failing CI run logs + repo SHA (+ optional local repro script).  
  - **Success**: CI (or the defined job subset) turns green **without violating rules**.

- **Issue-fix suite (test-backed bug fix)**  
  - **Input**: issue report + minimal repro + base SHA.  
  - **Success**: a regression test exists (new or strengthened) and **full test suite passes** (FAIL→PASS and PASS→PASS).

- **Feature/implementation suite (spec → code)**  
  - **Input**: short spec / acceptance criteria + relevant code pointers + base SHA.  
  - **Success**: new capability implemented + tests (and/or example programs) proving it, plus build cleanly on target toolchains.

- **Refactor/maintenance suite (behavior preserved)**  
  - **Input**: refactor goal + constraints (no behavior change, perf budget, API compat).  
  - **Success**: all tests pass + static checks pass; optionally verify ABI/API constraints where applicable.

- **Retrieval/context suite (MCP / search quality)**  
  - **Input**: new issue/PR context or a question requiring repository knowledge.  
  - **Success**: retrieved items match a labeled relevance set (top‑k recall/precision, MRR), with **evidence** (citations) in the agent output.

- **Review/triage suite (optional, policy-based)**  
  - **Input**: PR diff + CI result + project guidelines.  
  - **Success**: issues found match a labeled list; false positives are bounded; recommended changes are safe and consistent with style/policy.

---

### Benchmark case format (schema checklist)
Use a single normalized representation for all suites (e.g., JSON or YAML front-matter + Markdown body). Keep it close to your ingestion format, but add benchmark-only fields.

- **Identity and provenance**
  - `case_id`, `suite`, `title`, `labels/components`, `difficulty`
  - `repo_url`, `base_sha`, `created_from` (issue/PR/CI run IDs), `dataset_version`

- **Task input**
  - `prompt_markdown` (issue text / spec / failure log excerpt)
  - `context_hints` (optional: key files, commands, environment notes)

- **Reproducibility**
  - `setup_steps` (checkout, dependencies)
  - `repro_steps` (commands that demonstrate failing baseline)
  - `evaluation_steps` (commands that define success; typically full test suite and/or CI job equivalence)
  - `environment` (OS/container image, compiler versions, CMake/Ninja versions, sanitizers, etc.)

- **Constraints / policies**
  - `allowed_paths`, `forbidden_paths` (protected paths policy)
  - `time_budget_minutes`, `tool_budget` (optional), `network_policy` (allowed/disallowed)

- **Gold / reference outcome**
  - `gold_merge_sha` or `gold_patch` pointer
  - `gold_validation` (proof that the gold outcome passes evaluation steps)

- **Scoring hooks**
  - `success_criteria` (explicit, machine-checkable where possible)
  - `penalties` (protected path edits, disabling tests, skipping jobs, etc.)

---

### Scoring rubric (suite-by-suite)
Keep a **primary score** that is hard to argue with, plus secondary diagnostics that help engineering.

- **Primary metrics**
  - **Resolved rate** (case success %) for CI-fix / issue-fix / implementation suites.
  - **Pass@1** as the default; optionally **Pass@k** if your harness supports multiple attempts/seeds.
  - **Retrieval metrics** (top‑k recall/precision, MRR) for context suite.

- **Secondary metrics (always record, don’t over-optimize early)**
  - attempts/iterations, wall-clock time, diff size, number of files touched
  - build warnings introduced (treat warnings-as-errors where appropriate)
  - clang-tidy / formatting / lint deltas (if enforced by project policy)
  - “policy violations” count (protected path edits, test skipping, CI disabling)
  - optional: token/cost estimates per model step (if available)

---

### Anti-gaming and quality controls (must-have for credibility)
- **Protected paths**: default forbid edits to `tests/`, CI workflows, and build scripts unless a case explicitly allows it.
- **Assertion weakening detection**: flag patterns like skipped tests, reduced coverage, broadened tolerances, or deleted checks.
- **No “disable the checker” fixes**: editing CI to not run the failing job counts as failure unless the task is explicitly “fix CI config”.
- **Leakage screening**: exclude cases where the solution is effectively contained in the issue thread or PR comments.
- **Determinism checks**: rerun each case multiple times in a clean environment; quarantine flaky cases.

---

### How to create benchmark data for a new feature (the reusable process)
- **Step 0 — Feature definition**
  - Write a one-page “evaluation intent”: what the feature changes, what success looks like, what it must not break.

- **Step 1 — Task selection**
  - Pick a small set of tasks that directly exercise the feature, spread across easy/medium/hard.
  - Prefer tasks where success is measurable via build/tests/tools (especially for C/C++).

- **Step 2 — Candidate harvesting (recommended: start from history)**
  - Pull candidates from replayable history: issues + linked PRs, CI failures that were later fixed, regression bugs with tests added.
  - For C/C++, also consider curated bug corpora patterns (e.g., ManyBugs/IntroClass/Defects4C-like “bug + tests + fix commit” structure) as inspiration for what’s reproducible.

- **Step 3 — Case assembly**
  - Normalize the input (issue/log/spec) into `prompt_markdown`.
  - Add minimal context: exact repro commands, key file pointers, environment notes.

- **Step 4 — Verification (gate before adding to dataset)**
  - Confirm baseline fails on `base_sha`.
  - Confirm `gold_merge_sha` (or reference patch) makes evaluation pass.
  - Confirm PASS→PASS: no regressions elsewhere.

- **Step 5 — Labeling and difficulty**
  - Label component/area; set difficulty using transparent heuristics (e.g., number of files touched in gold patch, stack depth, toolchain complexity).

- **Step 6 — Dataset release**
  - Add cases + dataset metadata (dataset card), bump dataset version, publish changelog.

---

### Baseline scoring (today’s agents/LLMs) so we can compare against them
After the dataset exists, we need a “snapshot” scorecard for current state-of-the-art tools.

- **Standardize the evaluation harness**
  - Same container/toolchain, same repo checkout rules, same time budget.
  - Same tool access policy (network on/off, allowed commands, MCP on/off).
  - Same stopping criteria (max iterations/time).

- **Choose baseline systems**
  - **Closed-model coding assistants** (run via their APIs if available to you).
  - **Open-source coding models** (run locally if feasible).
  - **Agent frameworks**: at least one “single-shot” baseline and one “tool-using multi-step” baseline.

- **Run protocol**
  - Default to **Pass@1** with fixed settings; optionally repeat with multiple seeds for confidence intervals.
  - Record raw artifacts: patches, logs, tool calls, final test results.

- **Deliverable output**
  - A `baseline_scorecard.md` with per-suite resolved rate, plus the top failure modes (compile failures, missing tests, wrong file edits, policy violations).

---

### Current focus: Clang issues + CI failures (fits into the general framework)
We can start by shipping a **Clang/CI subset** as `dataset v0.1` because it is highly replayable and strongly signal-based.
- CI-fix cases: failing job logs + fixed run evidence.
- Issue-fix cases: issue + linked PR with tests.
- Retrieval cases: “find similar past failures” with labeled relevant items.

---

### Issue backlog (2–3 day, single-dev deliverables)
Below are small, shippable issues that build the general benchmarking capability **and** deliver the Clang/CI dataset already in this draft. (Create as many of these as you want; they’re intentionally granular.)

---

### Issue 1 — Write benchmark spec v0.1 (feature-agnostic)
- **Goal**: define suites, required artifacts, and acceptance criteria for a case.
- **Deliverables**: 2–4 page spec doc + glossary (case, suite, gold patch, protected paths, pass criteria).
- **Acceptance**: reviewer can classify a new feature into suites and know how to score it.

### Issue 2 — Define a canonical case schema (JSONSchema + examples)
- **Goal**: a single schema that all suites share.
- **Deliverables**: `schema.json` + 5 example cases (one per suite) validating against the schema.
- **Acceptance**: schema validation passes; examples render cleanly to markdown.

### Issue 3 — Create dataset layout + versioning conventions
- **Goal**: filesystem conventions for `benchmarks/` and versioning rules.
- **Deliverables**: folder structure + dataset card template + changelog template.
- **Acceptance**: adding a new dataset version is mechanical and consistent.

### Issue 4 — Implement a case validator CLI
- **Goal**: validate schema + required artifacts exist + path rules are sane.
- **Deliverables**: CLI that checks a dataset directory and emits a report.
- **Acceptance**: validator catches missing fields, missing artifacts, and invalid path globs.

### Issue 5 — Define protected-path policy + violation detector
- **Goal**: make anti-gaming enforceable.
- **Deliverables**: policy doc + script that inspects a patch/diff and flags forbidden edits.
- **Acceptance**: detector correctly flags: “only tests changed”, “CI disabled”, “skipped tests” patterns.

### Issue 6 — Container/toolchain pinning for C/C++ evaluation
- **Goal**: determinism across runs.
- **Deliverables**: container definition (or documented toolchain pin) for clang/gcc, CMake/Ninja, common deps.
- **Acceptance**: a sample case reproduces identically on two machines.

### Issue 7 — Create scoring rubric v0.1 (primary + secondary metrics)
- **Goal**: unambiguous scoring for all suites.
- **Deliverables**: rubric doc + `metrics.json` definition.
- **Acceptance**: two reviewers independently score the same run and match.

---

### Issue 8 — Clang/CI candidate mining query pack
- **Goal**: consistent way to find replayable candidates.
- **Deliverables**: documented GitHub queries/filters (issues, PRs, CI runs) + labeling rules.
- **Acceptance**: two people produce overlapping candidate lists with similar yield.

### Issue 9 — Clang/CI case assembler (CI-fix) from failing run → case bundle
- **Goal**: generate CI-fix cases automatically.
- **Deliverables**: script that takes a run URL/ID and outputs a case folder with logs + repro steps stub.
- **Acceptance**: produces 5 valid CI-fix cases end-to-end.

### Issue 10 — Clang/CI case assembler (issue-fix) from issue + linked PR → case bundle
- **Goal**: generate issue-fix cases automatically when there’s a linked PR.
- **Deliverables**: script that captures issue body, key comments, base SHA, gold merge SHA, and test commands.
- **Acceptance**: produces 5 valid issue-fix cases that pass verification on gold.

### Issue 11 — Create labeled retrieval cases for “similar failures” (starter set)
- **Goal**: bootstrap retrieval evaluation.
- **Deliverables**: 10 retrieval cases with labeled relevant doc/issue IDs (top‑k target list).
- **Acceptance**: label format is consistent; labels have rationale notes.

### Issue 12 — Clang/CI dataset v0.1 (N=30) with verification evidence
- **Goal**: ship the first dataset slice.
- **Deliverables**: 30 verified cases (suggest: 15 CI-fix, 10 issue-fix, 5 retrieval) + dataset card.
- **Acceptance**: every case has baseline-failing evidence and gold-passing evidence.

---

### Issue 13 — Benchmark runner skeleton (load cases, execute evaluation steps, record artifacts)
- **Goal**: minimal harness that runs a dataset and records results.
- **Deliverables**: runner that outputs `results.jsonl` + per-case logs.
- **Acceptance**: runs all cases in a dataset directory and produces a summary table.

### Issue 14 — Add policy checks to the runner (protected paths, skipped tests, CI disabling)
- **Goal**: enforce anti-gaming during evaluation.
- **Deliverables**: runner emits violation events and marks runs invalid/failed per rubric.
- **Acceptance**: a deliberately “cheating” patch is detected and scored down.

### Issue 15 — Add C/C++ quality signals (compile warnings, clang-tidy/format gates where applicable)
- **Goal**: align with “high-quality C/C++” focus.
- **Deliverables**: optional hooks for warnings-as-errors, clang-tidy, clang-format check.
- **Acceptance**: metrics show when a patch passes tests but worsens toolchain hygiene.

### Issue 16 — Baseline protocol doc (standard settings + reproducibility checklist)
- **Goal**: ensure baseline runs are comparable.
- **Deliverables**: doc specifying timeouts, retries, temperature, tool access, and artifact capture.
- **Acceptance**: two baseline runs from two people are directly comparable.

### Issue 17 — Baseline adapters: “single-shot patch” and “tool-using agent” wrappers
- **Goal**: run different baselines through one harness interface.
- **Deliverables**: adapter interfaces + 2 baseline implementations (one simple, one tool-using).
- **Acceptance**: both baselines produce results in the same schema.

### Issue 18 — Baseline scorecard for “today’s agents/LLMs” on Clang/CI v0.1
- **Goal**: create the comparison point for your product.
- **Deliverables**: `baseline_scorecard.md` + raw `results.jsonl` artifacts for each baseline.
- **Acceptance**: scorecard includes per-suite resolved rate + top failure modes.

---

### Issue 19 — Flakiness triage: detect and quarantine nondeterministic cases
- **Goal**: keep the dataset credible.
- **Deliverables**: rerun tool that repeats evaluation 3–5 times; tags flaky cases.
- **Acceptance**: flaky cases are excluded or marked and not counted in headline score.

### Issue 20 — Leakage screening checklist for harvested historical cases
- **Goal**: avoid “answer in the prompt thread” cases.
- **Deliverables**: checklist + automated heuristics (e.g., patch snippets present in comments).
- **Acceptance**: at least 5 cases reviewed with recorded decisions.

### Issue 21 — Dataset release automation (packaging + checks)
- **Goal**: make publishing a dataset version routine.
- **Deliverables**: one command that validates, packages, and emits a release summary.
- **Acceptance**: release fails fast on missing evidence/invalid schema.

### Issue 22 — Reporting: HTML/Markdown summary with drill-down
- **Goal**: make results easy to consume.
- **Deliverables**: report generator with per-suite charts/tables and per-case links to logs/diffs.
- **Acceptance**: a reviewer can identify top 10 failure patterns in <10 minutes.

### Issue 23 — Add “feature/implementation” mini-suite (N=5) for C/C++
- **Goal**: expand beyond fixing to implementing.
- **Deliverables**: 5 small implementation tasks with tests/examples and pinned toolchains.
- **Acceptance**: each task has a gold reference and deterministic evaluation steps.

### Issue 24 — Add “refactor/maintenance” mini-suite (N=5) for C/C++
- **Goal**: test safe edits and maintainability.
- **Deliverables**: 5 refactor tasks (no behavior change) with full regression checks.
- **Acceptance**: gold solution passes; evaluation detects behavior regressions.