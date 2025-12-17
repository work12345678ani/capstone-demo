#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing backend requirements..."
cd "$ROOT_DIR/backend"

exec uvicorn main:app --host 0.0.0.0 --port $PORT