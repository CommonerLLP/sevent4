#!/usr/bin/env python3
"""Spatial analysis of the Delhi Public Library fixed network (thin CLI wrapper).

Inputs:
  - data/cities/delhi/derived/geocoding/dpl_geocoded.csv  (located fixed libraries)
  - data/cities/delhi/layers/{districts,wards,metro,metro_lines}.geojson

Outputs:
  - data/cities/delhi/layers/dpl_libraries.geojson  (authoritative DPL fixed network
    for the console — distinct from OSM's partial `libraries`)
  - docs/figures/figD3_dpl_walk_access.png  (ward distance-to-nearest-DPL choropleth)
  - docs/figures/figD4_dpl_transit_siting.png (DPL vs Metro/bus network)
  - prints summary stats for the paper

Honest framing: most coordinates are verified, the rest approximate; the maps show
the FIXED network only (mobile service points are not fixed access). Treat the
numbers as indicative of sparsity, not survey-grade. The metric computation and
figure rendering live in sevent4.adapters.delhi_library_spatial_geospatial; the
order and stats shaping in sevent4.application/.domain.delhi_library_spatial.

Run: .venv/bin/python scripts/recipes/delhi/build_library_spatial.py
"""
from __future__ import annotations

import json
from pathlib import Path

from sevent4.adapters.delhi_library_spatial_geospatial import DelhiLibrarySpatial
from sevent4.application.delhi_library_spatial import build_library_spatial

ROOT = Path(__file__).resolve().parents[3]
LAYERS = ROOT / "data/cities/delhi/layers"
GEO = ROOT / "data/cities/delhi/derived/geocoding/dpl_geocoded.csv"
FIG = ROOT / "docs/figures"


def main() -> None:
    stats = build_library_spatial(DelhiLibrarySpatial(GEO, LAYERS, FIG))
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
