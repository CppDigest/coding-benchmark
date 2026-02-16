"# Child Issue 1 – SWE-Bench Multilingual (C/C++ Subset)

Dataset Acquisition + Documentation Guide (Windows)

Purpose
This document defines the exact steps and required outputs to complete Child Issue 1:

"Collect SWE-Bench Multilingual dataset and document methodology in a reproducible way."

Scope
This issue covers:

Deterministic dataset acquisition

Dataset version pinning

Local raw snapshot storage

Dataset structure documentation

Reverse engineering methodology

Replication plan for Boost/Clang

This issue does NOT yet include:

C/C++ filtering logic

Evaluation harness

Agent execution

FAIL→PASS validation

SECTION 1 — Directory Structure

From repository root (coding-benchmark), create:

external/
swe-bench-multilingual/
scripts/
data/
raw/
docs/

Windows PowerShell commands:

mkdir external\swe-bench-multilingual\scripts -Force
mkdir external\swe-bench-multilingual\data\raw -Force
mkdir external\swe-bench-multilingual\docs -Force

SECTION 2 — Environment Setup (Windows)

Requirements:

Python 3.10+

Git

Internet access

Create virtual environment:

cd coding-benchmark
python -m venv .venv
.\.venv\Scripts\Activate.ps1

If blocked by execution policy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Install dependencies:

pip install --upgrade pip
pip install datasets huggingface_hub pyarrow tqdm

SECTION 3 — Dataset Version Pinning (Mandatory)

Navigate to Hugging Face dataset page:
SWE-bench/SWE-bench_Multilingual

Open "Files and versions" or "History"

Copy a specific commit hash.

Create file:
external\swe-bench-multilingual\docs\dataset_version.md

Add:

DATASET_ID = SWE-bench/SWE-bench_Multilingual
DATASET_REVISION = <commit_hash>
DATE_SELECTED = YYYY-MM-DD
DOWNLOADED_BY = <name>

Never use "main" without revision pinning.

SECTION 4 — Dataset Download Script

Create file:
external\swe-bench-multilingual\scripts\download.py

Insert:

import argparse
import json
import os
from datetime import datetime
from datasets import load_dataset

DATASET_ID = "SWE-bench/SWE-bench_Multilingual"

def main():
parser = argparse.ArgumentParser(description="Download SWE-Bench Multilingual deterministically.")
parser.add_argument("--revision", required=True, help="Pinned dataset commit hash")
parser.add_argument("--output-dir", default="external/swe-bench-multilingual/data/raw")
args = parser.parse_args()

os.makedirs(args.output_dir, exist_ok=True)

print(\"Loading dataset...\")
dataset = load_dataset(DATASET_ID, revision=args.revision)

manifest = {
    \"dataset_id\": DATASET_ID,
    \"revision\": args.revision,
    \"downloaded_at_utc\": datetime.utcnow().isoformat() + \"Z\",
    \"splits\": list(dataset.keys())
}

manifest_path = os.path.join(args.output_dir, \"manifest.json\")
with open(manifest_path, \"w\", encoding=\"utf-8\") as f:
    json.dump(manifest, f, indent=2)

for split_name, split_data in dataset.items():
    split_path = os.path.join(args.output_dir, split_name + \".parquet\")
    split_data.to_parquet(split_path)
    print(\"Saved:\", split_name, \"Rows:\", len(split_data))

print(\"Download complete.\")
print(\"Manifest saved at:\", manifest_path)

if name == "main":
main()

SECTION 5 — Execute Download

From repo root:

python external\swe-bench-multilingual\scripts\download.py --revision <commit_hash>

Expected output:

external\swe-bench-multilingual\data\raw\
manifest.json
train.parquet
dev.parquet
test.parquet

Manifest.json contains:

dataset_id

revision

timestamp

splits

SECTION 6 — Dataset Overview Documentation

Create file:
external\swe-bench-multilingual\docs\dataset_overview.md

Include:

Dataset ID

Dataset Revision

Total number of tasks

Available splits

Field descriptions (repo, base_commit, patch, etc.)

How SWE-Bench defines success

How gold patches are provided

Known limitations of C/C++ tasks

This document must describe:

What each record contains

How evaluation works at high level

What assumptions SWE-Bench makes

SECTION 7 — Methodology Documentation

Create file:
external\swe-bench-multilingual\docs\methodology.md

Document the following:

A) How SWE-Bench mines issues

Issue selection criteria

Repository selection logic

Bug-to-commit linkage process

How gold patches are generated

B) Reproducibility Controls

Commit pinning

Environment assumptions

Determinism guarantees (if documented)

C) Replication Plan for Boost/Clang

For Boost:

Mine closed issues labeled bug

Identify fixing commits via git log

Extract parent commit (buggy) and fix commit

Confirm tests exist

Record build/test commands

For Clang:

Mine LLVM bug tracker or GitHub issues

Link issue to fixing commit

Extract regression test additions

Record build/test commands

The replication plan must be detailed enough that another engineer can follow it without coordination.

SECTION 8 — Completion Criteria

Child Issue 1 is complete when:

Dataset can be downloaded via one command.

Dataset revision is pinned.

Raw splits are saved locally.

manifest.json is auto-generated.

dataset_version.md records revision.

dataset_overview.md explains structure.

methodology.md explains mining process.

Replication plan for Boost/Clang is included.

No manual clicking required after setup.

End of Child Issue 1 Guide."