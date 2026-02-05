# Case Admission Checklist

## Overview

This checklist gates **case admission to the benchmark dataset**. Every case MUST pass all required checks before being added. This ensures dataset quality, reproducibility, and credibility.

**Purpose:**
- Prevent non-reproducible cases from entering dataset
- Ensure gold solutions actually work
- Verify cases are unambiguous and solvable
- Screen for leakage and gaming vulnerabilities

**Process:**
1. Curator prepares case (fills out schema)
2. Run automated checks (schema validation, path existence)
3. Manual review (human verification of quality)
4. Determinism testing (3x rerun protocol)
5. Approve or reject with documented reasoning

---

## Phase 1: Automated Checks (Gate 1)

These checks MUST pass before human review. Automated via `validate_case.py` script.

### ✅ Check 1.1: Schema Validation

**Requirement:** Case JSON validates against `case-schema.json`

**Command:**
```bash
ajv validate -s schema/case-schema.json -d cases/candidate.json
```

**Pass Criteria:**
- No schema validation errors
- All required fields present
- Field types correct (e.g., SHA is 40-char hex, URLs are valid)

**Failure Modes:**
- Missing required field → **REJECT**
- Invalid format (e.g., SHA is 39 chars) → **REJECT**
- Wrong enum value (e.g., suite="unknown") → **REJECT**

---

### ✅ Check 1.2: File Artifacts Exist

**Requirement:** All referenced files/paths exist and are accessible

**Checks:**
- `repo_url` is accessible (HTTP 200)
- `base_sha` exists in repository
- `gold_outcome.patch_file` exists (if type=patch_file)
- `gold_outcome.validation_proof.log_file` exists (if specified)

**Command:**
```bash
python scripts/check_artifacts.py cases/candidate.json
```

**Pass Criteria:**
- All file paths resolve
- All URLs return 2xx status
- All SHAs exist in git history

**Failure Modes:**
- Repo URL 404 → **REJECT** (fix URL)
- SHA not in repo history → **REJECT** (verify SHA)
- Missing patch file → **REJECT** (add file or change to inline)

---

### ✅ Check 1.3: Path Constraints Are Valid

**Requirement:** `forbidden_paths` and `allowed_paths` globs are valid

**Checks:**
- Glob patterns compile without errors
- No contradiction (path in both allowed & forbidden)
- Patterns match at least one file in repo (not empty)

**Command:**
```python
import glob
for pattern in case['constraints']['forbidden_paths']:
    matches = glob.glob(pattern, root_dir=repo_root)
    assert len(matches) > 0, f"Pattern {pattern} matches nothing"
```

**Pass Criteria:**
- All patterns valid
- No allowed/forbidden overlap
- Patterns match expected files

**Failure Modes:**
- Invalid glob syntax → **REJECT**
- Pattern matches nothing → **WARNING** (may be intentional)

---

## Phase 2: Reproducibility Verification (Gate 2)

These checks verify the case is reproducible and deterministic.

### ✅ Check 2.1: Baseline Fails at base_sha

**Requirement:** At `base_sha`, evaluation steps MUST fail

**Protocol:**
```bash
# 1. Clone repo
git clone $REPO_URL repo
cd repo
git checkout $BASE_SHA

# 2. Run setup steps
for cmd in case['setup_steps']:
    eval "$cmd" || exit 1

# 3. Run evaluation steps (expect failure)
for cmd in case['evaluation_steps']:
    eval "$cmd"
    if [ $? -eq 0 ]; then
        echo "VIOLATION: Evaluation passed at baseline (should fail)"
        exit 1
    fi
done
```

**Pass Criteria:**
- All `evaluation_steps` fail (exit code != 0)
- Specific `fail_to_pass` tests are failing
- All `pass_to_pass` tests are passing (if specified)

**Failure Modes:**
- Baseline passes → **REJECT** (case is not solvable, baseline already works)
- Wrong tests failing → **REJECT** (verify fail_to_pass list)
- pass_to_pass tests failing → **REJECT** (baseline is broken, not just issue)

---

### ✅ Check 2.2: Gold Outcome Passes

**Requirement:** Gold solution makes evaluation steps pass

**Protocol:**
```bash
# 1. Start from baseline
git checkout $BASE_SHA

# 2. Apply gold solution
if [ "$GOLD_TYPE" == "merge_sha" ]; then
    git checkout $GOLD_MERGE_SHA
elif [ "$GOLD_TYPE" == "patch_file" ]; then
    git apply $GOLD_PATCH_FILE
elif [ "$GOLD_TYPE" == "patch_inline" ]; then
    echo "$GOLD_PATCH_INLINE" | git apply
fi

# 3. Run evaluation steps (expect success)
for cmd in case['evaluation_steps']:
    eval "$cmd" || exit 1
done
```

