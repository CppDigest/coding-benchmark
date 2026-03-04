"""
Download SWE-Bench Multilingual dataset deterministically.
Requires: pip install datasets huggingface_hub pyarrow
"""
import argparse
import json
import os
import re
from datetime import datetime, timezone

from datasets import load_dataset

DATASET_ID = "SWE-bench/SWE-bench_Multilingual"


def _commit_hash(value: str) -> str:
    """Argparse type validator for Git commit hashes."""
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", value):
        raise argparse.ArgumentTypeError(
            f"Invalid --revision {value!r}: expected a Git commit hash (7-40 hex characters)"
        )
    return value


def main():
    parser = argparse.ArgumentParser(
        description="Download SWE-Bench Multilingual deterministically."
    )
    parser.add_argument(
        "--revision",
        required=True,
        type=_commit_hash,
        help="Pinned dataset commit hash (from Hugging Face Files and versions)",
    )
    parser.add_argument(
        "--output-dir",
        default="external/swe-bench-multilingual/data/raw",
        help="Directory to write parquet files and manifest.json",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("Loading dataset...")
    dataset = load_dataset(DATASET_ID, revision=args.revision)

    manifest = {
        "dataset_id": DATASET_ID,
        "revision": args.revision,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "splits": list(dataset.keys()),
    }

    for split_name, split_data in dataset.items():
        split_path = os.path.join(args.output_dir, split_name + ".parquet")
        split_data.to_parquet(split_path)
        print("Saved:", split_name, "Rows:", len(split_data))

    manifest_path = os.path.join(args.output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("Download complete.")
    print("Manifest saved at:", manifest_path)


if __name__ == "__main__":
    main()
