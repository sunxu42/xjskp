#!/usr/bin/env bash
set -euo pipefail

python -m uvicorn src.service.app:app --host 127.0.0.1 --port 18765 --reload
