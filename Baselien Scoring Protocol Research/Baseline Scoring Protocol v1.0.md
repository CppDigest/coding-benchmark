# Baseline Scoring Protocol v1.0

This document defines the baseline evaluation protocol for AI coding agents/LLMs on C/C++ engineering tasks. It standardizes how baselines are run, how results are compared, and how data leakage is controlled.

**Applicable benchmark suites**: Clang (issue-fix, feature, tests/coverage, PR review, triage) and Boost CI fixes (single-repo, cross-repo, build-system).

---

## 1. Baseline Categories

### 1.1 Single-Shot Patch Baseline (SS)

**Definition**: One request/response round-trip with no tool calls or iterative refinement.

| Parameter | Specification |
|-----------|---------------|
| Input | Repo snapshot at `base_sha` + failing log/issue description + context hints |
| Output | Full patch (unified diff format) |
| Tool access | None |
| Temperature | 0.0 (deterministic) |
| Context window | Up to 128K tokens |
| Token budget | 200K total (input + output) |

**Stopping criteria**: Single generation attempt; no iteration.

**Use case**: Measures raw model capability without external feedback. Establishes the capability floor.

---

### 1.2 Tool-Using Agent Baseline (TU)

**Definition**: Agent operates in an edit → build/test → iterate loop with access to predefined tools.

| Parameter | Specification |
|-----------|---------------|
| Input | Repo snapshot at `base_sha` + failing log/issue description + context hints |
| Output | Final patch after iteration |
| Tool access | `compile()`, `run_tests()`, `inspect_error_log()`, `get_compilation_flags()` |
| Temperature | 0.0 (deterministic) |
| Context window | Up to 256K tokens |
| Token budget | 300K aggregate |
| Max iterations | 10 tool-equipped reasoning loops |
| Time budget | 30 minutes wall-clock per task |

**Stopping criteria**:
- **Success**: All specified tests pass (FAIL→PASS achieved, PASS→PASS maintained)
- **Failure**: Max iterations reached, time budget exhausted, or no progress over 3 consecutive iterations
- **Timeout**: Hard wall-clock limit exceeded

**Use case**: Measures ability to use structured feedback loops for debugging and iterative refinement.

---

### 1.3 Retrieval-Enabled Baseline (RE)

**Definition**: All TU privileges plus read-only retrieval APIs for code search and documentation.

| Parameter | Specification |
|-----------|---------------|
| Input | Same as TU |
| Output | Final patch after iteration |
| Tool access | TU tools + `search_code()`, `search_documentation()`, `retrieve_similar_issues()` |
| Temperature | 0.0 (deterministic) |
| Context window | Up to 320K tokens |
| Token budget | 400K aggregate |
| Max iterations | 10 tool-equipped reasoning loops |
| Time budget | 45 minutes wall-clock per task |
| Retrieval corpus | Frozen snapshot (pre-dating gold outcomes) |

**Stopping criteria**: Same as TU.

**Use case**: Measures whether retrieval augmentation (MCP/RAG) improves resolution rates.

---

## 2. Environment Standardization

### 2.1 Container Specification

All evaluations run in containerized Docker environments for reproducibility.

**Base image**: `ghcr.io/evalbench/cpp-baseline:<year>-v1` built from Ubuntu 22.04 LTS

**Pinned toolchains**:
| Tool | Version |
|------|---------|
| GCC | 12.3 |
| Clang | 17 |
| CMake | 3.27 |
| Ninja | 1.11 |
| GDB | 13 |
| Python | 3.10 |

**Additional diagnostics**: `clang-tidy`, `cppcheck`, `include-what-you-use`

**Dockerfile requirements**:
- Pin all package versions explicitly
- Multi-stage build: (1) build environment, (2) repo at `base_sha`, (3) clean evaluation layer
- No development headers beyond task requirements

---

### 2.2 Resource Limits

