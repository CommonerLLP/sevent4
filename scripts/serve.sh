#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CITY="${1:-ahmedabad}"
PORT="${PORT:-9174}"

cd "$ROOT"

echo "Serving The Unelected City from $ROOT"
echo "Open: http://127.0.0.1:$PORT/index.html"
echo "City console: http://127.0.0.1:$PORT/public/cities/$CITY/index.html"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  exec "$ROOT/.venv/bin/python" -m http.server "$PORT" --bind 127.0.0.1
fi

exec "${PYTHON:-python3}" -m http.server "$PORT" --bind 127.0.0.1
