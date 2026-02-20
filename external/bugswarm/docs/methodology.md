# BugSwarm C/C++ CI Subset: Methodology

This document answers the research questions for using BugSwarm as a C/C++ CI benchmark and describes how we replicate and evaluate artifacts.

## Child Issue 3 checklist (questions and guide)

| Requirement | Where answered / implemented |
|-------------|------------------------------|
| Where is BugSwarm hosted? | § Where is BugSwarm hosted? |
| How to list artifacts and filter by language? | § How do we list artifacts and filter by language? |
| Metadata and language filtering? | § How many C/C++…, § Language detection |
| Docker image structure? | § What is the structure of an artifact and its Docker image? |
| How to reproduce failure in container? | § How do we reproduce the failure (and the pass)? |
| Fail vs pass job? | § What is the structure… (job pair), § Fail vs pass job in Summary |
| How many C/C++ artifacts; which CI systems? | § How many C/C++ artifacts are there, and which CI systems? |
| CI build log extraction? | § How do we get the original CI build log? |
| Artifact mining and Docker image creation? | § Artifact mining and Docker image creation |
| Language detection (how C/C++ identified)? | § Language detection |
| Replication plan for Boost/Clang? | § Replication plan for Boost/Clang |
| Full dataset and filter? | `download_dataset.py`: fetch all reproducible → `data/full_artifacts.json`; filter for C/C++ → `data/cpp_artifacts.json` |
| 50+ C/C++ when available? | Tooling supports 50+; current API has 0 C/C++ (Java/Python only) |

## Research questions

### Where is BugSwarm hosted?