**Pass Criteria:**
- All `evaluation_steps` pass (exit code = 0)
- All `fail_to_pass` tests now pass
- All `pass_to_pass` tests still pass (no regressions)

**Failure Modes:**
- Gold doesn't apply cleanly → **REJECT** (update patch)
- Gold fails evaluation → **REJECT** (gold is wrong)
- Gold causes regressions → **REJECT** (gold breaks existing tests)

---

### ✅ Check 2.3: FAIL→PASS and PASS→PASS Verification

**Requirement:** Specific tests transition correctly

**Protocol:**
```bash
# At baseline
git checkout $BASE_SHA
run_tests > baseline_results.txt

# Extract fail_to_pass test status
for test in case['fail_to_pass']:
    grep "$test" baseline_results.txt | grep "FAIL" || echo "ERROR: Should fail"
done

# Extract pass_to_pass test status
for test in case['pass_to_pass']:
    grep "$test" baseline_results.txt | grep "PASS" || echo "ERROR: Should pass"
done

# At gold
git apply $GOLD_PATCH
run_tests > gold_results.txt

# Verify fail_to_pass now passes
for test in case['fail_to_pass']:
    grep "$test" gold_results.txt | grep "PASS" || echo "ERROR: Should pass"
done

# Verify pass_to_pass still passes
for test in case['pass_to_pass']:
    grep "$test" gold_results.txt | grep "PASS" || echo "ERROR: Should still pass"
done
```

**Pass Criteria:**
- All fail_to_pass tests: FAIL at baseline, PASS at gold
- All pass_to_pass tests: PASS at baseline, PASS at gold

