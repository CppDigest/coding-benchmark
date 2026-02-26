# SWE-Bench Multilingual — Dataset Acquisition

Deterministic download and documentation for the [SWE-bench Multilingual](https://huggingface.co/datasets/SWE-bench/SWE-bench_Multilingual) dataset (Child Issue 1).

## Quick start

From the **repository root** (`coding-benchmark`). For full setup (venv, Linux/macOS, troubleshooting), see [docs/methodology.md](docs/methodology.md#installation-and-environment-setup).

```powershell
# 1. Create venv and install deps (one-time)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r external/swe-bench-multilingual/requirements.txt

# 2. Download dataset (revision pinned in docs/dataset_version.md)
python external/swe-bench-multilingual/scripts/download.py --revision 2b7aced941b4873e9cad3e76abbae93f481d1beb

# 3. (Optional) Filter to C/C++ and run evaluation
python external/swe-bench-multilingual/scripts/filter_cpp.py
python external/swe-bench-multilingual/evaluation/run_evaluation.py --predictions_path <path> --output_dir <dir>
```

Output: `external/swe-bench-multilingual/data/raw/manifest.json` and parquet split(s); C/C++ subset in `external/swe-bench-multilingual/data/cpp_issues.jsonl` after step 3.

## Layout

| Path | Purpose |
|------|--------|
| `scripts/download.py` | Download script; requires `--revision` (commit hash from Hugging Face). |
| `scripts/filter_cpp.py` | Filter raw data to C/C++ issues → `data/cpp_issues.jsonl`. |
| `data/raw/` | Raw parquet splits and `manifest.json`. |
| `data/cpp_issues.jsonl` | C/C++ subset for agents and evaluation. |
| `docs/schema.md` | Dataset schema (raw + C/C++ JSONL fields). |
| `docs/methodology.md` | Installation, reproducibility, version pinning, Boost/Clang replication plan. |
| `evaluation/run_evaluation.py` | Evaluation harness adapter (predictions → pass/fail metrics). |

## Pinning a different revision

See **Dataset version pinning** in [docs/dataset_version.md](docs/dataset_version.md). Then run:
```powershell
python external/swe-bench-multilingual/scripts/download.py --revision <commit_hash>
```
