# Dataset schema

This document describes the schema of the SWE-Bench Multilingual data used in this project: the **raw parquet** fields and the **C/C++ JSONL** (`data/cpp_issues.jsonl`) consumed by agents and the evaluation harness. For dataset version pinning (revision) and download steps, see [methodology.md](methodology.md).

---

## Raw dataset (Parquet)

Source: `data/raw/*.parquet` (produced by `scripts/download.py` from Hugging Face).

| Field | Type | Description |
|-------|------|--------------|
| `repo` | string | Repository identifier `owner/name` (e.g. `redis/redis`). |
| `instance_id` | string | Unique instance id: `owner__repo-pr_number` (official format). |
| `base_commit` | string | Git commit hash of the repo in the pre-solution (buggy) state. |
| `patch` | string | Gold patch (unified diff) that fixes the issue. |
| `test_patch` | string | Optional patch or metadata related to tests. |
| `problem_statement` | string | Natural language description of the issue. |
| `hints_text` | string | Optional hints or extra context (may be empty). |
| `created_at` | string | Issue creation timestamp. |
| `version` | string | Issue or version identifier. |
| `FAIL_TO_PASS` | list[str] | Test identifiers that must change from fail → pass. |
| `PASS_TO_PASS` | list[str] | Test identifiers that must remain passing. |

---

## C/C++ subset (JSONL)

File: `data/cpp_issues.jsonl`. One JSON object per line. Produced by `scripts/filter_cpp.py` from the raw parquet (issues whose gold patch touches at least one `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`, `.hxx` file).

| Field | Type | Description |
|-------|------|--------------|
| `instance_id` | string | Same as raw: `owner__repo-pr_number` (official format). |
| `repo_url` | string | Full GitHub URL: `https://github.com/{owner}/{name}`. |
| `repo` | string | Repository `owner/name`. |
| `commit_base` | string | Same as raw `base_commit`: repo state to patch. |
| `issue_text` | string | Concatenation of `problem_statement` and `hints_text` (issue description for the agent). |
| `gold_patch` | string | Gold patch (unified diff) for evaluation. |
| `test_command` | string | Human-readable instruction; actual tests are in `fail_to_pass` / `pass_to_pass`. |
| `fail_to_pass` | list[str] | Test IDs that must go from fail to pass. |
| `pass_to_pass` | list[str] | Test IDs that must stay passing. |

Every C/C++ issue in the benchmark has at least: `repo_url`, `commit_base`, `issue_text`, `gold_patch`, `test_command` (acceptance criterion).

---

## Evaluation input (agent output)

The evaluation harness expects a **predictions** file (e.g. JSONL) where each line has at least:

| Field | Type | Description |
|-------|------|--------------|
| `instance_id` | string | Must match an `instance_id` in `cpp_issues.jsonl`. |
| `model_patch` | string | The patch produced by the agent (unified diff). |

Optional: `model_name_or_path` for logging. See `evaluation/run_evaluation.py` and SWE-bench prediction format.