- **Web:** https://www.bugswarm.org/
- **REST API:** Same host; programmatic access via the `bugswarm-common` Python package (`DatabaseAPI`). Base URL is configured via the package (e.g. `www.bugswarm.org`).
- **Docker images:** Publicly on Docker Hub at **bugswarm/cached-images**. Each artifact has a tag equal to its `image_tag` (e.g. `Abjad-abjad-289716771`).
- **Code:** GitHub organization [BugSwarm](https://github.com/BugSwarm) (e.g. `bugswarm/bugswarm`, `BugSwarm/client`).

### How do we list artifacts and filter by language?

- **List:** `DatabaseAPI.list_artifacts()` returns artifacts with `reproduce_successes > 0` (no language filter).
- **Filter:** `DatabaseAPI.filter_artifacts(api_filter)` with MongoDB-style JSON. Example: filter by language and reproducibility:
  - `'{"reproduce_successes":{"$gt":0},"lang":{"$in":["C","C++","C/C++"]}}'`
- **Language field:** Each artifact has a `lang` string (e.g. `"Java"`, `"Python"`), set from the project’s Travis config or GitHub language classification. We use it to build the C/C++ subset.
- **Rate limits:** Unauthenticated: 20 requests/minute; with an API token (from [BugSwarm contact](https://www.bugswarm.org/contact/)): no limit. The script `scripts/download_dataset.py` uses `BUGSWARM_API_TOKEN` if set.

### How many C/C++ artifacts are there, and which CI systems?

- The public dataset is **focused on Java and Python**; the dataset site lists only Python and Java. C/C++ may be present in the database if any mined projects used `lang: cpp` or similar in Travis or were classified as C/C++ by GitHub.
- We do not assume a minimum count. We run `download_dataset.py` (with optional `--include-build-system` to add CMake/Makefile artifacts) and record whatever count we get in `data/cpp_artifacts.json`. The methodology and tooling support 50+ artifacts when available.
- **CI systems:** Artifacts have a `ci_service` field: `"travis"` or `"github"` (GitHub Actions). Mining was originally from Travis-CI; newer artifacts may be from GitHub Actions.

### What is the structure of an artifact and its Docker image?

- **Metadata:** Stored in the BugSwarm API; key fields: `image_tag`, `repo`, `lang`, `failed_job`, `passed_job`, `reproduce_successes`, `reproducibility_status`, `ci_service`, `build_system`.
- **Docker image:** One image per artifact; tag = `image_tag`. The image contains:
  - **Failed repo:** `/home/travis/build/failed`
  - **Passed repo:** `/home/travis/build/passed`
  - **Run failed build:** `bash /usr/local/bin/run_failed.sh`
  - **Run passed build:** `bash /usr/local/bin/run_passed.sh`
- **Job pair:** Each artifact is a fail–pass pair: one job that failed (e.g. tests or build) and the next chronological job that passed after a fix.

### How do we reproduce the failure (and the pass) in the container?

- **Pull image:** `docker pull bugswarm/cached-images:<image_tag>`
- **Reproduce failing job:** `docker run --rm bugswarm/cached-images:<image_tag> bash /usr/local/bin/run_failed.sh`
- **Reproduce passing job:** `docker run --rm bugswarm/cached-images:<image_tag> bash /usr/local/bin/run_passed.sh`
- Our harness: `evaluation/reproduce_ci.py --artifact-id <image_tag> --job fail|pass`. Exit code reflects the script’s success/failure.

### How do we get the original CI build log?

- **API:** `DatabaseAPI.get_build_log(job_id)` returns the original build log for a given job (use `failed_job.job_id` or `passed_job.job_id` from artifact metadata).
- **In catalog:** We store `failed_job_id` (and optionally `passed_job_id`) in `data/cpp_artifacts.json`. The field `fail_log_path` can be filled by fetching the log via the API and saving to a file; the download script can be extended to do this.

### Artifact mining and Docker image creation (BugSwarm pipeline)

- BugSwarm **mines** fail–pass build pairs from GitHub projects using Travis-CI (and later GitHub Actions). It identifies builds where the first job fails and the next passes.
- The **Reproducer** turns each pair into a Docker image: it reconstructs the CI environment, checks out the failing and passing commits, and adds scripts (`run_failed.sh`, `run_passed.sh`) so the same steps can be re-run. Images are then cached on Docker Hub.

### Language detection

- **In BugSwarm:** `lang` comes from the mining pipeline (Travis config language and/or GitHub repo language). We treat it as the source of truth for “C/C++” and filter with `lang` in `["C","C++","C/C++"]`.
- **Fallback:** If we need more C/C++-related cases, we can include artifacts with `build_system` in `["CMake","Makefile","make"]` via `download_dataset.py --include-build-system`; these may be C/C++ even when `lang` is missing or different.

### Replication plan for Boost/Clang

- **Goal:** Use BugSwarm-style CI replay as a pattern for our own Boost/Clang benchmarks: checked-out repo, fixed environment, one command to run the failing (or passing) build/tests.
- **Steps:**
  1. **Curate fail–pass pairs** for Boost/Clang (e.g. from CI history or issue trackers).
  2. **Create Docker images** (or equivalent) that contain the repo at the failing and passing commits and a single entrypoint (e.g. “run failing job” / “run passing job”), analogous to BugSwarm’s `run_failed.sh` / `run_passed.sh`.
  3. **Store metadata** in a small catalog (repo, fail_commit, pass_commit, image_tag, job type) similar to `cpp_artifacts.json`.
  4. **Evaluation:** Run the “fail” job in the container; the agent’s patch is applied (or repo updated); then run the “pass” job (or same test command) to verify the fix. Success = same outcome as the known pass.
- **Difference:** Our Boost/Clang suites may use custom images and test commands rather than BugSwarm’s Travis/GHA reproducer; the *contract* (reproducible fail/pass in a container with clear commands) is what we replicate.

## Summary

| Question | Answer |
|----------|--------|
| Where hosted? | bugswarm.org, Docker Hub bugswarm/cached-images, GitHub BugSwarm |
| How to list/filter? | REST API via bugswarm-common; filter_artifacts(MongoDB query); lang and reproduce_successes |
| Metadata / language? | Artifact schema includes lang, build_system, failed_job, passed_job; we filter by lang and optionally build_system |
| Docker structure? | One image per artifact; run_failed.sh / run_passed.sh; repos under /home/travis/build/ |
| Reproduce failure? | docker run image bash /usr/local/bin/run_failed.sh (or reproduce_ci.py --job fail) |
| Fail vs pass job? | fail = first job (failed build/tests); pass = next job that passed after fix |
| C/C++ count? | Dataset is Java/Python-focused; we catalog whatever C/C++ (and optional CMake) artifacts exist |
| CI systems? | travis, github (GitHub Actions) |
| Boost/Clang replication? | Same pattern: curated pairs, Docker (or env) with run_fail/run_pass, catalog, evaluate by re-running after agent fix |
