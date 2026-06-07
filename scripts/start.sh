#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CITY="${1:-ahmedabad}"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  "$ROOT/scripts/setup.sh"
fi

"$ROOT/scripts/build-city.sh" "$CITY"
exec "$ROOT/scripts/serve.sh" "$CITY"
