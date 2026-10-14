#!/bin/bash
# Run all quality checks without modifying files. Exits non-zero on failure.
cd "$(dirname "$0")/.."

status=0

echo "==> isort (import order)"
uv run isort --check-only --diff backend main.py || status=1

echo "==> black (formatting)"
uv run black --check --diff backend main.py || status=1

echo "==> flake8 (lint)"
uv run flake8 backend main.py || status=1

if [ $status -eq 0 ]; then
    echo "All quality checks passed."
else
    echo "Quality checks failed. Run ./scripts/format.sh to fix formatting issues."
fi
exit $status
