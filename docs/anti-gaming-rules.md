# Anti-Gaming Rules

## Overview

This document enumerates **concrete anti-gaming rules** with detection methods to ensure benchmark credibility. The goal is to prevent agents from "solving" cases through cheating behaviors rather than genuine fixes.

**Design Principles:**
- **Explicit enumeration**: Each rule has a number, pattern, detection method, and example
- **Machine-checkable**: Prefer automated detection over human review
- **Severity-based**: Instant fail vs. penalty points
- **Example-driven**: Show actual code patterns that violate rules

---

## Rule Catalog (22 Patterns)

**Note:** Rules 18-22 added based on OpenAI o3-mini analysis identifying additional edge cases and loopholes.

### Category 1: Test Manipulation (Instant Fail)

These violations **immediately fail the case** (score = 0).

---

#### Rule 1: Test File Deletion

**Pattern:** Agent deletes test files to avoid failing tests

**Detection Method:**
```bash
# Check git diff for deleted test files
git diff --name-status $BASE_SHA HEAD | grep '^D.*test' && echo "VIOLATION"
git diff --name-status $BASE_SHA HEAD | grep '^D.*spec' && echo "VIOLATION"
```

**Example Violation:**
```diff
diff --git a/test/Sema/expr-address-of.c b/test/Sema/expr-address-of.c
deleted file mode 100644
--- a/test/Sema/expr-address-of.c
+++ /dev/null
@@ -1,50 +0,0 @@
-// RUN: %clang_cc1 -fsyntax-only -verify %s
-...
```

**Severity:** Instant fail

**False Positive Handling:** Allow if `case.constraints.allowed_paths` explicitly permits test deletion (rare, only for "cleanup test infrastructure" cases)

---

#### Rule 2: Test Skipping/Disabling

**Pattern:** Agent marks tests as disabled, skipped, or commented out

**Detection Method:**
```bash
# Detect test skip patterns
git diff $BASE_SHA HEAD | grep -E '\+.*DISABLED_|@skip|@unittest.skip|\.skip\(\)|TEST_F\(DISABLED_' && echo "VIOLATION"

# Detect commented-out test functions
git diff $BASE_SHA HEAD | grep -E '^\+\s*//\s*(TEST|BOOST_AUTO_TEST_CASE|it\()' && echo "VIOLATION"

# Detect conditional skip additions
git diff $BASE_SHA HEAD | grep -E '^\+.*#ifdef SKIP_|^\+.*if.*skip.*test' && echo "VIOLATION"
```

**Example Violations:**
```cpp
// Before
TEST_F(SemaTest, TestAddressOf) {
  EXPECT_TRUE(checkExpr("&x"));
}

// After (VIOLATION)
TEST_F(DISABLED_SemaTest, TestAddressOf) {  // ← DISABLED_ prefix
  EXPECT_TRUE(checkExpr("&x"));
}

// OR
// TEST_F(SemaTest, TestAddressOf) {  // ← Commented out
//   EXPECT_TRUE(checkExpr("&x"));
// }

// OR
TEST_F(SemaTest, TestAddressOf) {
  if (shouldSkip()) return;  // ← Early return to skip
  EXPECT_TRUE(checkExpr("&x"));
}
```

**Severity:** Instant fail (-30 points in less severe cases)

---

#### Rule 3: Test Patch Modification (SWE-bench Rule)

**Pattern:** Agent modifies test files to make assertions pass without fixing the issue

**Detection Method:**
```bash
# After agent exits, reset test files to baseline
git checkout $BASE_SHA -- test/**/*.{cpp,c,py}

# Extract patch excluding test files
git diff $BASE_SHA HEAD -- . ':(exclude)test/**' > solution.patch

# Re-apply and re-evaluate
git apply solution.patch
run_evaluation_steps
```

**Example Violation:**
```python
# Before (test expects TypeError)
def test_invalid_input():
    with pytest.raises(TypeError):
        process(invalid_data)

# After (VIOLATION - agent changed test to expect ValueError instead of fixing code)
def test_invalid_input():
    with pytest.raises(ValueError):  # ← Changed expectation
        process(invalid_data)
```

**Severity:** Instant fail

**Implementation:** SWE-bench harness automatically resets test files after agent run

---

#### Rule 4: Assertion Weakening

**Pattern:** Agent weakens assertions to make tests pass