| Resource | Limit |
|----------|-------|
| CPU | 8 vCPU (4 for resource-constrained runs) |
| RAM | 16 GB |
| Disk | 40 GB scratch |
| GPU | Prohibited for baseline |

---

### 2.3 Time and Token Budgets

| Baseline | Time Budget | Token Budget | Iterations |
|----------|-------------|--------------|------------|
| Single-Shot (SS) | 2 min | 200K | 1 |
| Tool-Using (TU) | 30 min | 300K | ≤10 |
| Retrieval-Enabled (RE) | 45 min | 400K | ≤10 |

---

### 2.4 Network Policy

| Policy | Rule |
|--------|------|
| Default | Outbound network blocked |
| Retrieval (RE only) | Whitelisted stub mapping to local corpus |
| Package downloads | Pre-installed in container; no runtime downloads |

---

### 2.5 Decoding / Reproducibility Settings

| Setting | Value |
|---------|-------|
| Temperature | 0.0 |
| Top-p | 1.0 (or provider default for determinism) |
| Random seed | Fixed (`CTEST_RANDOM=OFF`) |
| Compile flags | `-fno-omit-frame-pointer -O1 -g` |
| Repeats (optional) | 3-5 runs for confidence intervals |

---

## 3. Artifact Capture Requirements

Every evaluation run must persist the following artifacts to `${TASK_ID}/${RUN_ID}/`:

### 3.1 Required Artifacts

| Artifact | Format | Description |
|----------|--------|-------------|
| `patch.diff` | Unified diff | Agent's proposed patch |
| `build.log` | Text | stdout/stderr from `cmake`, `make`, `ctest` (or equivalent) |
| `tool_trace.jsonl` | JSON Lines | One entry per tool call: `{"ts": "...", "cmd": "...", "exit": N, "duration_ms": N}` |
| `agent_transcript.md` | Markdown | Full prompts/completions (secrets redacted) |
| `metrics.yaml` | YAML | Elapsed time, tokens consumed, peak RSS, attempt count |

### 3.2 Metrics Schema

```yaml
# metrics.yaml
task_id: clang-issue-001
run_id: run-2026-02-05-001
baseline: TU
model: claude-opus-4.5

timing:
  wall_clock_seconds: 847
  build_seconds: 124
  test_seconds: 312

tokens:
  input: 89432
  output: 12847
  total: 102279

resources:
  peak_rss_mb: 4821
  cpu_seconds: 1892

attempts:
  iteration_count: 4
  tool_calls: 23
  compile_attempts: 6
  test_runs: 4

verdict: PASS  # PASS | FAIL | TIMEOUT | ERROR
failure_category: null  # or: compile_error | test_failure | build_sys | policy_violation | timeout | unknown
policy_violations: 0
```

---

## 4. Leakage and Contamination Safeguards

### 4.1 Actionable Leakage Checklist

Run this checklist for every dataset batch before publishing baselines:

#### Temporal Isolation
- [ ] Every task's `base_sha` commit date is **after** January 1, 2023 (or defined cutoff)
- [ ] Model training cutoff date is **before** the minimum `base_sha` date in the batch
- [ ] Task release date is documented and verified against authoritative sources (git log, issue timestamps)

#### Solution-in-Thread Prevention
- [ ] Issue thread scanned for code blocks, "here's the fix", "try this" patterns
- [ ] PR comments reviewed for explicit solution hints
- [ ] Prompt construction verified to exclude gold patches and solution context

#### Gold Patch Isolation
- [ ] Gold patches stored in separate, inaccessible directory during evaluation
- [ ] Verification container runs separately from agent container
- [ ] Prompt templates verified to not include gold patch content

#### Decontamination Checks
- [ ] Agent output compared to gold patch; flag if ≥80% token overlap (may indicate memorization)
- [ ] N-gram analysis performed against known training corpora (where available)
- [ ] 2% random sample manually inspected for plagiarism

