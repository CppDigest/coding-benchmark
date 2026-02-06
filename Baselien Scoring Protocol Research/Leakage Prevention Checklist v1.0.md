# Leakage Prevention Checklist v1.0

A standalone checklist for preventing data contamination during benchmark dataset curation and baseline evaluation. This document extracts the leakage controls from the Baseline Scoring Protocol for practical use during case selection and validation.

---

## Quick Reference

Use this checklist at three stages:
1. **Case Selection** - When adding new cases to the dataset
2. **Pre-Evaluation** - Before running baselines on a dataset batch
3. **Post-Evaluation** - When validating and publishing results

---

## Stage 1: Case Selection Checklist

### Temporal Isolation

| # | Check | Status |
|---|-------|--------|
| 1.1 | Task source (issue/PR/CI failure) has a verifiable creation date | ☐ |
| 1.2 | Creation date is documented in case metadata (`task_creation_date`) | ☐ |
| 1.3 | Gold fix date is documented (`task_gold_date`) | ☐ |
| 1.4 | Task creation date is after January 1, 2023 (or defined cutoff) | ☐ |

### Solution-in-Thread Detection

| # | Check | Status |
|---|-------|--------|
| 2.1 | Issue thread scanned for code blocks containing fix patterns | ☐ |
| 2.2 | Issue thread scanned for phrases: "here's the fix", "try this", "solution:", "workaround:" | ☐ |
| 2.3 | PR comments reviewed for explicit solution hints | ☐ |
| 2.4 | If solution content found: case excluded OR issue text rewritten to remove hints | ☐ |

### Solution Uniqueness

| # | Check | Status |
|---|-------|--------|
| 3.1 | Task has a single canonical correct solution (not multiple equally-valid approaches) | ☐ |
| 3.2 | Success criteria are unambiguous and machine-checkable | ☐ |
| 3.3 | Gold patch verified to pass all evaluation steps | ☐ |

### Source Verification

| # | Check | Status |
|---|-------|--------|
| 4.1 | Task origin documented (`created_from` field) | ☐ |
| 4.2 | Source is not known to be heavily represented in common training corpora | ☐ |
| 4.3 | If synthetic: documented as synthetic with creation methodology | ☐ |

---

## Stage 2: Pre-Evaluation Checklist

### Model Training Cutoff Verification

| # | Check | Status |
|---|-------|--------|
| 5.1 | Model training cutoff date obtained from official documentation | ☐ |
| 5.2 | Cutoff date recorded in evaluation metadata (`model_training_cutoff`) | ☐ |
| 5.3 | All tasks in batch have creation dates AFTER model cutoff | ☐ |
| 5.4 | Tasks with creation dates before cutoff flagged as `contamination_risk: FLAGGED` | ☐ |

### Gold Patch Isolation

| # | Check | Status |
|---|-------|--------|
| 6.1 | Gold patches stored in separate directory from evaluation environment | ☐ |
| 6.2 | Agent container has NO access to gold patch directory | ☐ |
| 6.3 | Verification container runs separately from agent container | ☐ |
| 6.4 | Prompt templates verified to not include gold patch content | ☐ |

### Retrieval Corpus Validation (RE baseline only)

| # | Check | Status |
|---|-------|--------|
| 7.1 | Retrieval corpus snapshot date documented | ☐ |
| 7.2 | Corpus snapshot predates ALL gold outcomes in the batch | ☐ |
| 7.3 | Corpus SHA256 hash recorded (`retrieval_digest`) | ☐ |

### Infrastructure Integrity

| # | Check | Status |
|---|-------|--------|
| 8.1 | Container image hash recorded (`container_digest`) | ☐ |
| 8.2 | Outbound network disabled (verified with network test) | ☐ |
| 8.3 | Harness commit hash recorded | ☐ |

---

## Stage 3: Post-Evaluation Checklist

### Output Verification

| # | Check | Status |
|---|-------|--------|
| 9.1 | Agent patches compared against gold patches for token overlap | ☐ |
| 9.2 | Patches with ≥80% token overlap flagged for manual review | ☐ |
| 9.3 | Flagged patches manually inspected for memorization indicators | ☐ |

### Decontamination Checks

| # | Check | Status |
|---|-------|--------|
| 10.1 | N-gram analysis performed (if training corpus available) | ☐ |
| 10.2 | Semantic similarity analysis performed on suspicious cases | ☐ |
| 10.3 | 2% random sample manually inspected | ☐ |

### Reporting Compliance

| # | Check | Status |
|---|-------|--------|
| 11.1 | Results segmented by contamination risk (SAFE vs FLAGGED) | ☐ |
| 11.2 | Primary metrics use only SAFE tasks | ☐ |
| 11.3 | Excluded tasks documented with exclusion rationale | ☐ |
| 11.4 | All environment hashes included in scorecard | ☐ |

---

## Case Exclusion Criteria

Exclude a case if ANY of the following apply:

| Criterion | Action | Severity |
|-----------|--------|----------|
| Solution code appears in issue thread | Exclude or rewrite | CRITICAL |
| Gold patch visible in PR comments | Exclude | CRITICAL |
| Task creation date precedes model training cutoff | Flag or exclude for that model | HIGH |
| N-gram overlap >90% with known training corpus | Manual review; exclude if confirmed | HIGH |
| Multiple equally-valid solutions exist | Exclude or define canonical | MEDIUM |
| Test suite is flaky/non-deterministic | Quarantine; exclude from metrics | MEDIUM |
| Source is known training data (popular project, pre-cutoff) | Flag for review | LOW |