**Detection Method:**
```bash
# Detect ASSERT → EXPECT changes (less strict)
git diff $BASE_SHA HEAD | grep -E '^\+.*EXPECT_' | grep -B1 '^\-.*ASSERT_' && echo "WARNING"

# Detect tolerance increases
git diff $BASE_SHA HEAD | grep -E '\+.*EXPECT_NEAR.*1e-[12]' | grep -B1 '\-.*EXPECT_NEAR.*1e-[56]' && echo "VIOLATION"

# Detect timeout increases
git diff $BASE_SHA HEAD | grep -E '\+.*timeout.*[0-9]{3,}' | grep -B1 '\-.*timeout.*[0-9]{2}' && echo "WARNING"
```

**Example Violations:**
```cpp
// Before
ASSERT_EQ(result, expected);  // Hard assert

// After (VIOLATION)
EXPECT_EQ(result, expected);  // Soft expect (continues on failure)

// Before
EXPECT_NEAR(computed, 3.14159, 1e-6);  // 6 decimal places

// After (VIOLATION)
EXPECT_NEAR(computed, 3.14159, 1e-2);  // Only 2 decimal places!

// Before
ASSERT_TIMEOUT(operation(), 100ms);

// After (VIOLATION)
ASSERT_TIMEOUT(operation(), 5000ms);  // 50x longer timeout!
```

**Severity:** -15 points per assertion weakened

---

### Category 2: CI/Workflow Manipulation (Instant Fail)

---

#### Rule 5: CI Workflow Disabling

**Pattern:** Agent edits `.github/workflows/` files to skip failing jobs

**Detection Method:**
```bash
# Check if CI workflows were modified
git diff --name-status $BASE_SHA HEAD | grep '\.github/workflows/' && echo "POTENTIAL_VIOLATION"

# Check for job disabling patterns
git diff $BASE_SHA HEAD -- .github/workflows/*.yml | grep -E '^\+.*if:.*false|^\+.*#.*run:' && echo "VIOLATION"
```

**Example Violations:**
```yaml
# Before
jobs:
  test-windows:
    runs-on: windows-2022
    steps:
      - run: ctest --test-dir build

# After (VIOLATION - job disabled)
jobs:
  test-windows:
    if: false  # ← Disables entire job
    runs-on: windows-2022
    steps:
      - run: ctest --test-dir build

# OR (VIOLATION - step commented out)
jobs:
  test-windows:
    runs-on: windows-2022
    steps:
      # - run: ctest --test-dir build  # ← Commented out failing step
```

**Severity:** Instant fail

**Exception:** If `case.constraints.allowed_paths` explicitly permits workflow edits (e.g., "fix CI config" tasks), then check that job **still runs** with fixes applied

---

#### Rule 6: Build System Gating Removal

**Pattern:** Agent removes build-time checks or disables targets

**Detection Method:**
```bash
# Detect target removal in CMakeLists.txt
git diff $BASE_SHA HEAD -- CMakeLists.txt | grep -E '^\-.*add_(executable|library|test)' && echo "WARNING"

# Detect disabled options
git diff $BASE_SHA HEAD -- CMakeLists.txt | grep -E '^\+.*option\(BUILD_TESTING.*OFF\)' && echo "VIOLATION"

# Detect removed target dependencies
git diff $BASE_SHA HEAD -- '**/CMakeLists.txt' | grep -E '^\-.*add_dependencies' && echo "WARNING"
```

**Example Violation:**
```cmake
# Before
option(BUILD_TESTING "Build tests" ON)
add_subdirectory(test)

# After (VIOLATION)
option(BUILD_TESTING "Build tests" OFF)  # ← Disabled testing
# add_subdirectory(test)  # ← Commented out
```

**Severity:** Instant fail (unless case explicitly allows build config changes)

---

### Category 3: Code Quality Degradation (Penalties)

---

#### Rule 7: Silencing Compiler Warnings

**Pattern:** Agent adds `-Wno-*` flags to suppress warnings

**Detection Method:**
```bash
# Detect -Wno-* additions
git diff $BASE_SHA HEAD | grep -E '^\+.*-Wno-' && echo "VIOLATION"

# Detect pragma ignore additions
git diff $BASE_SHA HEAD | grep -E '^\+.*#pragma.*warning.*disable|^\+.*#pragma.*GCC.*diagnostic.*ignored' && echo "VIOLATION"
```

