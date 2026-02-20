# Timeline and Effort Estimate (Boost/Clang Benchmark)

This document provides a realistic timeline and effort estimate for creating the internal Boost and Clang benchmark dataset (target: 100–200 high-quality cases each, or a combined first release with 100–200 total with balanced coverage).

---

## Assumptions

- One FTE (or equivalent part-time) working on mining, extraction, validation, and documentation.
- Existing tooling: Git, Python, Docker; Boost and LLVM build experience helpful but not assumed from day one.
- Methodology and plan docs (methodology_analysis, boost_plan, clang_plan, tooling_spec) are done; script templates are in place.

---

## Phases and Milestones

### Phase 1: Tooling and mining (Weeks 1–3)

| Milestone | Deliverable | Effort (rough) |
|-----------|-------------|----------------|
| 1.1 | Scripts implemented from templates: mine GitHub issues (Boost), mine Bugzilla/git (Clang) | 3–5 d |
| 1.2 | Extract bug-fix pairs (buggy/fixed commits) and link to issues | 2–3 d |
| 1.3 | Generate candidate list with test_cmd/build_cmd (Boost) or test_file/build_target (Clang) | 2–3 d |
| 1.4 | Docker images for Boost and Clang build/test | 2–3 d |

**Output:** Candidate list (e.g. 300–500 Boost + 300–500 Clang), runnable scripts, and Dockerfiles.

---

### Phase 2: Validation and filtering (Weeks 4–6)

| Milestone | Deliverable | Effort (rough) |
|-----------|-------------|----------------|
| 2.1 | Validation runner: checkout buggy → run test (expect fail), checkout fixed → run test (expect pass) | 3–5 d |
| 2.2 | Run validation on all candidates; collect pass/fail and flakiness | 2–4 d (mostly compute time) |
| 2.3 | Filter to cases that satisfy “buggy fails, fixed passes” and drop flaky/unclear | 1–2 d |
| 2.4 | Add metadata (difficulty, category, lines_changed) and finalize schema | 1–2 d |

**Output:** Validated dataset (target 100–200 per project or combined), with JSONL and schema documented.

---

### Phase 3: Dataset release and documentation (Weeks 7–8)

| Milestone | Deliverable | Effort (rough) |
|-----------|-------------|----------------|
| 3.1 | Final JSONL + schema, versioned (e.g. v0.1) | 0.5 d |
| 3.2 | README: how to download, run validation, and cite | 0.5 d |
| 3.3 | Methodology update: actual counts, library/component distribution, any exclusions | 1 d |
| 3.4 | Optional: CI job or script to re-run validation on dataset | 1 d |

**Output:** Released dataset, README, and methodology suitable for a new team member to use or extend.

---

## Total effort (order of magnitude)

| Phase | Duration | Effort (person-days) |
|-------|----------|----------------------|
| Phase 1 | 3 weeks | ~10–14 d |
| Phase 2 | 3 weeks | ~7–13 d |
| Phase 3 | 2 weeks | ~3 d |
| **Total** | **~8 weeks** | **~20–30 d** |

If scope is “100–200 cases total” (Boost + Clang combined) instead of per project, Phase 1–2 can be shortened (e.g. 6 weeks total, ~15–20 person-days) by doing one project first and reusing tooling for the other.

---

## Risks and buffers

- **Mining yield:** Fewer than expected issues with tests or clear fix commits → add more libraries (Boost) or components (Clang), or relax filters slightly; buffer +1 week.
- **Build/test instability:** Flaky tests or environment differences → invest in Docker and retry logic; buffer +1 week in Phase 2.
- **Scope creep:** Stick to “100–200 high-quality” and defer “more libraries” or “more categories” to a follow-up.

---

## Acceptance criteria (recap)

- Plans are detailed enough for immediate implementation.
- Each plan has concrete commands and code examples.
- Tooling spec lists all required dependencies.
- Timeline provides realistic estimates with milestones.
- A new team member can start implementing without additional clarification.
