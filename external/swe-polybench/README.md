# SWE-PolyBench 500 Subset (Child Issue 4)

**Not a C/C++ dataset.** SWE-PolyBench 500 is a **multi-language** benchmark with **Java, JavaScript, TypeScript, and Python only** (125 issues per language). There are no C/C++ issues in the official 500 subset. We still produce `cpp_subset.jsonl` (filtered by language) so the pipeline is ready if the benchmark adds C/C++ later.

## Layout

- **scripts/download.py** — Download 500 subset from Hugging Face (`AmazonScience/SWE-PolyBench_500`), write `data/polybench_500.jsonl` and `data/cpp_subset.jsonl`.
- **data/polybench_500.jsonl** — Full 500 issues (one JSON per line). Each has: `language`, `repo`, `issue_text`, `test_cmd`, `expected_patch`, plus `instance_id`, `base_commit`, `F2P`, `P2P`, `task_category`, etc.
- **data/cpp_subset.jsonl** — C/C++ filtered subset (same schema). **Always empty** for the current benchmark — the 500 subset does not include C/C++.
- **evaluation/evaluate.py** — Evaluation runner: accuracy/pass-rate. Use `--use-official --polybench-repo /path/to/SWE-PolyBench` to run the official harness.
- **docs/methodology.md** — Research Q&A, issue selection, multi-language coverage, difficulty, test generation, replication plan for Boost/Clang.

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
- **C/C++ identification:** `data/cpp_subset.jsonl` holds C/C++ issues when present; for SWE-PolyBench 500 there are none (not a C/C++ dataset).
- **Evaluation script** returns accuracy/pass-rate (via official harness when `--use-official`).
- **Per issue:** `language`, `repo`, `issue_text`, `test_cmd`, `expected_patch` (and `instance_id`, `base_commit`, F2P, P2P, etc.).

## References

- [Hugging Face: AmazonScience/SWE-PolyBench_500](https://huggingface.co/datasets/AmazonScience/SWE-PolyBench_500)
- [GitHub: amazon-science/SWE-PolyBench](https://github.com/amazon-science/SWE-PolyBench)
- [Leaderboard & docs](https://amazon-science.github.io/SWE-PolyBench/)
