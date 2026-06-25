#!/usr/bin/env python3
"""Pull Delhi transit + service layers from OpenStreetMap (Overpass) into the
atlas, writing into data/cities/delhi/layers/ and registering each in
layer_manifest.json (idempotent).

Thin CLI wrapper: the Overpass query builder, GeoJSON shaping, and manifest merge
live in sevent4.domain.delhi_acquire / sevent4.application.delhi_acquire; the
Overpass POST + JSON IO in the delhi-acquire adapter.

    .venv/bin/python scripts/recipes/delhi/acquire_osm.py
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.delhi_acquire_filesystem import load_layer_manifest, overpass_post, write_geojson, write_json
from sevent4.application.delhi_acquire import acquire_osm_layers

ROOT = Path(__file__).resolve().parents[3]
LAYERS = ROOT / "data/cities/delhi/layers"


def main() -> None:
    manifest = load_layer_manifest(LAYERS / "layer_manifest.json")
    counts = acquire_osm_layers(
        overpass_post,
        lambda fc, lid: write_geojson(fc, LAYERS / f"{lid}.geojson"),
        manifest,
    )
    write_json(manifest, LAYERS / "layer_manifest.json", indent=2)
    print("delhi OSM layers:", ", ".join(f"{k} {v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
