# Scoring Rubric

## Overview

This document defines **how to score agent performance** on coding benchmark cases. The rubric is designed to be:
- **Objective**: Machine-checkable where possible
- **Suite-specific**: Different suites have different success criteria
- **Gaming-resistant**: Penalties for cheating behaviors
- **Comparable**: Two reviewers should arrive at the same score

---

## Scoring Philosophy

### Primary vs. Secondary Metrics

- **Primary metric**: Determines pass/fail and headline score (0-100)
- **Secondary metrics**: Diagnostic data (not used for scoring, but recorded for analysis)

### Pass@1 vs. Pass@k

- **Pass@1** (default): Did the agent succeed on first attempt? Binary 0 or 1.
- **Pass@k**: Did the agent succeed within k attempts? Useful for CI-fix loops.
- **Resolved rate**: Percentage of cases solved in a suite (aggregated Pass@1)

---

## Suite-Specific Scoring

### 1. CI-Fix Suite

**Primary Metric:** `resolved` (binary pass/fail)

**Success Criteria:**
1. All specified GitHub Actions jobs/workflows are GREEN
2. No `fail_to_pass` tests remain failing
3. All `pass_to_pass` tests remain passing (regression check)
4. No policy violations (see penalties below)

**Scoring Formula:**
```
base_score = 100 if all criteria met, else 0
final_score = max(0, base_score - Σ(penalties))
```

**Common Penalties:**
- Protected path edit (e.g., `.github/workflows/**`): **-20 points each**
- Test disabled/skipped: **-30 points**
- CI workflow disabled: **Instant fail (0 points)**
- Excessive diff (>500 lines without justification): **-1 point per 100 lines over**

**Secondary Metrics (recorded but not scored):**
- `attempts`: Number of edit-test cycles
- `wall_clock_seconds`: Time to solution
- `diff_size_lines`: Total lines changed
- `files_touched`: Number of files modified
- `build_warnings_delta`: New warnings introduced

**Example:**
```
Agent edits .github/workflows/ci.yml to skip failing job
→ base_score = 0 (instant fail due to CI workflow edit)
→ final_score = 0
```

---

### 2. Issue-Fix Suite

**Primary Metric:** `resolved` (binary pass/fail)

**Success Criteria:**
1. All `fail_to_pass` tests now pass
2. All `pass_to_pass` tests still pass (no regressions)
3. At least one new or strengthened regression test added (if not already present)
4. Build completes without errors
5. No policy violations

**Scoring Formula:**
```
base_score = 100 if all criteria met, else 0

# Regression test requirement
if no_new_test_added and suite_requires_test:
    base_score -= 40

final_score = max(0, base_score - Σ(penalties))
```

**Common Penalties:**
- No regression test added: **-40 points** (case-dependent)
- Test file deleted: **Instant fail**
- Assertion weakened (e.g., `ASSERT_EQ` → `EXPECT_*`, tolerance increased): **-15 points each**
- Protected path edit (test infrastructure): **-20 points each**

**Secondary Metrics:**
- `test_coverage_delta`: Coverage change (lines/branches)
- `clang_tidy_violations_delta`: Static analysis issues introduced
- `diff_size_lines`
- `wall_clock_seconds`

**Example:**
```
Agent fixes bug, all tests pass, but no regression test added
→ base_score = 100 - 40 = 60
→ No other violations
→ final_score = 60
```

---

### 3. Feature-Implementation Suite

**Primary Metric:** `completeness_score` (0-100)

**Success Criteria:**
1. Implementation matches spec/acceptance criteria
2. Tests added that exercise new functionality
3. Build passes on all target toolchains
4. Documentation updated (if spec requires it)
5. No regressions (`pass_to_pass` tests remain passing)

**Scoring Formula:**
```
completeness_score = (
    0.4 * spec_criteria_met +     # 40% weight
    0.3 * test_quality +           # 30% weight
    0.2 * build_hygiene +          # 20% weight
    0.1 * docs_updated             # 10% weight
)

spec_criteria_met = (criteria_passed / total_criteria) * 100
test_quality = min(100, (tests_added * 20))  # Cap at 100
build_hygiene = 100 if no_warnings else max(0, 100 - warnings_count * 2)
docs_updated = 100 if docs_changed or not_required else 0

final_score = max(0, completeness_score - Σ(penalties))
```