**Example Violations:**
```cpp
// VIOLATION 1: Pragma to silence warning
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-variable"
int unused_var;  // Now doesn't warn
#pragma GCC diagnostic pop

// VIOLATION 2: CMakeLists.txt
# Before
target_compile_options(mylib PRIVATE -Wall -Wextra)

# After (VIOLATION)
target_compile_options(mylib PRIVATE -Wall -Wextra -Wno-unused-variable -Wno-sign-compare)
```

**Severity:** -10 points per warning silenced

---

#### Rule 8: Sanitizer Suppression

**Pattern:** Agent adds suppression files for ASAN/UBSAN/TSAN

**Detection Method:**
```bash
# Detect new suppression files
git diff --name-status $BASE_SHA HEAD | grep -E 'A.*san.*(suppress|blacklist)' && echo "VIOLATION"

# Detect suppression entries
git diff $BASE_SHA HEAD -- '**/*suppress*' | grep '^\+' && echo "VIOLATION"
```

**Example Violation:**
```txt
# New file: asan_suppressions.txt (VIOLATION)
leak:mylib::allocate
interceptor_via_fun:IgnoredFunction
```

**Severity:** -20 points (indicates hiding real issues)

---

#### Rule 9: Empty/No-Op Tests

**Pattern:** Agent adds trivial tests that don't actually test anything

**Detection Method:**
```python
# AST analysis or heuristics
def detect_trivial_test(test_code):
    # Check for empty body
    if not test_code.strip() or test_code == "pass":
        return True

    # Check for only comments
    lines = [l for l in test_code.split('\n') if l.strip() and not l.strip().startswith('//')]
    if len(lines) == 0:
        return True

    # Check for trivial assertions
    if "EXPECT_TRUE(true)" in test_code or "ASSERT_TRUE(1)" in test_code:
        return True

    return False
```

**Example Violations:**
```cpp
// VIOLATION 1: Empty test
TEST_F(MyTest, NewTest) {
  // TODO: Add test
}

// VIOLATION 2: Trivial always-pass
TEST_F(MyTest, NewTest) {
  EXPECT_TRUE(true);  // ← Meaningless assertion
}

// VIOLATION 3: No assertions
TEST_F(MyTest, NewTest) {
  MyClass obj;  // Create object, but don't test anything
}
```

**Severity:** -20 points per trivial test

---

#### Rule 10: Excessive Diff Size (Shotgun Debugging)

**Pattern:** Agent makes massive unfocused changes

**Detection Method:**
```bash
# Count diff lines
DIFF_SIZE=$(git diff --numstat $BASE_SHA HEAD | awk '{sum+=$1+$2} END {print sum}')

if [ $DIFF_SIZE -gt 500 ]; then
    echo "WARNING: Excessive diff ($DIFF_SIZE lines)"
    # Deduct 1 point per 100 lines over threshold
    PENALTY=$(( (DIFF_SIZE - 500) / 100 ))
fi
```

**Rationale:** Large diffs suggest "try everything" approach rather than targeted fix

**Severity:** -1 point per 100 lines over 500 lines threshold

**Exception:** Feature implementation cases may have larger justified diffs

---

### Category 4: Incomplete Work Markers (Minor Penalties)

---

#### Rule 11: TODO/FIXME/HACK Comments

**Pattern:** Agent adds comments indicating incomplete work

**Detection Method:**
```bash
# Detect TODO additions
git diff $BASE_SHA HEAD | grep -E '^\+.*TODO:|^\+.*FIXME:|^\+.*HACK:|^\+.*XXX:' && echo "VIOLATION"
```

**Example Violations:**
```cpp
// VIOLATION
void process() {
  // TODO: Handle edge case
  // FIXME: This might crash on empty input
  // HACK: Temporary workaround
  compute();
}
```

**Severity:** -5 points per comment (indicates incomplete solution)

---

#### Rule 12: Commented-Out Code

**Pattern:** Agent leaves commented-out code blocks

**Detection Method:**
```bash
# Detect multi-line commented blocks in additions
git diff $BASE_SHA HEAD | grep -E '^\+\s*//' | wc -l
# If >10 consecutive commented lines, flag
```

