#!/usr/bin/env python3
"""
Pull the BugSwarm Docker image for an artifact by image_tag (artifact-id).
Image is pulled from bugswarm/cached-images:<image_tag>.

Usage:
  python download_artifact.py --artifact-id <image_tag>
  python download_artifact.py -i Abjad-abjad-289716771

Requires Docker. Optional: BUGSWARM_IMAGE_REPO to override (default bugswarm/cached-images).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

DEFAULT_IMAGE_REPO = "bugswarm/cached-images"


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull BugSwarm Docker image for an artifact")
    parser.add_argument(
        "--artifact-id",
        "-i",
        type=str,
        required=True,
        help="Artifact image_tag (e.g. Abjad-abjad-289716771)",
    )
    parser.add_argument(
        "--image-repo",
        type=str,
        default=None,
        help=f"Docker image repository (default: {DEFAULT_IMAGE_REPO})",
    )
    args = parser.parse_args()

    artifact_id = args.artifact_id.strip()
    if not artifact_id:
        print("Empty --artifact-id", file=sys.stderr)
        return 1
    repo = (args.image_repo or os.environ.get("BUGSWARM_IMAGE_REPO") or DEFAULT_IMAGE_REPO).strip()
    image = f"{repo}:{artifact_id}"

    try:
        subprocess.run(
            ["docker", "pull", image],
            check=True,
        )
    except FileNotFoundError:
        print("Docker not found. Install Docker and ensure 'docker' is on PATH.", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        print(f"docker pull failed: {e}", file=sys.stderr)
        return 1
    print(f"Pulled {image}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
