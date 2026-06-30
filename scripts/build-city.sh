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

# The strip reads layers/ward_heat_summary.json at runtime. Only publish it when
# the manifest actually includes the heat layer — otherwise a console that
# intentionally dropped heat could still render the strip. When present, build it
# from the SOURCE data/ layer (the truth), writing the sidecar into public/; when
# absent, remove any stale published sidecar so the strip hides.
if grep -q '"ward_heat"' "$MANIFEST"; then
  "$PY" scripts/recipes/build_heat_summaries.py --tree data --write-tree public "$CITY"
else
  rm -f "$ROOT/public/cities/$CITY/layers/ward_heat_summary.json"
fi

echo "Built $CITY console: $OUT"
