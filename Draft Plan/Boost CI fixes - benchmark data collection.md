### Boost CI fixes — benchmark data collection spec (v0.1)

This document defines what must be captured to build **replayable benchmark cases** for **Boost / cppalliance CI failure fixing**, using the general framework in `2026-02/2026-02-04/AI benchmarking.md`.

It is grounded in the repo’s documented experience:
- iterative CI-fix loops exist (agent reads failing runs and pushes commits until green)
- Boost/build-system issues (e.g., `b2`) are domain-specific and often need strong context
- cross-repo dependency ambiguity is real (a failure in repo A may require a fix in repo B)
- runner availability/latency is a major throughput constraint and should be recorded as a secondary metric

---

### End-to-end process (Boost CI-fix specific)
- **Select CI-fix outcomes**: turn red builds green without “disabling the checker.”
- **Harvest replayable CI failures**: failing GitHub Actions runs that were later fixed (PR merged or known-good commit).
- **Package each case** with a pinned base commit and deterministic reproduction/evaluation steps.
- **Verify case**: baseline run fails at `base_sha`; gold patch makes the defined workflow/job subset pass.
- **Run baselines** (today’s agents/LLMs) under a standardized harness and compare to your product.
- **Publish dataset version + baseline scorecard** for regression tracking.

---

### Scope and goals
- **Primary goal**: benchmark AI’s ability to **diagnose and fix CI failures** in Boost-adjacent repos while respecting project policies.
- **Secondary goal**: benchmark the system’s ability to correctly decide **where the fix belongs** (current repo vs dependency vs shared workspace).
- **Non-goals**: “fixing” by skipping jobs, relaxing checks, or changing CI to not run; unless the case is explicitly “repair CI config”.

---

### Benchmark suites for Boost CI fixes

- **Single-repo CI-fix suite**
  - **Input**: failing GH Actions run logs + repo SHA + job name(s).
  - **Success**: the specified workflow/jobs are green after applying the patch; no policy violations.

- **Cross-repo CI-fix suite (dependency attribution)**
  - **Input**: failing run logs in repo A + dependency graph hint (e.g., boost-workspace manifest or CI checkout list).
  - **Success**: the fix is applied to the correct repo (A or dependency B) and the end-to-end workflow is green.
  - **Why it matters**: documented cases where an agent claims “can’t fix in repo A, should fix in repo B” require multi-repo verification to avoid false confidence.

- **Build-system & configuration suite (b2/CMake/packaging)**
  - **Input**: failure logs + minimal context for build tooling.
  - **Success**: builds/tests pass across the defined matrix; change is minimal and policy-compliant.

- **(Optional) CI acceleration / throughput suite**
  - **Input**: workflow definition + observed queueing/startup overhead.
  - **Success**: measurable reduction in time-to-start or time-to-green without reducing coverage or skipping checks.
  - **Note**: this is more “infra improvement” than “agent fixes,” so treat as optional and score separately.

---

### Data sources (what we harvest)
- **GitHub Actions artifacts**
  - run IDs, job names, failing step logs (full log as artifact; excerpt in prompt)
  - environment metadata (OS, compiler versions, toolchain install steps)
  - timestamps (queued, started, finished) so we can compute latency metrics

- **Fix provenance**
  - PRs/commits that actually fixed the failure (`gold_merge_sha`)
  - discussion/context if needed (issue/PR comments that clarify intent)

- **Workspace / dependency context**
  - if using `boost-workspace` or similar “umbrella builds,” capture the exact set of checked-out repos and revisions
  - dependency mapping from repo manifests/CI scripts (so cross-repo cases are reproducible)

---

### Case definition (required fields for Boost CI cases)
Follow the general schema in `AI benchmarking.md`; minimum required fields below ensure replayability and unambiguous scoring.

- **Identity and provenance**
  - `case_id`, `suite`, `title`, `labels` (e.g., `windows`, `msvc`, `clang`, `gcc`, `cmake`, `b2`, `packaging`), `difficulty`
  - `repo_url`, `base_sha`, `created_from` (run ID, PR IDs), `dataset_version`

