#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f "src/service/app.py" ]; then
  echo "src/service/app.py not found. Complete Task 2 before running dev server."
  exit 1
fi

python -m uvicorn src.service.app:app --host 127.0.0.1 --port 18765 --reload