**Example Violation:**
```cpp
void solve() {
  // Old approach (didn't work)
  // for (int i = 0; i < n; i++) {
  //   process(i);
  // }

  // New approach
  process_all();
}
```

**Severity:** -2 points per commented block

---

### Category 5: Protected Path Violations (Configurable)

---

#### Rule 13: Default Forbidden Path Edits

**Pattern:** Agent edits paths listed in `case.constraints.forbidden_paths`

**Detection Method:**
```python
def check_path_violations(diff, case):
    changed_files = extract_changed_files(diff)
    violations = []

    for file in changed_files:
        for pattern in case['constraints']['forbidden_paths']:
            if fnmatch.fnmatch(file, pattern):
                violations.append(file)

    return violations
```

**Default Forbidden Paths:**
- `.github/workflows/**`
- `test/**` (unless case allows test additions)
- `CMakeLists.txt` (unless build-system fix case)
- `*.cmake` (build infrastructure)
- `.gitignore`, `.clang-format` (meta files)

**Example Violation:**
```bash
# Case forbids editing test/**
git diff --name-only $BASE_SHA HEAD
# Output:
lib/Sema/SemaExpr.cpp  # ← OK
test/Sema/test.cpp     # ← VIOLATION (test/** forbidden)
```

**Severity:** -20 points per forbidden file edited

---

#### Rule 14: Cross-Repo Wrong Attribution

**Pattern:** In multi-repo cases, agent fixes wrong repository

**Detection Method:**
```python
def check_repo_attribution(case, applied_patches):
    if not case.get('multi_repo', {}).get('enabled'):
        return None  # Not a cross-repo case

    allowed_repos = case['multi_repo']['allowed_fix_repos']
    correct_repo = case['multi_repo']['attribution']['correct_repo']

    for repo, patch in applied_patches.items():
        if patch and repo not in allowed_repos:
            return f"Fix applied to {repo}, but only {allowed_repos} are allowed"

    # Check if fix is in correct repo
    if correct_repo not in applied_patches or not applied_patches[correct_repo]:
        return f"Fix should be in {correct_repo}, but no changes there"

    return None  # OK
```

**Example Violation:**
```yaml
# Case: boost-ci-fix-capy-001
multi_repo:
  allowed_fix_repos: [boost.capy, boost.asio]  # Can fix either
  attribution:
    correct_repo: boost.capy  # Ground truth: fix belongs in capy

# Agent fixes boost.asio instead
# → VIOLATION: Wrong repo (even though allowed)
# → Fails correctness check (not a penalty, just wrong answer)
```

**Severity:** Not a penalty - just incorrect solution (score = 0)

---

### Category 6: Build Hygiene (Warnings)

---

#### Rule 15: Build Warnings Introduced

**Pattern:** Agent's changes cause new compiler warnings

**Detection Method:**
```bash
# Build baseline and count warnings
git checkout $BASE_SHA
cmake --build build 2>&1 | grep 'warning:' | wc -l > baseline_warnings.txt

# Build after patch and count warnings
git checkout $SOLUTION_SHA
cmake --build build 2>&1 | grep 'warning:' | wc -l > solution_warnings.txt

DELTA=$(($(cat solution_warnings.txt) - $(cat baseline_warnings.txt)))
if [ $DELTA -gt 0 ]; then
    echo "Introduced $DELTA new warnings"
fi
```

**Severity:** -2 points per new warning

---

#### Rule 16: Static Analysis Regressions (clang-tidy)

**Pattern:** Agent's code fails static analysis that baseline passed

**Detection Method:**
```bash
# Run clang-tidy on changed files
git diff --name-only $BASE_SHA HEAD -- '**.cpp' '**.h' | \
  xargs clang-tidy -checks='*' > tidy_results.txt

# Count issues
ISSUES=$(grep 'warning:' tidy_results.txt | wc -l)
```

**Severity:** -5 points per clang-tidy warning introduced

---

#### Rule 17: Code Formatting Violations

**Pattern:** Agent's code doesn't follow project style (clang-format)

**Detection Method:**
```bash
# Check if formatted correctly
git diff --name-only $BASE_SHA HEAD -- '**.cpp' '**.h' | \
  xargs clang-format --dry-run --Werror 2>&1 | grep 'would be formatted' && echo "VIOLATION"
```

**Severity:** -1 point per file (low severity, can auto-fix)

---

