# MultiPL-E C++ Subset and HumanEval (Child Issue 5)

Code-generation benchmark: MultiPL-E C++ (HumanEval translated to C++) and HumanEval Python reference. Used for pass@1, pass@10, pass@100 evaluation.

## Layout

- **scripts/download.py** — Download `nuprl/MultiPL-E` (humaneval-cpp) → `data/cpp_problems.jsonl`; `openai/openai_humaneval` → `data/humaneval_python.jsonl`.
- **data/cpp_problems.jsonl** — 161 C++ problems (task_id, prompt, tests, canonical_solution).
- **data/humaneval_python.jsonl** — 164 Python problems (original HumanEval reference).
- **evaluation/sandbox/** — Docker + execute.py: compile and run C++ with g++, timeout, no network.
- **evaluation/evaluate_passk.py** — Compute pass@1, pass@10, pass@100 from completions using the sandbox.

## Quick start

```bash
cd external/multiple-humaneval
pip install -r scripts/requirements.txt
python scripts/download.py
```

Build the sandbox (for evaluation):

```bash
docker build -t multiple-humaneval-sandbox:latest evaluation/sandbox
```

Run pass@k evaluation (completions JSONL: one line per task with `task_id` and `solution` or `completion`):

```bash
python evaluation/evaluate_passk.py --dataset data/cpp_problems.jsonl --completions completions.jsonl --result-dir ./results
```

## Acceptance criteria (Child Issue 5)

- **164 HumanEval problems in C++ format:** MultiPL-E C++ has **161** problems (downloaded to cpp_problems.jsonl). Python reference has 164.
- **Each problem:** task_id, prompt, tests, canonical_solution (canonical_solution may be empty for C++ on HF).
- **Sandbox:** Safely compiles and runs C++ (Docker, g++, timeout, no network).
- **Evaluation:** Returns pass@1, pass@10, pass@100 (evaluate_passk.py writes evaluate_passk.json).

## References

- [nuprl/MultiPL-E](https://huggingface.co/datasets/nuprl/MultiPL-E) · [GitHub](https://github.com/nuprl/MultiPL-E)
- [openai/openai_humaneval](https://huggingface.co/datasets/openai/openai_humaneval)
- [MultiPL-E tutorial](https://nuprl.github.io/MultiPL-E/)