**Common Penalties:**
- Incomplete implementation (only partial features): **-30 points**
- No tests for new code: **-40 points**
- Build warnings introduced: **-2 points per warning**
- Test file deleted: **Instant fail**

**Secondary Metrics:**
- `spec_criteria_count`: Total acceptance criteria
- `spec_criteria_passed`: Number met
- `tests_added`: Count of new tests
- `lines_of_code_added`: Implementation size

**Example:**
```
Agent implements 4/5 spec criteria, adds 3 tests, 2 new warnings
→ spec_criteria_met = 80
→ test_quality = 60 (3 * 20)
→ build_hygiene = 96 (100 - 2*2)
→ docs_updated = 100 (not required)
→ completeness_score = 0.4*80 + 0.3*60 + 0.2*96 + 0.1*100 = 79.2
→ final_score = 79
```

---

### 4. Test-Coverage Suite

**Primary Metric:** `coverage_delta` (percentage point increase)

**Success Criteria:**
1. Coverage increases for target scope (file/dir/component)
2. All existing tests remain passing
3. New tests are meaningful (not trivial/no-op)
4. Test runtime doesn't exceed budget

**Scoring Formula:**
```
base_score = min(100, coverage_delta * 10)  # 10% increase = 100 points

# Runtime penalty
if runtime_seconds > budget_seconds:
    runtime_penalty = (runtime_seconds - budget_seconds) / 10

final_score = max(0, base_score - runtime_penalty - Σ(penalties))
```

**Common Penalties:**
- Trivial tests detected (e.g., empty test, always-pass): **-20 points each**
- Coverage decreased: **Instant fail**
- Tests disabled: **-30 points**
- Runtime exceeds budget by >2x: **Instant fail**

**Secondary Metrics:**
- `coverage_before`: Baseline coverage %
- `coverage_after`: Final coverage %
- `lines_covered_delta`: Absolute line count increase
- `branches_covered_delta`: Branch coverage increase
- `runtime_seconds`: Test suite runtime

**Example:**
```
Agent adds tests, coverage increases 5.2% → 15.9% (+10.7%)
Runtime: 45s (budget: 60s)
→ base_score = min(100, 10.7 * 10) = 100
→ No runtime penalty
→ final_score = 100
```

---

### 5. Refactor Suite

**Primary Metric:** `refactor_quality` (0-100)

**Success Criteria:**
1. All tests pass (behavior preserved)
2. Static analysis metrics improve or stay neutral
3. Code complexity reduced (if measurable)
4. No API/ABI breakage (if applicable)

**Scoring Formula:**
```
refactor_quality = (
    0.5 * regression_safety +      # 50% weight (most critical)
    0.3 * static_analysis_delta +  # 30% weight
    0.2 * complexity_delta         # 20% weight
)

regression_safety = 100 if all_tests_pass else 0
static_analysis_delta = max(-100, min(100, -violations_delta * 5))
complexity_delta = max(-100, min(100, -cyclomatic_delta * 2))

final_score = max(0, refactor_quality - Σ(penalties))
```

**Common Penalties:**
- Behavior change detected: **Instant fail**
- API breakage: **Instant fail**
- Increased cyclomatic complexity: **-2 points per unit**
- New static analysis warnings: **-5 points each**

**Secondary Metrics:**
- `cyclomatic_complexity_before`
- `cyclomatic_complexity_after`
- `clang_tidy_violations_before`
- `clang_tidy_violations_after`
- `diff_size_lines`

---

### 6. Retrieval Suite

**Primary Metric:** `recall@5` or `mrr` (Mean Reciprocal Rank)

**Success Criteria:**
1. Retrieved items include labeled relevant documents (ground truth)
2. Retrieval latency within budget

**Scoring Formula:**
```
# Recall@k
recall_at_k = (relevant_items_in_top_k / total_relevant_items) * 100

# Mean Reciprocal Rank (MRR)
# rank = position of first relevant item (1-indexed)
mrr = (1 / rank) * 100 if relevant_found else 0

# Use whichever is specified as primary for this case
final_score = recall_at_k OR mrr
```

