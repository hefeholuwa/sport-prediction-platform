#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR/backend"

echo "Starting Football Prediction Backend API on http://0.0.0.0:8000..."
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