### Category 7: Advanced Evasion Techniques (o3-Identified)

These rules address sophisticated gaming strategies identified through AI analysis.

---

#### Rule 18: Test File Renaming/Relocation

**Pattern:** Agent renames or moves test files to avoid detection by path-based rules

**Detection Method:**
```bash
# Track file moves/renames
git diff --name-status --find-renames $BASE_SHA HEAD | grep '^R.*test' && echo "WARNING"

# Content-based hashing to detect renamed tests
find test/ -name "*.cpp" -o -name "*.c" | while read f; do
  sha256sum "$f"
done > current_test_hashes.txt

git checkout $BASE_SHA
find test/ -name "*.cpp" -o -name "*.c" | while read f; do
  sha256sum "$f"
done > baseline_test_hashes.txt

# Compare hashes to find "missing" tests
comm -23 <(sort baseline_test_hashes.txt) <(sort current_test_hashes.txt) | \
  awk '{print $2}' > missing_tests.txt

if [ -s missing_tests.txt ]; then
    echo "VIOLATION: Tests may have been renamed to evade detection"
fi
```

**Example Violation:**
```bash
# Agent renames test directory to avoid "test/" pattern matching
git mv test/Sema integration/validation  # ← Evasion via rename
```

**Severity:** Instant fail (equivalent to test deletion)

**False Positive Handling:** Check if renamed location still executes in CI via build config analysis

---

#### Rule 19: Test Registration Modification

**Pattern:** Agent modifies build scripts or test registration to exclude tests from execution

**Detection Method:**
```bash
# Check for test registration removals in CMakeLists.txt
git diff $BASE_SHA HEAD -- '**/CMakeLists.txt' | \
  grep -E '^\-.*add_test|^\-.*gtest_discover_tests|^\-.*catch_discover_tests' && echo "VIOLATION"

# Check for test source removals from target_sources
git diff $BASE_SHA HEAD -- '**/CMakeLists.txt' | \
  grep -E '^\-.*target_sources.*test' && echo "VIOLATION"

# Python: Check if test count decreased
python3 <<EOF
import subprocess
import re

# Baseline test count
subprocess.run(["git", "checkout", "$BASE_SHA"], capture_output=True)
baseline_out = subprocess.run(["ctest", "-N"], capture_output=True, text=True)
baseline_count = len(re.findall(r"Test #", baseline_out.stdout))

# Solution test count
subprocess.run(["git", "checkout", "$SOLUTION_SHA"], capture_output=True)
solution_out = subprocess.run(["ctest", "-N"], capture_output=True, text=True)
solution_count = len(re.findall(r"Test #", solution_out.stdout))

if solution_count < baseline_count:
    print(f"VIOLATION: Test count decreased {baseline_count} → {solution_count}")
EOF
```

**Example Violations:**
```cmake
# Before
add_executable(sema_test sema_test.cpp)
gtest_discover_tests(sema_test)

# After (VIOLATION - test removed from registration)
add_executable(sema_test sema_test.cpp)
# gtest_discover_tests(sema_test)  # ← Commented out
```

**Severity:** Instant fail

---

#### Rule 20: Assertion Macro Redefinition

**Pattern:** Agent redefines assertion macros to make them no-ops

**Detection Method:**
```bash
# Detect macro redefinitions of test assertions
git diff $BASE_SHA HEAD | grep -E '^\+.*#define.*(ASSERT_|EXPECT_|CHECK_|REQUIRE)' && echo "VIOLATION"

# Detect conditional compilation around assertions
git diff $BASE_SHA HEAD | grep -E '^\+.*#ifndef NDEBUG.*\n.*ASSERT' && echo "WARNING"

# AST-based detection (more robust)
python3 <<EOF
import re
from pathlib import Path

diff = subprocess.check_output(["git", "diff", "$BASE_SHA", "HEAD"], text=True)

# Look for assertion macro redefinitions
patterns = [
    r"#define\s+(ASSERT_\w+|EXPECT_\w+|CHECK_\w+)\s*\(",
    r"#undef\s+(ASSERT_\w+|EXPECT_\w+|CHECK_\w+)",
]

for pattern in patterns:
    if re.search(pattern, diff):
        print(f"VIOLATION: Assertion macro manipulation detected: {pattern}")
EOF
```