**Common Penalties:**
- Latency exceeds budget: **-10 points per second over**

**Secondary Metrics:**
- `precision@k`: Relevant items / k
- `ndcg@k`: Normalized Discounted Cumulative Gain
- `latency_ms`: Retrieval time

**Example:**
```
Case has 8 relevant documents labeled
Agent retrieves 10 items, top 5 contain 4 relevant docs
→ recall@5 = (4/8) * 100 = 50
→ final_score = 50
```

---

### 7. Review Suite

**Primary Metric:** `review_f1` (F1 score of findings)

**Success Criteria:**
1. Agent identifies issues from labeled ground truth (recall)
2. Agent doesn't produce excessive false positives (precision)
3. Findings are actionable and specific

**Scoring Formula:**
```
precision = true_positives / (true_positives + false_positives)
recall = true_positives / (true_positives + false_negatives)
f1 = 2 * (precision * recall) / (precision + recall)

review_f1 = f1 * 100

final_score = review_f1
```

**Common Penalties:**
- Excessive false positives (>50% FP rate): **-20 points**

**Secondary Metrics:**
- `true_positives`: Correct findings
- `false_positives`: Incorrect findings
- `false_negatives`: Missed issues
- `precision`
- `recall`

---

## Global Penalty Catalog

### Instant Fail Violations (score = 0)

These violations result in **immediate failure** regardless of other success:

1. **CI workflow disabled** (`.github/workflows/` edited to skip failing jobs)
2. **Test file deleted** (without explicit permission in case)
3. **Behavior change in refactor suite** (tests fail)
4. **Test patch modification** (agent edits test files to make them pass, SWE-bench rule)
5. **Timeout exceeded by >3x** (agent takes too long)

### Severe Penalties (20-40 points)