---

## Detection Patterns

### Solution-in-Thread Keywords

Scan issue/PR text for these patterns (case-insensitive):

```regex
here's the fix
here is the fix
try this:
solution:
workaround:
fixed by
the fix is
patch:
this patch
```

### Code Block Detection

Flag issues containing code blocks that appear to be complete fixes:

```regex
```(cpp|c|cmake|diff)
.*\n(.*\n)+
```
```

### Policy Violation Patterns

Detect patches that may be "gaming" the benchmark:

```regex
# Test skipping
GTEST_SKIP|DISABLED_|\.skip\(|xfail|XFAIL

# Assertion weakening
ASSERT_.*→EXPECT_|tolerance.*=.*[0-9]+\.[0-9]+

# Warning suppression
#pragma warning\s*\(\s*disable|#pragma GCC diagnostic ignored|-Wno-

# CI config changes
\.github/workflows/.*\.yml|\.github/workflows/.*\.yaml
```

---

## Time-Slicing Reference

### Model Training Cutoffs (Approximate)

| Model | Documented Cutoff | Source |
|-------|------------------|--------|
| Claude Opus 4.5 | ~April 2025 | Anthropic model card |
| Claude Sonnet 4.5 | ~April 2025 | Anthropic model card |
| GPT-5.2 | ~January 2025 | OpenAI documentation |
| GPT-4o | ~October 2023 | OpenAI documentation |
| Gemini 3 Flash | ~November 2025 | Google model card |
| DeepSeek V3.2 | ~Mid 2025 | DeepSeek documentation |
| Qwen3-Coder | ~Mid 2025 | Alibaba documentation |

**Note**: Always verify current cutoffs with provider documentation. Cutoffs may be updated.

### Contamination Risk Classification

```yaml
# For each task × model pair:
if task_creation_date > model_training_cutoff:
  contamination_risk: SAFE
elif task_creation_date <= model_training_cutoff:
  contamination_risk: FLAGGED
  # Options:
  # 1. Exclude from evaluation for this model
  # 2. Include but report separately
  # 3. Manual review for actual leakage indicators
```

---

## Verification Scripts

### Token Overlap Check

```python
def check_token_overlap(agent_patch: str, gold_patch: str, threshold: float = 0.8) -> bool:
    """Flag if agent output has high overlap with gold patch."""
    from difflib import SequenceMatcher
    
    ratio = SequenceMatcher(None, agent_patch, gold_patch).ratio()
    
    if ratio >= threshold:
        return True  # Flag for review
    return False
```

### Solution-in-Thread Scanner

```python
import re

SOLUTION_PATTERNS = [
    r"here'?s?\s+the\s+fix",
    r"solution\s*:",
    r"try\s+this\s*:",
    r"workaround\s*:",
    r"fixed\s+by",
    r"the\s+fix\s+is",
    r"patch\s*:",
]

def scan_for_solutions(text: str) -> list[str]:
    """Return list of matched solution-hint patterns."""
    matches = []
    for pattern in SOLUTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(pattern)
    return matches
```

### Date Validation

```python
from datetime import date

def validate_temporal_isolation(
    task_creation_date: date,
    model_cutoff_date: date,
    dataset_cutoff: date = date(2023, 1, 1)
) -> dict:
    """Validate task dates against cutoffs."""
    return {
        "passes_dataset_cutoff": task_creation_date > dataset_cutoff,
        "passes_model_cutoff": task_creation_date > model_cutoff_date,
        "contamination_risk": "SAFE" if task_creation_date > model_cutoff_date else "FLAGGED"
    }
```

---

## Audit Log Template

Maintain an audit log for each dataset version:

```yaml
# leakage_audit_log.yaml
dataset_version: v0.1
audit_date: 2026-02-05
auditor: [name]

temporal_checks:
  tasks_reviewed: 60
  tasks_passed: 57
  tasks_flagged: 3
  flagged_task_ids: [boost-ci-023, clang-feat-005, clang-issue-008]

solution_in_thread_checks:
  tasks_scanned: 60
  tasks_clean: 58
  tasks_rewritten: 2
  rewritten_task_ids: [clang-issue-003, boost-ci-015]

gold_patch_isolation:
  isolation_verified: true
  verification_method: "Container filesystem audit + prompt template review"

random_sample_review:
  sample_size: 2  # 2% of 60
  sample_task_ids: [clang-issue-007, boost-ci-012]
  issues_found: 0

exclusions:
  total_excluded: 3
  exclusion_reasons:
    - task_id: boost-ci-023
      reason: "Solution code in issue thread"
    - task_id: clang-feat-005
      reason: "Multiple valid solutions"
    - task_id: clang-issue-008
      reason: "Predates all model cutoffs"
```

---

## Summary Checklist (One-Page Reference)

### Before Adding a Case
- [ ] Creation date verified and documented
- [ ] Issue/PR thread scanned for solution hints
- [ ] Gold patch verified to work
- [ ] Single canonical solution exists

### Before Running Baselines
- [ ] Model cutoff dates documented
- [ ] Tasks flagged if before cutoff
- [ ] Gold patches isolated from agent
- [ ] Network disabled
- [ ] Environment hashes recorded

### After Evaluation
- [ ] Output overlap checked against gold
- [ ] High-overlap cases manually reviewed
- [ ] Random sample inspected
- [ ] Results split by contamination risk
- [ ] All exclusions documented

---

*This checklist is designed to be printed and used alongside dataset curation and evaluation workflows. For detailed rationale, see the full Baseline Scoring Protocol.*
