#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

cd "$ROOT"

if [[ ! -d .venv ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# install the sevent4 package itself (editable) so the recipe wrappers under
# scripts/ can `import sevent4...` when run by path with .venv/bin/python.
python -m pip install -e .

echo "The Unelected City environment ready: $ROOT/.venv"