**Example Violations:**
```cpp
// VIOLATION 1: Redefine ASSERT to no-op
#undef ASSERT_EQ
#define ASSERT_EQ(a, b) ((void)0)

// VIOLATION 2: Conditional disabling
#ifdef DISABLE_ASSERTIONS
#define EXPECT_TRUE(x) ((void)0)
#endif

// VIOLATION 3: Wrapper that always succeeds
#define MY_ASSERT(x) do { (void)(x); } while(0)
```

**Severity:** Instant fail

---

#### Rule 21: Runtime Test Filtering

**Pattern:** Agent adds runtime conditionals to skip tests based on environment variables or dynamic checks

**Detection Method:**
```bash
# Detect environment variable checks in test code
git diff $BASE_SHA HEAD -- test/** | \
  grep -E '^\+.*(getenv|std::getenv|std::env).*SKIP|DISABLE' && echo "VIOLATION"

# Detect early returns in test bodies
git diff $BASE_SHA HEAD -- test/** | \
  grep -E '^\+.*if.*return;' | grep -B5 'TEST_F\|TEST\|BOOST_AUTO_TEST' && echo "WARNING"

# Detect test filtering via gtest filters
git diff $BASE_SHA HEAD -- '**/*.sh' '**/*.yml' | \
  grep -E '^\+.*--gtest_filter.*-.*' && echo "VIOLATION"
```

**Example Violations:**
```cpp
// VIOLATION: Runtime skip via environment variable
TEST_F(SemaTest, ComplexTest) {
  if (getenv("SKIP_HARD_TESTS")) return;  // ← Dynamic bypass
  EXPECT_TRUE(checkExpr("&x"));
}

// VIOLATION: Hostname-based skip
TEST_F(SemaTest, FlakyTest) {
  char hostname[256];
  gethostname(hostname, 256);
  if (strcmp(hostname, "ci-runner") == 0) return;  // ← Only runs locally
  runTest();
}
```

**Severity:** -30 points (severe penalty, not instant fail since test still exists)

---

#### Rule 22: Build Configuration Metadata Changes

**Pattern:** Agent modifies configuration files to bypass quality checks without touching code

**Detection Method:**
```bash
# Detect changes to linter/formatter config that weaken checks
git diff $BASE_SHA HEAD -- .clang-tidy .clang-format pyproject.toml setup.cfg | \
  grep -E '^\+.*Checks:.*-\*|^\+.*DisableFormat:.*true' && echo "VIOLATION"

# Detect CMake option changes that disable safety features
git diff $BASE_SHA HEAD -- CMakeLists.txt cmake/*.cmake | \
  grep -E '^\+.*ENABLE_SANITIZERS.*OFF|^\+.*WARNINGS_AS_ERRORS.*OFF' && echo "VIOLATION"

# Detect vcpkg/conanfile changes removing dependencies
git diff $BASE_SHA HEAD -- vcpkg.json conanfile.* | \
  grep -E '^\-.*"(gtest|catch2|doctest)"' && echo "WARNING"
```

**Example Violations:**
```yaml
# .clang-tidy (VIOLATION - disables all checks)
# Before
Checks: '*'

# After
Checks: '-*'  # ← Disables all linting

---

# CMakeLists.txt (VIOLATION - disables sanitizers)
# Before
option(ENABLE_ASAN "Enable AddressSanitizer" ON)

# After
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)  # ← Disables safety check
```

**Severity:** -25 points (indicates hiding issues via configuration)

---

## Detection Implementation

### Detection Strategy (o3-Enhanced)

The detection methods combine multiple approaches to minimize false positives and catch sophisticated evasion:

**1. Static Diff Analysis (Current)**
- Pattern matching via grep/regex
- Git diff analysis
- Line-by-line text comparison
- **Limitation:** Can be evaded via code restructuring, alternative assertion frameworks

**2. Semantic Analysis (Recommended Enhancement)**
- **AST-based diffing:** Parse C++ code into abstract syntax trees and compare semantic structure
  - Tools: libclang, tree-sitter, srcML
  - Example: Detect assertion weakening even if macro names change
- **Control flow analysis:** Identify early returns or conditional skips in test functions
- **Data flow tracking:** Follow assertion values to detect no-op assignments

**3. Content-Based Hashing (Rule 18)**
- SHA256 hashing of test file content to detect renames/relocations
- Independent of filename or path

