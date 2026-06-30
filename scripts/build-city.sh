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

# The strip reads layers/ward_heat_summary.json at runtime. Build it from the
# SOURCE data/ layer (the truth), writing the sidecar into the published public/
# tree — so if a rebuild drops the heat layer, the stale summary is removed
# rather than rebuilt from a stale published copy.
"$PY" scripts/recipes/build_heat_summaries.py --tree data --write-tree public "$CITY"

echo "Built $CITY console: $OUT"