6. **Protected path edit** (default: `-20 points per file`)
   - Forbidden paths typically: tests/**, .github/**, build scripts
   - Unless explicitly allowed in case

7. **Test disabled/skipped** (`-30 points`)
   - Patterns: `DISABLED_`, `@skip`, `#ifdef SKIP_TEST`

8. **No regression test added** (`-40 points`, issue-fix suite)
   - When suite requires test but none added

9. **Assertion weakening** (`-15 points each`)
   - `ASSERT_*` → `EXPECT_*`
   - Tolerance increased (e.g., `1e-6` → `1e-3`)
   - Timeout increased

### Moderate Penalties (5-15 points)

10. **Build warnings introduced** (`-2 points per warning`)

11. **Static analysis violations** (`-5 points each`)
    - clang-tidy warnings
    - cppcheck issues

12. **Trivial/no-op tests** (`-20 points each`)
    - Empty test body
    - Always-pass test

13. **Excessive diff size** (`-1 point per 100 lines over threshold`)
    - Threshold typically 500 lines
    - Indicates potential "shotgun debugging"

### Minor Penalties (1-5 points)

14. **TODO/FIXME comments added** (`-5 points each`)
    - Indicates incomplete work

15. **Commented-out code** (`-2 points per block`)

---

## Scoring Examples (Complete Worked Cases)

### Example 1: CI-Fix Success

**Case:** `boost-ci-gcc-14-fail-001`
**Suite:** ci-fix
**Issue:** GCC 14 build fails with `-Werror=missing-field-initializers`

**Agent Actions:**
1. Identifies missing field initializers in 3 structs
2. Adds explicit initialization: `= {}` or `= nullptr`
3. Runs CI, all jobs green
4. Diff: 8 lines changed across 2 files

**Scoring:**
```
base_score = 100 (all criteria met)
penalties = 0 (no violations)
final_score = 100
```

**Secondary Metrics:**
- attempts: 1
- wall_clock_seconds: 142
- diff_size_lines: 8
- files_touched: 2

---

### Example 2: Issue-Fix with Missing Test

**Case:** `clang-issue-56789`
**Suite:** issue-fix
**Issue:** Clang crashes on constexpr evaluation

**Agent Actions:**
1. Fixes null pointer dereference in `lib/AST/ExprConstant.cpp`
2. All existing tests pass
3. **No new regression test added**

**Scoring:**
```
base_score = 100
penalty_no_test = -40 (suite requires regression test)
penalties_total = 40
final_score = 60
```

**Result:** Partial credit - fix works but lacks test coverage

---

### Example 3: Feature Implementation Partial

**Case:** `clang-feature-c++26-pack-indexing`
**Suite:** feature-impl
**Spec:** 5 acceptance criteria

**Agent Actions:**
1. Implements 3/5 features (60%)
2. Adds 2 tests
3. Introduces 1 build warning
4. No docs (not required)

**Scoring:**
```
spec_criteria_met = 60
test_quality = 40 (2 * 20)
build_hygiene = 98 (100 - 1*2)
docs_updated = 100 (not required)

completeness_score = 0.4*60 + 0.3*40 + 0.2*98 + 0.1*100 = 65.6
final_score = 66
```

**Result:** Incomplete implementation, but partial credit given

---

### Example 4: Gaming Attempt (Caught)

**Case:** `boost-ci-msvc-fail-002`
**Suite:** ci-fix
**Issue:** MSVC tests failing on Windows

**Agent Actions:**
1. Edits `.github/workflows/ci.yml`
2. Changes `if: ${{ matrix.os == 'windows-2022' }}` to skip Windows builds
3. CI is now "green" (because Windows job doesn't run)

**Scoring:**
```
base_score = 0 (instant fail - CI workflow edit is forbidden)
final_score = 0
```

**Violation Detected:** CI workflow modification without permission

---

## Aggregation: Suite-Level and Dataset-Level Scores

### Suite-Level Resolved Rate

```
suite_resolved_rate = (cases_solved / total_cases) * 100

Example:
CI-Fix suite: 18/20 cases solved = 90% resolved rate
Issue-Fix suite: 12/20 cases solved = 60% resolved rate
```

### Dataset-Level Average Score

```
dataset_avg_score = Σ(case_scores) / total_cases

Example:
30 cases, scores: [100, 100, 60, 0, 100, ..., 66]
dataset_avg_score = 2140 / 30 = 71.3
```

### Pass@k Calculation

```
pass_at_k = probability of solving within k attempts

Estimated from n samples, c solved:
pass@1 ≈ c / n
pass@3 ≈ 1 - ((n-c)/n)^3 (for small c/n)
```

---

## Validation and Calibration

### Two-Reviewer Agreement Test

**Procedure:**
1. Select 10 diverse cases
2. Two reviewers independently score same agent runs
3. Calculate inter-rater reliability (IRR)

**Acceptance Criterion:**
- Cohen's Kappa > 0.8 (strong agreement)
- If < 0.8, refine ambiguous scoring rules

### Baseline Calibration

**Procedure:**
1. Run 3 baseline agents (simple, moderate, advanced)
2. Verify scores align with expected capabilities
3. Ensure rubric distinguishes between skill levels

**Acceptance Criterion:**
- Simple baseline: 20-40% resolved rate
- Moderate baseline: 50-70% resolved rate
- Advanced baseline: 80-95% resolved rate

---

## References

This rubric is informed by:
- **SWE-bench Verified**: FAIL_TO_PASS and PASS_TO_PASS test methodology ([OpenAI SWE-bench](https://openai.com/index/introducing-swe-bench-verified/))
- **Defects4C/ManyBugs**: Partial fix scoring in automated program repair
- **LiveCodeBench**: Contamination-resistant evaluation practices
- **CompilerGym**: Compiler optimization benchmarking
- **ACM Reproducibility Guidelines**: Deterministic evaluation standards

**Sources:**
- [Introducing SWE-bench Verified | OpenAI](https://openai.com/index/introducing-swe-bench-verified/)
- [SWE-bench Evaluation Guide](https://www.swebench.com/SWE-bench/guides/evaluation/)
- [Cognition SWE-bench Technical Report](https://cognition.ai/blog/swe-bench-technical-report)

---

**Version History:**
- v0.1.0 (2026-02-04): Initial draft for Issue #2
