#!/usr/bin/env python3
"""
Reproduce the failing or passing CI job for a BugSwarm artifact inside its Docker container.
Runs /usr/local/bin/run_failed.sh or /usr/local/bin/run_passed.sh in the artifact image.

Usage:
  python reproduce_ci.py --artifact-id <image_tag> --job fail
  python reproduce_ci.py --artifact-id <image_tag> --job pass
  python reproduce_ci.py -i Abjad-abjad-289716771 --job fail

Requires the image to be pulled first (e.g. scripts/download_artifact.py).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

DEFAULT_IMAGE_REPO = "bugswarm/cached-images"
# Max time for docker run (CI reproduce can be long; 1 hour)
TIMEOUT_SECONDS = 3600


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce BugSwarm CI job (fail or pass) in container")
    parser.add_argument(
        "--artifact-id",
        "-i",
        type=str,
        required=True,
        help="Artifact image_tag",
    )
    parser.add_argument(
        "--job",
        type=str,
        required=True,
        choices=["fail", "pass"],
        help="Which job to run: fail (run_failed.sh) or pass (run_passed.sh)",
    )
    parser.add_argument(
        "--image-repo",
        type=str,
        default=None,
        help=f"Docker image repository (default: {DEFAULT_IMAGE_REPO})",
    )
    parser.add_argument(
        "--rm",
        action="store_true",
        default=True,
        help="Remove container after run (default: True)",
    )
    parser.add_argument(
        "--no-rm",
        action="store_false",
        dest="rm",
        help="Do not remove container after run",
    )
    args = parser.parse_args()

    artifact_id = args.artifact_id.strip()
    if not artifact_id:
        print("Empty --artifact-id", file=sys.stderr)
        return 1
    repo = (args.image_repo or os.environ.get("BUGSWARM_IMAGE_REPO") or DEFAULT_IMAGE_REPO).strip()
    image = f"{repo}:{artifact_id}"

    script_name = "/usr/local/bin/run_failed.sh" if args.job == "fail" else "/usr/local/bin/run_passed.sh"
    cmd = ["docker", "run"]
    if args.rm:
        cmd.append("--rm")
    cmd.extend([image, "bash", script_name])

    try:
        rc = subprocess.run(cmd, check=False, timeout=TIMEOUT_SECONDS).returncode
        return rc
    except subprocess.TimeoutExpired:
        print(f"Reproduce job timed out after {TIMEOUT_SECONDS}s.", file=sys.stderr)
        return 124
    except FileNotFoundError:
        print("Docker not found. Install Docker and ensure 'docker' is on PATH.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