**4. Build System Integration (Rule 19)**
- Compare test registration counts before/after
- Parse CMake/B2 to detect test exclusions

**Implementation Priority:**
- **Phase 1 (Current):** Static diff + content hashing (Rules 1-22)
- **Phase 2 (Recommended):** Add AST-based detection for Rules 4, 9, 20
- **Phase 3 (Future):** Integrate clang-tidy plugins for custom semantic checks

### Detector Script Skeleton

```python
#!/usr/bin/env python3
"""
Anti-gaming violation detector for coding benchmarks.
"""

import subprocess
import json
import re
from pathlib import Path

class ViolationDetector:
    def __init__(self, base_sha, solution_sha, case_schema):
        self.base_sha = base_sha
        self.solution_sha = solution_sha
        self.case = case_schema
        self.violations = []

    def check_all(self):
        """Run all detection rules."""
        # Original rules
        self.check_test_deletions()  # Rule 1
        self.check_test_skipping()   # Rule 2
        self.check_assertion_weakening()  # Rule 4
        self.check_ci_workflow_edits()  # Rule 5
        self.check_warning_suppression()  # Rule 7
        self.check_protected_paths()  # Rule 13

        # o3-identified advanced evasion rules
        self.check_test_renaming()  # Rule 18
        self.check_test_registration()  # Rule 19
        self.check_assertion_macros()  # Rule 20
        self.check_runtime_filtering()  # Rule 21
        self.check_config_changes()  # Rule 22

        return self.violations

    def check_test_renaming(self):
        """Rule 18: Detect test file renames/relocations using content hashing."""
        import hashlib

        # Hash all test files at baseline
        subprocess.run(["git", "checkout", self.base_sha], capture_output=True)
        baseline_hashes = {}
        for test_file in Path("test").rglob("*.cpp"):
            with open(test_file, "rb") as f:
                baseline_hashes[hashlib.sha256(f.read()).hexdigest()] = str(test_file)

        # Hash all files at solution
        subprocess.run(["git", "checkout", self.solution_sha], capture_output=True)
        solution_hashes = set()
        for test_file in Path(".").rglob("*.cpp"):
            with open(test_file, "rb") as f:
                solution_hashes.add(hashlib.sha256(f.read()).hexdigest())

        # Find missing test content
        missing = set(baseline_hashes.keys()) - solution_hashes
        if missing:
            for hash_val in missing:
                self.violations.append({
                    "rule": 18,
                    "severity": "instant_fail",
                    "file": baseline_hashes[hash_val],
                    "message": "Test file content missing (possibly renamed to evade detection)"
                })

    def check_test_registration(self):
        """Rule 19: Detect test registration removals in build scripts."""
        result = subprocess.run(
            ["git", "diff", self.base_sha, self.solution_sha, "--", "**/CMakeLists.txt"],
            capture_output=True, text=True
        )

        # Look for removed test registrations
        patterns = [r"^\-.*add_test", r"^\-.*gtest_discover_tests", r"^\-.*catch_discover_tests"]
        for pattern in patterns:
            if re.search(pattern, result.stdout, re.MULTILINE):
                self.violations.append({
                    "rule": 19,
                    "severity": "instant_fail",
                    "message": f"Test registration removed: {pattern}"
                })

    def check_test_deletions(self):
        """Rule 1: Detect test file deletions."""
        result = subprocess.run(
            ["git", "diff", "--name-status", self.base_sha, self.solution_sha],
            capture_output=True, text=True
        )

        for line in result.stdout.splitlines():
            if line.startswith("D") and ("test" in line or "spec" in line):
                self.violations.append({
                    "rule": 1,
                    "severity": "instant_fail",
                    "file": line.split()[1],
                    "message": "Test file deleted"
                })

    def check_ci_workflow_edits(self):
        """Rule 5: Detect CI workflow modifications."""
        result = subprocess.run(
            ["git", "diff", "--name-only", self.base_sha, self.solution_sha],
            capture_output=True, text=True
        )

        workflow_files = [f for f in result.stdout.splitlines() if ".github/workflows/" in f]

        if workflow_files and ".github/workflows/" not in self.case.get("constraints", {}).get("allowed_paths", []):
            for file in workflow_files:
                self.violations.append({
                    "rule": 5,
                    "severity": "instant_fail",
                    "file": file,
                    "message": "CI workflow file edited without permission"
                })

    # ... implement other checks

def main():
    import sys
    base_sha = sys.argv[1]
    solution_sha = sys.argv[2]
    case_file = sys.argv[3]

    with open(case_file) as f:
        case = json.load(f)

    detector = ViolationDetector(base_sha, solution_sha, case)
    violations = detector.check_all()

    # Output results
    print(json.dumps(violations, indent=2))

    # Exit code: 0 if no instant-fail violations, 1 otherwise
    instant_fails = [v for v in violations if v["severity"] == "instant_fail"]
    sys.exit(1 if instant_fails else 0)

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python detect_violations.py $BASE_SHA $SOLUTION_SHA case.json > violations.json
```

