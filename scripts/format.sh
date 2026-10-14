#!/bin/bash
# Auto-format the codebase: sort imports, then apply black.
set -e
cd "$(dirname "$0")/.."

echo "Sorting imports with isort..."
uv run isort backend main.py

echo "Formatting with black..."
uv run black backend main.py

echo "Done."
