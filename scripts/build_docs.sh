#!/usr/bin/env bash
set -euo pipefail

# Install documentation dependencies (idempotent)
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# Build the static site into ./site
mkdocs build --clean
echo "✅ Documentation built in ./site"