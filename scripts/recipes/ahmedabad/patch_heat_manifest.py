#!/usr/bin/env python3
"""Add the ward_heat + heat30m Climate layers to a city's layer_manifest.json.

Mirrors the Ahmedabad manifest entries. Idempotent: if a layer id already
exists it is replaced in place rather than duplicated. Only runs when the
city actually has the heat outputs on disk.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

WARD_HEAT = {
    "id": "ward_heat",
    "label": "Ward heat",
    "file": "ward_heat.geojson",
    "kind": "fill",
    "group": "Climate",
    "default": False,
    "outline": True,
    "popup": ["Name", "mean_lst_c", "max_lst_c"],
    "paint": {
        "fill-color": [
            "interpolate", ["linear"], ["to-number", ["get", "mean_lst_c"], 35],
            32, "#2c7a55", 36, "#d7b33f", 39, "#d36b32", 42, "#9f2d2d",
        ],
        "fill-opacity": 0.58,
    },
}

HEAT30M = {
    "id": "heat30m",
    "label": "Surface heat - 30m",
    "file": "heat30m.png",
    "bounds_file": "heat30m_bounds.json",
    "kind": "image",
    "group": "Climate",
    "default": False,
    "popup": [],
    "paint": {"raster-opacity": 0.78, "raster-resampling": "nearest"},
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True)
    args = parser.parse_args()
    city = args.city.lower()
    layers = REPO / "data" / "cities" / city / "layers"
    manifest_path = layers / "layer_manifest.json"
    if not manifest_path.exists():
        sys.exit(f"No manifest at {manifest_path}")
    if not (layers / "heat30m.png").exists() or not (layers / "ward_heat.geojson").exists():
        sys.exit(f"{city}: heat outputs missing, not patching manifest")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    existing = manifest.get("layers", [])
    by_id = {l.get("id"): i for i, l in enumerate(existing)}

    for entry in (WARD_HEAT, HEAT30M):
        if entry["id"] in by_id:
            existing[by_id[entry["id"]]] = entry
        else:
            existing.append(entry)
    manifest["layers"] = existing
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"{city}: manifest patched with ward_heat + heat30m")


if __name__ == "__main__":
    main()
