#!/usr/bin/env bash
# ==============================================================================
# Build OBEPath Sandbox Image (Linux / macOS Shell)
# Target Image Tag: obepath-sandbox:1
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Building obepath-sandbox:1 from ${SCRIPT_DIR}..."

docker build -t obepath-sandbox:1 "${SCRIPT_DIR}"

echo "Successfully built and tagged obepath-sandbox:1"