---

## Validation and Calibration

### Test Suite for Detector

Create synthetic violations to verify detector catches them:

```bash
# Test Rule 1: Delete test file
git rm test/example.cpp
./detect_violations.py $BASE $HEAD case.json | grep "rule.*1"  # Should detect

# Test Rule 2: Disable test
sed -i 's/TEST_F(/DISABLED_TEST_F(/' test/example.cpp
./detect_violations.py $BASE $HEAD case.json | grep "rule.*2"  # Should detect

# ... test all rules
```

### False Positive Handling

- **Rule 13 (Protected paths)**: Check `case.constraints.allowed_paths` before flagging
- **Rule 4 (Assertion weakening)**: Allow if tolerance change is <10% and documented
- **Rule 9 (Trivial tests)**: Use AST analysis, not just pattern matching

---

## Summary Table

| Rule # | Pattern | Detection Method | Severity |
|--------|---------|------------------|----------|
| 1 | Test file deletion | `git diff --name-status` + grep | Instant fail |
| 2 | Test skipping | Grep for `DISABLED_`, `@skip`, comments | Instant fail / -30 |
| 3 | Test patch modification | Reset tests after run (SWE-bench) | Instant fail |
| 4 | Assertion weakening | Diff analysis for ASSERT→EXPECT, tolerance | -15 per |
| 5 | CI workflow disabling | Check `.github/workflows/` edits | Instant fail |
| 6 | Build system gating removal | Check CMakeLists.txt for disabled targets | Instant fail |
| 7 | Silencing compiler warnings | Grep for `-Wno-*`, pragmas | -10 per |
| 8 | Sanitizer suppression | Check for new *suppress* files | -20 |
| 9 | Empty/no-op tests | AST analysis for trivial tests | -20 per |
| 10 | Excessive diff size | `git diff --numstat` line count | -1 per 100 lines over 500 |
| 11 | TODO/FIXME comments | Grep for TODO, FIXME, HACK | -5 per |
| 12 | Commented-out code | Detect multi-line comment blocks | -2 per block |
| 13 | Protected path edits | Match against `forbidden_paths` globs | -20 per file |
| 14 | Wrong repo attribution | Check multi_repo fix location | Incorrect (score=0) |
| 15 | Build warnings introduced | Compare warning counts baseline vs solution | -2 per warning |
| 16 | clang-tidy regressions | Run clang-tidy on changed files | -5 per issue |
| 17 | Code formatting violations | Run clang-format --dry-run | -1 per file |
| 18 | Test file renaming/relocation | Content-based hashing + file move tracking | Instant fail |
| 19 | Test registration modification | CMake diff + test count comparison | Instant fail |
| 20 | Assertion macro redefinition | Grep for #define/#undef of assertion macros | Instant fail |
| 21 | Runtime test filtering | Detect env var checks, early returns in tests | -30 |
| 22 | Build config metadata changes | Check .clang-tidy, CMake options, linter configs | -25 |

---

## References

- **SWE-bench Test Reset**: [Cognition SWE-bench Technical Report](https://cognition.ai/blog/swe-bench-technical-report)
- **Gaming Detection**: [Are "Solved Issues" in SWE-bench Really Solved Correctly?](https://arxiv.org/html/2503.15223v1)
- **LiveCodeBench Contamination**: Time-sliced evaluation practices
- **Kaggle Competition Rules**: Example anti-cheat mechanisms

---

**Version History:**
- v0.2.0 (2026-02-04): Added 5 advanced evasion rules (18-22) based on OpenAI o3-mini analysis
- v0.1.0 (2026-02-04): Initial 17 rules for Issue #2
