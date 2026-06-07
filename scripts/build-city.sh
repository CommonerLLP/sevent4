#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CITY="${1:-ahmedabad}"
CITY_DIR="$ROOT/data/cities/$CITY"
CONFIG="$CITY_DIR/city.yaml"
MANIFEST="$CITY_DIR/layers/layer_manifest.json"
OUT="$ROOT/public/cities/$CITY/index.html"

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing city config: $CONFIG" >&2
  exit 1
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing layer manifest: $MANIFEST" >&2
  exit 1
fi

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi

cd "$ROOT"
"$PY" -m sevent4.build_city_console \
  --city "$CONFIG" \
  --layers "$MANIFEST" \
  --out "$OUT"

echo "Built $CITY console: $OUT"
