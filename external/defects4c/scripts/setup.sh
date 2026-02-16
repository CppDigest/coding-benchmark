#!/usr/bin/env bash
# Defects4C setup script (Child Issue 2).
# Clones the official Defects4C repo and prepares the bug catalog.
# Run from repo root or from external/defects4c. Requires: git, curl, python3.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFECTS4C_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$DEFECTS4C_DIR/data"
REPO_DIR="$DEFECTS4C_DIR/repos"
OFFICIAL_REPO="https://github.com/defects4c/defects4c.git"
CLONE_DIR="$DEFECTS4C_DIR/defects4c_upstream"

echo "Defects4C setup: $DEFECTS4C_DIR"

# Clone upstream Defects4C (metadata, Docker, scripts)
if [ ! -d "$CLONE_DIR" ]; then
  echo "Cloning Defects4C upstream..."
  git clone --depth 1 "$OFFICIAL_REPO" "$CLONE_DIR"
else
  echo "Upstream already cloned: $CLONE_DIR"
fi

mkdir -p "$DATA_DIR"
mkdir -p "$REPO_DIR"

# Fetch full dataset from upstream (same pattern as SWE-Bench: download then use)
if command -v python3 &>/dev/null; then
  DOWNLOAD_SCRIPT="$SCRIPT_DIR/download_dataset.py"
  if [ -f "$DOWNLOAD_SCRIPT" ]; then
    echo "Fetching full Defects4C bug list from GitHub..."
    python3 "$DOWNLOAD_SCRIPT" || true
  fi
fi

if [ ! -f "$DATA_DIR/bug_catalog.json" ] || [ ! -s "$DATA_DIR/bug_catalog.json" ]; then
  echo "Warning: bug_catalog.json missing or empty. Run: python scripts/download_dataset.py"
fi

echo "Setup complete. Next: python scripts/checkout_bug.py --bug-id PROJECT@SHA"
echo "Catalog: $DATA_DIR/bug_catalog.json"