#### Infrastructure Integrity
- [ ] Retrieval corpus snapshot predates all gold outcomes
- [ ] Internet disabled during evaluation
- [ ] Container image hash (SHA256) recorded
- [ ] Retrieval corpus hash (SHA256) recorded
- [ ] Result bundle signed with TUF metadata (optional)

---

### 4.2 Case Exclusion Criteria

Exclude a case from the dataset if any of the following apply:

| Criterion | Action |
|-----------|--------|
| Solution code appears in issue thread | Exclude or rewrite issue text |
| Gold patch visible in PR discussion | Exclude |
| Task predates model training cutoff | Exclude for that model |
| N-gram overlap >90% with training corpus | Manual review; exclude if confirmed |
| Multiple equally-valid solutions exist | Exclude or define canonical success |
| Test suite is flaky (non-deterministic) | Quarantine; exclude from reported metrics |

---

### 4.3 Time-Slicing Protocol

For each model evaluated, record:

| Field | Description |
|-------|-------------|
| `model_training_cutoff` | Model's documented knowledge cutoff date |
| `task_creation_date` | Date the underlying issue/failure was filed |
| `task_gold_date` | Date the gold fix was merged |
| `contamination_risk` | `SAFE` if task_creation_date > model_training_cutoff, else `FLAGGED` |

**Reporting rule**: Report metrics separately for `SAFE` and `FLAGGED` tasks. Primary metrics use only `SAFE` tasks.

---

## 5. Scoring and Reporting

### 5.1 Primary Metrics

| Metric | Definition |
|--------|------------|
| **Resolved Rate** | `(tasks_resolved / tasks_attempted) × 100%` |
| **Pass@1** | Fraction where first patch attempt resolves the task |
| **Pass@k** | Fraction where at least one of k attempts resolves (for TU/RE) |

### 5.2 Confidence Intervals

Use **Wilson score interval** (95% confidence) for resolved rate:

```
CI_lower = (p̂ + z²/2n − z√((p̂(1−p̂) + z²/4n)/n)) / (1 + z²/n)
CI_upper = (p̂ + z²/2n + z√((p̂(1−p̂) + z²/4n)/n)) / (1 + z²/n)
```

Where:
- p̂ = x/n (observed proportion)
- x = number of successes (resolved tasks)
- n = number of attempts (total tasks)
- z = 1.96 (for 95% confidence)

For Pass@k, use bootstrap confidence intervals (1000 resamples, 2.5th and 97.5th percentiles).

---

### 5.3 Failure Taxonomy

Classify every failed task into exactly one category:

| Category | Definition | Typical % |
|----------|------------|-----------|
| `compile_error` | Patch fails to compile on GCC and Clang | 20-25% |
| `test_failure` | Compiles but `ctest` / test suite fails | 15-20% |
| `build_sys` | CMake/Ninja/b2 generation failure | 10-15% |
| `policy_violation` | Edited protected paths, skipped tests, weakened assertions | 10-15% |
| `wrong_repo` | Cross-repo: fix applied to incorrect repository | 5-10% |
| `timeout` | Wall-clock or token budget exhausted | 10-15% |
| `unknown` | Infrastructure crash or unclassifiable | 5-10% |

---

### 5.4 Scorecard Template

