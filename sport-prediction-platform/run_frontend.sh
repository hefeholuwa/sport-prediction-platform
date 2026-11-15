#!/data/data/com.termux/files/usr/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR/frontend"

echo "Starting Football Prediction Frontend UI on http://0.0.0.0:3000..."
exec node ./node_modules/vite/bin/vite.js --host 0.0.0.0 --port 3000
