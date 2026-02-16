#!/usr/bin/env bash
# Install deps and download dataset (same pattern as Child 1/2: Python + download script).
# Run from external/bugswarm: ./scripts/setup_client.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
pip install -q -r scripts/requirements.txt
python scripts/download_dataset.py --include-build-system