```yaml
# baseline_scorecard.yaml
evaluation:
  date: 2026-02-05
  protocol_version: "1.0"
  harness_commit: 6c3b8d5

model:
  name: claude-opus-4.5
  provider: anthropic
  training_cutoff: 2025-04-01

baseline: TU  # SS | TU | RE

environment:
  container_digest: sha256:abcd1234...
  retrieval_digest: sha256:5678efgh...  # RE only

hyperparameters:
  temperature: 0.0
  max_iterations: 10
  time_budget_minutes: 30
  token_budget: 300000

summary:
  tasks_total: 60
  tasks_attempted: 60
  tasks_resolved: 37
  resolved_rate: 0.6167
  resolved_rate_ci_95: [0.487, 0.734]
  pass_at_1: 0.5167
  pass_at_10: 0.6167

by_suite:
  clang_issue_fix:
    total: 10
    resolved: 7
    rate: 0.70
  clang_feature:
    total: 8
    resolved: 4
    rate: 0.50
  clang_tests_coverage:
    total: 7
    resolved: 5
    rate: 0.71
  clang_pr_review:
    total: 3
    resolved: 2
    rate: 0.67
  clang_triage:
    total: 2
    resolved: 1
    rate: 0.50
  boost_single_repo:
    total: 20
    resolved: 13
    rate: 0.65
  boost_cross_repo:
    total: 7
    resolved: 3
    rate: 0.43
  boost_build_system:
    total: 3
    resolved: 2
    rate: 0.67

failure_taxonomy:
  compile_error: 8
  test_failure: 6
  build_sys: 4
  policy_violation: 2
  wrong_repo: 2
  timeout: 1
  unknown: 0

efficiency:
  avg_iterations_per_task: 4.2
  avg_tokens_per_task: 78500
  avg_wall_clock_seconds: 612
  total_cpu_hours: 10.2
  estimated_cost_usd: 27.00

contamination:
  tasks_flagged: 3
  tasks_excluded: 3
  safe_resolved_rate: 0.6316
```

---

### 5.5 Scorecard Markdown Template

For human-readable reporting:

```markdown
# Baseline Scorecard: [Model Name] - [Baseline Type]

**Evaluation Date**: YYYY-MM-DD  
**Protocol Version**: 1.0  
**Model**: [name] ([provider])  
**Training Cutoff**: YYYY-MM-DD  

## Summary

| Metric | Value | 95% CI |
|--------|-------|--------|
| Tasks Attempted | N | - |
| Tasks Resolved | X | - |
| Resolved Rate | X.XX% | [X.XX%, X.XX%] |
| Pass@1 | X.XX% | [X.XX%, X.XX%] |

## Results by Suite

| Suite | Total | Resolved | Rate |
|-------|-------|----------|------|
| Clang Issue-Fix | N | X | X.XX% |
| Clang Feature | N | X | X.XX% |
| Clang Tests/Coverage | N | X | X.XX% |
| Clang PR Review | N | X | X.XX% |
| Clang Triage | N | X | X.XX% |
| Boost Single-Repo CI | N | X | X.XX% |
| Boost Cross-Repo CI | N | X | X.XX% |
| Boost Build-System | N | X | X.XX% |

## Failure Analysis

| Failure Mode | Count | % of Failures |
|--------------|-------|---------------|
| Compile Error | N | X.X% |
| Test Failure | N | X.X% |
| Build System | N | X.X% |
| Policy Violation | N | X.X% |
| Wrong Repo | N | X.X% |
| Timeout | N | X.X% |
| Unknown | N | X.X% |

## Efficiency Metrics

| Metric | Value |
|--------|-------|
| Avg Iterations/Task | X.X |
| Avg Tokens/Task | XXXXX |
| Avg Wall-Clock (sec) | XXX |
| Total CPU Hours | X.X |
| Estimated Cost (USD) | $X.XX |

## Contamination Status

| Metric | Value |
|--------|-------|
| Tasks Flagged | N |
| Tasks Excluded | N |
| Safe Resolved Rate | X.XX% |

## Environment

- **Container**: `sha256:...`
- **Retrieval Corpus**: `sha256:...` (RE only)
- **Harness Commit**: `abc123`
```

---

## 6. Anti-Gaming Enforcement

### 6.1 Protected Paths (Default Forbidden)

| Path Pattern | Reason |
|--------------|--------|
| `.github/workflows/*` | Disabling CI jobs |
| `**/CMakeLists.txt` (test-skip patterns) | Reducing test coverage |
| `**/*_test.cpp` (deletion) | Removing tests |
| `**/XFAIL` additions | Marking tests as expected-fail |

