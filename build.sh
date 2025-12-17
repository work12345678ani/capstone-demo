#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing backend requirements..."
cd "$ROOT_DIR/backend"


if [[ -f requirements.txt ]]; then
  python3 -m pip install --upgrade pip
  python3 -m pip install -r requirements.txt
else
  echo "ERROR: backend/requirements.txt not found."
  exit 1
fi

echo "==> Running Alembic migrations..."
alembic upgrade head

echo "==> Installing frontend deps and building..."
cd "$ROOT_DIR/frontend"

if command -v npm >/dev/null 2>&1; then
  npm install
  npm run build
else
  echo "ERROR: npm not found in PATH."
  exit 1
fi
echo "==> Setup complete!"