- **Task input**
  - `prompt_markdown`: failing log excerpt + summary of failure mode + job context
  - `context_hints`: where to look (files, workflow YAML, CMakeLists, b2 configs)

- **Reproducibility**
  - `environment`: runner OS + compiler toolchain + dependency install steps
  - `setup_steps`: checkout rules, caches, and any workspace setup
  - `repro_steps`: commands that reproduce locally if possible (optional but preferred)
  - `evaluation_steps`: the exact workflows/jobs/commands that define success

- **Multi-repo fields (required for cross-repo suite)**
  - `workspace_repos`: list of repos + SHAs used by the workflow
  - `primary_repo`: where the failure was observed
  - `allowed_fix_repos`: which repos may be modified for this case

- **Constraints / policies**
  - `forbidden_paths` (default): disabling workflows, skipping tests, broad “turn off warnings” changes
  - `allowed_paths`: explicit per-case exceptions (e.g., if the task is “fix CI config”)
  - `time_budget_minutes`

- **Gold outcome**
  - `gold_merge_sha` or `gold_patch` pointer
  - `gold_validation`: evidence the gold outcome makes the defined jobs green

- **Scoring hooks**
  - `success_criteria`: explicit green jobs/workflows; and any required tests
  - `penalties`: protected path edits, test skipping, CI disabling, “fix is in wrong repo”

---

### Success criteria (Boost CI-fix guidance)
- **Primary success**: specified GH Actions jobs are green (or local equivalent commands pass).
- **Regression safety**: if the workflow defines additional tests, keep PASS→PASS for the defined job set.
- **Correct repo attribution** (cross-repo suite): a fix only “counts” if it lands in the repo allowed by the case and the end-to-end workflow is green.

---

### Anti-gaming / guardrails (Boost CI)
- **Default protected paths**:
  - workflow files (`.github/workflows/*`)
  - scripts that gate tests/builds
  - changes that reduce test coverage or bypass failing steps
- **Allowed exception mechanism**:
  - if the case is explicitly “repair CI config” or “fix workflow,” the case must whitelist those files and define success accordingly.

---

### Metrics to record (beyond pass/fail)
These are secondary but directly reflect the documented pain points.

- **Attempts/iterations**: commits or patch attempts until green.
- **Time-to-start**: queued → started.
- **Time-to-green**: started → success.
- **Runner cost proxies**: total minutes consumed (if available from Actions).
- **Violation counts**: protected-path edits, test-skipping patterns.

---

### Baseline scoring plan (Boost CI dataset)
Once dataset slice exists:
- Run **Pass@1** baselines and, if practical, a small **Pass@k** for CI-fix (because CI iteration is inherently multi-step).
- Include:
  - a minimal “log-to-patch” baseline (no repo-wide retrieval)
  - a tool-using baseline (edits + rerun loop)
  - MCP on/off variants for build-system context retrieval
- Produce `baseline_scorecard.md` with resolved rate by suite + top failure modes (wrong repo attribution, b2 misunderstandings, Windows-only failures, policy violations).

---

### Deliverable definition (dataset v0.1 for Boost CI fixes)
Start with a narrow, high-signal dataset slice:
- **N=30** total cases, for example:
  - 20 single-repo CI-fix
  - 7 cross-repo attribution cases
  - 3 build-system focused cases (b2/CMake)

Every case must include:
- pinned `base_sha`
- run/job identification + logs
- deterministic evaluation steps
- explicit allowed/forbidden paths and allowed fix repos (when cross-repo)
- verified gold outcome

---

### Open questions to track (do not block v0.1)
- **Standard “workspace” representation**: how to encode `boost-workspace` (or similar) checkout graphs in the case schema.
- **Local reproduction**: which subset of CI failures can be reproduced deterministically outside GH Actions.
- **Infra vs agent benchmarks**: keep runner-speed improvements and agent coding fixes as separate suites so scores remain interpretable.