### 6.2 Prohibited Patterns

Automatically flag and penalize patches that:

| Pattern | Penalty |
|---------|---------|
| Delete or skip tests | `policy_violation` failure + log |
| Weaken assertions (`ASSERT_EQ` → `EXPECT_EQ`, tolerance broadening) | `policy_violation` failure + log |
| Disable warnings (`-w`, `#pragma warning(disable:...)`) | `policy_violation` failure + log |
| Modify CI config to skip failing jobs | `policy_violation` failure + log |
| Edit files outside `allowed_paths` | `policy_violation` failure + log |

### 6.3 Allowed Exceptions

Cases marked with `suite: ci_config_fix` or explicit `allowed_paths` entries may modify protected files. Such cases must:
- Define success as "CI config now correct" (not "tests pass by skipping")
- Document the exception in the case definition
- Be scored in a separate subsuite

---

## 7. Reproducibility Requirements

### 7.1 Case-Level Requirements

Every benchmark case must specify:

| Field | Required | Description |
|-------|----------|-------------|
| `case_id` | Yes | Unique identifier |
| `suite` | Yes | Benchmark suite name |
| `repo_url` | Yes | Git repository URL |
| `base_sha` | Yes | Exact commit hash for baseline |
| `gold_merge_sha` or `gold_patch` | Yes | Reference solution |
| `environment` | Yes | Container spec or Dockerfile |
| `evaluation_steps` | Yes | Exact commands to verify success |
| `allowed_paths` | No | Explicit whitelist (optional) |
| `forbidden_paths` | Yes | Protected paths for this case |
| `time_budget_minutes` | Yes | Per-case time limit |

### 7.2 Run-Level Requirements

Every baseline run must record:

| Field | Required | Description |
|-------|----------|-------------|
| `run_id` | Yes | Unique run identifier |
| `model` | Yes | Model name and version |
| `baseline` | Yes | SS, TU, or RE |
| `container_digest` | Yes | SHA256 of container image |
| `retrieval_digest` | Conditional | SHA256 of retrieval corpus (RE only) |
| `harness_commit` | Yes | Git commit of evaluation harness |
| `timestamp` | Yes | ISO 8601 start time |

---

## 8. Validation Checklist

Before publishing baseline results, verify:

### Protocol Compliance
- [ ] All runs used the specified container image
- [ ] Time and token budgets were enforced
- [ ] Network was disabled (except retrieval stub for RE)
- [ ] Temperature was set to 0.0
- [ ] All artifacts were captured per Section 3

### Data Integrity
- [ ] Leakage checklist (Section 4.1) completed
- [ ] Excluded cases documented with rationale
- [ ] Confidence intervals computed correctly
- [ ] Failure taxonomy applied consistently

### Reporting
- [ ] Scorecard includes all required fields
- [ ] Results segmented by suite
- [ ] Contamination status reported
- [ ] Environment hashes included

---

## Appendix A: Quick Reference

### Baseline Comparison

| Aspect | SS | TU | RE |
|--------|----|----|-----|
| Iterations | 1 | ≤10 | ≤10 |
| Tools | None | Build/Test | Build/Test + Retrieval |
| Time | 2 min | 30 min | 45 min |
| Tokens | 200K | 300K | 400K |
| Expected Rate | 5-15% | 25-40% | 35-55% |

### Key Dates

| Milestone | Date |
|-----------|------|
| Protocol v1.0 | 2026-02-05 |
| Dataset v0.1 target | TBD |
| First baseline run | TBD |

---

## Appendix B: Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-05 | Initial protocol based on research synthesis |

---

*This protocol is designed to be machine-checkable where possible and human-auditable where judgment is required. For questions or clarifications, file an issue in the benchmark repository.*
