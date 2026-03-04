# Dataset version (pinned)

This document records the pinned revision of the SWE-Bench Multilingual dataset used in this repo. Never use `main` without revision pinning.

## Versioning metadata

| Field | Value |
|-------|--------|
| **DATASET_ID** | `SWE-bench/SWE-bench_Multilingual` |
| **DATASET_REVISION** | `2b7aced941b4873e9cad3e76abbae93f481d1beb` |
| **DATE_SELECTED** | 2026-02-16 |
| **DOWNLOADED_BY** | (set when running download) |

- **Git/commit:** The revision is a Hugging Face dataset commit hash (git commit on the dataset repo), not a branch name.
- **Tag:** No tag is used; the commit hash is the single source of truth.

## How to confirm the pinned revision

1. **From this repo (after download):**  
   Open `external/swe-bench-multilingual/data/raw/manifest.json` and check that the `revision` field equals the `DATASET_REVISION` above.

2. **On Hugging Face:**  
   Go to [SWE-bench/SWE-bench_Multilingual](https://huggingface.co/datasets/SWE-bench/SWE-bench_Multilingual), open "Files and versions" (or "Commit history"), and confirm that commit `2b7aced941b4873e9cad3e76abbae93f481d1beb` exists and matches the snapshot you intend to use.

3. **When re-downloading:**  
   Run the download script with this exact revision:
   ```bash
   python external/swe-bench-multilingual/scripts/download.py --revision 2b7aced941b4873e9cad3e76abbae93f481d1beb
   ```
   The generated `manifest.json` will again list this revision, confirming the pinned snapshot.