**Failure Modes:**
- fail_to_pass already passing at baseline → **REJECT** (wrong test list)
- fail_to_pass still failing at gold → **REJECT** (gold doesn't fix)
- pass_to_pass failing at baseline → **REJECT** (test was already broken)
- pass_to_pass failing at gold → **REJECT** (gold introduces regression)

---

### ✅ Check 2.4: Determinism Verification (3x Rerun)

**Requirement:** Case produces same result on multiple runs

**Protocol:**
```bash
# Clone ONCE, copy 3 times to ensure identical state
# (prevents repo state changes between runs)
git clone $REPO_URL repo-baseline
cd repo-baseline
git checkout $BASE_SHA
cd ..

# Run 3 times from identical copies
for i in {1..3}; do
    # Copy from frozen baseline
    rm -rf repo-test-$i
    cp -r repo-baseline repo-test-$i
    cd repo-test-$i

    # Run in isolated process with frozen time (prevents time-dependent flakiness)
    faketime '2026-01-01 00:00:00' run_evaluation > ../results-$i.txt 2>&1
    EXITCODE=$?
    echo "$EXITCODE" > ../exitcode-$i.txt
    cd ..
done

# Compare results
diff results-1.txt results-2.txt
diff results-2.txt results-3.txt
diff exitcode-1.txt exitcode-2.txt

# Optional: Test on different OS/architectures (recommended for cross-platform cases)
# docker run --rm -v $(pwd)/repo-baseline:/work ubuntu:22.04 bash -c "cd /work && run_evaluation"
# docker run --rm -v $(pwd)/repo-baseline:/work alpine:3.19 bash -c "cd /work && run_evaluation"
```

**Pass Criteria:**
- All 3 runs produce identical results (text and exit codes)
- No flakiness or non-deterministic failures

**Failure Modes:**
- Different results across runs → **QUARANTINE** (flaky case, needs investigation)
- Intermittent passes/fails → **QUARANTINE** (timing-dependent)

**Flakiness Tolerance:**
- 0 tolerance for pass/fail differences
- Minor timing differences OK if not affecting correctness

---

### ✅ Check 2.5: Environmental Validation (o3-Recommended)

**Requirement:** Verify baseline failure is not due to environmental factors

**Rationale:** Real-world CI issues (especially for Clang/Boost) can be affected by library versions, network dependencies, or OS-specific behavior. This check ensures the failure is intrinsic to the code, not the environment.

**Protocol:**
```bash
# 1. Validate environment matches specification
if [ -n "$case['environment']['build_options']['sanitizers']" ]; then
    # Check sanitizer libraries are available
    ldconfig -p | grep -E 'libasan|libubsan|libtsan' || echo "WARN: Sanitizers not installed"
fi

# 2. Check for external dependencies
# Parse setup_steps for network calls
grep -E 'curl|wget|apt-get|pip install' case['setup_steps'] && echo "WARN: Network dependency detected"

# 3. Verify compiler version matches
ACTUAL_VERSION=$(gcc --version | head -n1)
REQUIRED_VERSION=$case['environment']['compiler']['version']
[[ "$ACTUAL_VERSION" =~ "$REQUIRED_VERSION" ]] || echo "WARN: Compiler version mismatch"

# 4. Run in isolated container (recommended)
# Capture WHICH tests fail, not just that evaluation fails
run_evaluation > host_failures.txt 2>&1
docker run --rm -v $(pwd):/work $case['environment']['container_image'] \
    bash -c "cd /work && run_evaluation" > container_failures.txt 2>&1

# Compare failure patterns (same tests must fail in both environments)
diff <(grep "FAILED:" host_failures.txt | sort) \
     <(grep "FAILED:" container_failures.txt | sort)

if [ $? -ne 0 ]; then
    echo "REJECT: Different failures in different environments"
    echo "Host failures may be due to actual bug, container failures may be due to missing dependencies"
    exit 1
fi
```

**Pass Criteria:**
- Baseline failure occurs both in host and containerized environment
- No external network dependencies unless explicitly documented
- Environment specification (OS, compiler, sanitizers) is complete and correct

**Failure Modes:**
- Failure only occurs in specific environment → **REJECT** (document exact environment or fix case)
- Missing sanitizer libraries cause false failures → **REJECT** (update environment spec)
- Network dependency causes intermittent failures → **QUARANTINE** or update setup_steps

**Note:** This check is especially critical for Clang (compiler warnings vary by version) and Boost (library interactions sensitive to stdlib version).

---

## Phase 3: Quality Review (Gate 3)

Manual human review for content quality and anti-gaming.

### ✅ Check 3.1: Prompt Quality

**Requirement:** `prompt_markdown` is clear, unambiguous, and solvable

**Reviewer Questions:**
1. Is the problem statement clear?
2. Are acceptance criteria unambiguous?
3. Is the prompt self-contained (minimal context needed)?
4. Does prompt avoid leaking the solution?

**Pass Criteria:**
- Prompt is understandable without deep domain knowledge
- No direct code snippets from gold solution in prompt
- Issue description matches actual failure behavior

**Failure Modes:**
- Prompt is too vague → **REJECT** (clarify requirements)
- Prompt contains solution → **REJECT** (leakage, remove details)
- Prompt contradicts gold solution → **REJECT** (fix inconsistency)

---

### ✅ Check 3.2: Leakage Screening

**Requirement:** Solution is not contained in prompt, comments, or issue thread

**Checks:**
1. Prompt doesn't contain code from gold patch
2. Issue comments (if from real issue) don't reveal solution
3. PR description (if from real PR) is excluded from prompt

**Protocol:**
```python
# Extract gold patch code
gold_code = extract_code_from_patch(case['gold_outcome'])

# Check for leakage in prompt
prompt = case['prompt_markdown']
similarity = fuzzy_match(prompt, gold_code)

if similarity > 0.7:  # >70% similarity
    print("WARNING: Potential leakage detected")
```

**Pass Criteria:**
- No code from gold solution in prompt
- Issue discussion doesn't directly state the fix
- Context hints don't over-constrain to single solution

**Failure Modes:**
- Direct code leakage → **REJECT** (rewrite prompt)
- Solution obvious from hints → **WARNING** (reduce hints)

---

### ✅ Check 3.3: Difficulty Calibration

**Requirement:** Difficulty label matches case complexity

**Heuristics:**
- **Easy**: 1-2 files, <50 lines changed, single component
- **Medium**: 3-5 files, 50-200 lines, multiple components
- **Hard**: 6+ files, >200 lines, cross-component, requires domain knowledge
- **Expert**: Architecture changes, performance optimization, subtle correctness

**Checks:**
1. Count files in gold patch
2. Count lines changed
3. Assess component count
4. Human judgment on domain knowledge required

**Pass Criteria:**
- Difficulty label roughly matches heuristics
- Edge cases documented in `metadata.notes`

**Failure Modes:**
- Mislabeled (e.g., marked "easy" but requires 10+ files) → **WARNING** (relabel)

---

### ✅ Check 3.4: Anti-Gaming Vulnerability Scan

**Requirement:** Case is not easily gamed by trivial modifications

**Reviewer Questions:**
1. Can agent skip all tests to "pass"? (protected paths set correctly?)
2. Can agent weaken assertions to pass?
3. Can agent disable CI to avoid failure?
4. Are test files protected from modification?

**Checks:**
- `constraints.forbidden_paths` includes tests/ (unless explicitly allowed)
- `constraints.forbidden_paths` includes .github/workflows/
- Evaluation includes pass_to_pass regression checks

**Pass Criteria:**
- Default protections in place
- Custom allowed_paths are justified and documented

**Failure Modes:**
- No path protections → **REJECT** (add forbidden_paths)
- Tests not protected → **REJECT** (add tests/** to forbidden)

---

## Phase 4: Multi-Repo Cases (Gate 4)

Additional checks for cross-repo attribution cases.

### ✅ Check 4.1: Workspace Definition Complete

**Requirement:** All repos in workspace are pinned with SHAs

**Checks:**
- `multi_repo.workspace_repos` lists all dependencies
- Each repo has valid URL and 40-char SHA
- Repo checkout order is specified (if matters)

**Pass Criteria:**
- Workspace can be reproduced exactly
- All dependency SHAs exist

**Failure Modes:**
- Missing dependency → **REJECT** (add to workspace_repos)
- Invalid SHA → **REJECT** (fix SHA)

---

### ✅ Check 4.2: Attribution Ground Truth Verified

**Requirement:** Human has verified which repo the fix belongs in

**Checks:**
- `multi_repo.attribution.correct_repo` is specified
- `multi_repo.attribution.confidence` is 70-100% (not guessed)
- `multi_repo.attribution.reasoning` is documented

**Protocol:**
1. Human curator manually traces failure to source
2. Applies gold patch to correct repo
3. Verifies end-to-end workflow passes
4. Documents reasoning

**Pass Criteria:**
- Curator has high confidence (80%+) in attribution
- Reasoning is documented and reviewable
- Gold patch actually fixes when applied to correct repo

**Failure Modes:**
- Low confidence (<70%) → **REJECT** (investigate further)
- Attribution unclear → **QUARANTINE** (flag for expert review)

---

### ✅ Check 4.3: Cross-Repo Evaluation Works

**Requirement:** Evaluation can test fixes in any allowed repo

**Protocol:**
```bash
# Test that workspace builds correctly
checkout_workspace(case['multi_repo']['workspace_repos'])

# Test fix in primary repo
apply_patch_to_repo(case['multi_repo']['primary_repo'], gold_patch)
run_evaluation()  # Should pass

# Test fix in wrong repo (should fail)
reset_workspace()
apply_patch_to_repo(case['multi_repo']['primary_repo'], empty_patch)
apply_patch_to_repo(wrong_repo, gold_patch)
run_evaluation()  # Should fail (validates attribution)
```

**Pass Criteria:**
- Workspace builds successfully
- Fix in correct repo passes evaluation
- Fix in wrong repo fails evaluation (validates ground truth)

**Failure Modes:**
- Workspace doesn't build → **REJECT** (fix workspace definition)
- Fix works in multiple repos → **REJECT** (ambiguous attribution, not suitable)

---

## Phase 5: Final Approval (Gate 5)

### ✅ Check 5.1: Metadata Complete

**Requirement:** All required metadata fields filled out

**Fields to verify:**
- `case_id` is unique in dataset
- `dataset_version` matches current version
- `metadata.curator` is specified
- `metadata.created_date` is set
- `labels` are appropriate

**Pass Criteria:**
- No missing metadata
- case_id doesn't conflict with existing cases

---

### ✅ Check 5.2: Documentation and Rationale

**Requirement:** Case has clear rationale for inclusion

**Questions:**
1. Why is this case valuable for the benchmark?
2. What capability does it test?
3. Is it representative of real-world tasks?

**Pass Criteria:**
- Rationale documented in `metadata.notes`
- Case fits suite definition
- Not a duplicate of existing case

**Failure Modes:**
- No clear purpose → **REJECT** (justify or drop)
- Duplicate of existing case → **REJECT** (redundant)

---

### ✅ Check 5.3: Sign-Off

**Requirement:** Two reviewers approve with high inter-rater reliability

**Process:**
1. Primary curator prepares case
2. Reviewer 1 runs automated checks (Gates 1-2)
3. Reviewer 2 does quality review (Gate 3)
4. Both sign off in `metadata.reviewers`
5. **Inter-rater reliability check:** Both reviewers independently assess case quality on key dimensions (reproducibility, clarity, difficulty, anti-gaming protection) using a 1-5 scale. Calculate Cohen's Kappa or Spearman correlation.

**Pass Criteria:**
- Both reviewers approve
- All gate checks passed
- Any warnings documented and justified
- **Inter-rater reliability ≥ 0.85** (measured via Cohen's Kappa on quality dimensions, or correlation ≥ 0.85 on difficulty rating)

**Note:** The 0.85 threshold follows 2025 expert consensus standards for evaluator qualification in benchmark datasets.

---

## Rejection Reasons Catalog

Document why cases are rejected for transparency.

| Rejection Code | Reason | Resolution |
|---------------|--------|------------|
| R1-SCHEMA | Schema validation failed | Fix JSON format, add missing fields |
| R2-ARTIFACTS | Referenced files don't exist | Add missing files or fix paths |
| R3-NO-FAIL | Baseline doesn't fail | Verify base_sha, check fail_to_pass list |
| R4-GOLD-FAIL | Gold solution doesn't pass | Fix gold patch, verify evaluation steps |
| R5-REGRESSION | Gold causes regressions | Fix gold patch to preserve pass_to_pass |
| R6-FLAKY | Non-deterministic results | Quarantine, investigate flakiness |
| R7-LEAKAGE | Solution in prompt | Rewrite prompt without code snippets |
| R8-UNCLEAR | Prompt ambiguous | Clarify requirements, add context |
| R9-NO-PROTECTION | Missing anti-gaming protections | Add forbidden_paths constraints |
| R10-DUPLICATE | Duplicate of existing case | Drop or merge with existing |
| R11-LOW-QUALITY | Trivial or not representative | Justify value or drop |

---

## Quarantine Process

For flaky or suspicious cases:

1. **Tag as quarantined:**
   ```json
   "metadata": {
     "quarantined": true,
     "quarantine_reason": "Intermittent failures in Check 2.4 (determinism)",
     "quarantine_date": "2026-02-04"
   }
   ```

2. **Investigate:**
   - Run 10x to characterize flakiness
   - Check for timing dependencies, network calls, randomness
   - Document findings

3. **Resolution:**
   - Fix case → Remove quarantine, admit
   - Can't fix → Permanent quarantine (exclude from evaluation)
   - Document outcome

---

## Admission Rate Targets

**Quality over quantity:**
- Expect 30-50% rejection rate in early dataset building
- As process matures, aim for 70%+ acceptance rate
- Maintain high bar: better 50 good cases than 100 mediocre ones

---

## Tools and Scripts

### Case Validator CLI

```bash
# Run full admission checks
python scripts/validate_case.py cases/candidate.json

# Output:
# ✅ Check 1.1: Schema validation PASSED
# ✅ Check 1.2: Artifacts exist PASSED
# ✅ Check 2.1: Baseline fails PASSED
# ✅ Check 2.2: Gold passes PASSED
# ❌ Check 2.4: Determinism FAILED (2/3 runs passed)
#
# RESULT: QUARANTINE (1 failure)
```

### Bulk Validation

```bash
# Validate all candidate cases
find cases/candidates/ -name "*.json" | \
  xargs -I {} python scripts/validate_case.py {}

# Generate admission report
python scripts/generate_admission_report.py cases/candidates/ > report.md
```

---

## Case Lifecycle

```
[Candidate] → [Automated Checks] → [Manual Review] → [Determinism Test] → [Approved]
     ↓              ↓                   ↓                  ↓                   ↓
  [Rejected]    [Rejected]          [Rejected]       [Quarantined]      [Dataset]
```

---

## Summary Checklist (For Quick Reference)

**Phase 1: Automated**
- [ ] Schema validates
- [ ] Artifacts exist
- [ ] Paths are valid

**Phase 2: Reproducibility**
- [ ] Baseline fails
- [ ] Gold passes
- [ ] FAIL→PASS / PASS→PASS verified
- [ ] Deterministic (3x rerun)

**Phase 3: Quality**
- [ ] Prompt is clear
- [ ] No solution leakage
- [ ] Difficulty calibrated
- [ ] Anti-gaming protections in place

**Phase 4: Multi-Repo (if applicable)**
- [ ] Workspace complete
- [ ] Attribution verified
- [ ] Cross-repo evaluation works

**Phase 5: Final**
- [ ] Metadata complete
- [ ] Documentation and rationale
- [ ] Two-reviewer sign-off

---

## References

- **SWE-bench Verification**: Human-validated screening process ([OpenAI SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/))
- **ACM Reproducibility Badges**: [ACM Artifact Review and Badging](https://www.acm.org/publications/policies/artifact-review-and-badging-current)
- **Papers With Code**: Dataset validation requirements

---

**Version History:**
- v0.1.0 (2026-02-04): Initial checklist for Issue #2
