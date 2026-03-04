# SWE-PolyBench 500 Subset (Child Issue 4)

## Important: This is not a C/C++ dataset

**SWE-PolyBench 500 contains only Java, JavaScript, TypeScript, and Python** (125 issues per language). There are no C/C++ issues. We do **not** produce a C/C++ subset file—use SWE-Bench Multilingual (Issue 1), Defects4C (Issue 2), BugSwarm (Issue 3), or the Boost/Clang plan (Issue 6) for C/C++.

## Layout

- **scripts/download.py** — Download 500 subset from Hugging Face (`AmazonScience/SWE-PolyBench_500`), write `data/polybench_500.jsonl`.
- **data/polybench_500.jsonl** — Full 500 issues (one JSON per line). Each has: `language`, `repo`, `issue_text`, `test_cmd`, `expected_patch`, plus `instance_id`, `base_commit`, `F2P`, `P2P`, `task_category`, etc.
- **evaluation/evaluate.py** — Evaluation runner: accuracy/pass-rate. Use `--use-official --polybench-repo /path/to/SWE-PolyBench` to run the official harness.
- **docs/methodology.md** — Research Q&A, issue selection, language coverage, difficulty, test generation, replication plan for Boost/Clang.

## Quick start

```bash
cd external/swe-polybench
pip install -r scripts/requirements.txt
python scripts/download.py
```

Then run evaluation (lightweight: just validates predictions; for full pass-rate use official repo):

```bash
python evaluation/evaluate.py --dataset-path data/polybench_500.jsonl --predictions-path predictions.jsonl --result-path ./eval_results
# Full evaluation (requires clone of amazon-science/SWE-PolyBench):
python evaluation/evaluate.py --dataset-path data/polybench_500.jsonl --predictions-path predictions.jsonl --result-path ./eval_results --use-official --polybench-repo /path/to/SWE-PolyBench
```

## Acceptance criteria (Child Issue 4)

- **500-issue dataset** downloadable via `python scripts/download.py`.
- **C/C++:** The 500 subset has **no C/C++**; no C/C++ subset file is produced (deliverable N/A). Use other benchmarks in this repo for C/C++.
- **Evaluation script** returns accuracy/pass-rate (via official harness when `--use-official`).
- **Per issue:** `language`, `repo`, `issue_text`, `test_cmd`, `expected_patch` (and `instance_id`, `base_commit`, F2P, P2P, etc.).

## References

- [Hugging Face: AmazonScience/SWE-PolyBench_500](https://huggingface.co/datasets/AmazonScience/SWE-PolyBench_500)
- [GitHub: amazon-science/SWE-PolyBench](https://github.com/amazon-science/SWE-PolyBench)
- [Leaderboard & docs](https://amazon-science.github.io/SWE-PolyBench/)
