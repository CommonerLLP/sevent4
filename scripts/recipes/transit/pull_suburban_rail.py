#!/usr/bin/env python3
"""First-pass suburban/commuter rail network from OpenStreetMap (Overpass).

Suburban rail is a UNION subject (Indian Railways) — the city's biggest
mass-transit spine, run two rungs above the elected municipality. This adds a
suburban layer (lines + stations) so the governance stack (Union rail vs state
metro vs city/state bus) is legible on one map.

DATA-TRUST: geometry is OSM — NON-AUTHORITATIVE per the atlas hierarchy. First
pass; clearly labelled OSM.

Writes per city: layers/suburban_rail.geojson, layers/suburban_rail_stations.geojson,
source/transit/suburban_rail.sources.json.

Thin CLI wrapper: bbox tiling, query builders, and feature shaping live in
sevent4.domain.suburban_rail / sevent4.application.comparators; Overpass + JSON
writes in the comparators adapter. (The previous version was corrupted with
missing-parens method calls; repaired in the refactor.)

  .venv/bin/python scripts/recipes/transit/pull_suburban_rail.py <city>
"""
from __future__ import annotations

import sys
from pathlib import Path

from sevent4.adapters.comparators_filesystem import overpass_rail, write_json
from sevent4.application.comparators import build_suburban_rail
from sevent4.domain.suburban_rail import BBOX, CONSTRUCTION

ROOT = Path(__file__).resolve().parents[3]


def run(city: str):
    line_fc, station_fc, sources, (n_lines, n_stations) = build_suburban_rail(city, overpass_rail)
    layers = ROOT / "data" / "cities" / city / "layers"
    src = ROOT / "data" / "cities" / city / "source" / "transit"
    write_json(line_fc, layers / "suburban_rail.geojson")
    write_json(station_fc, layers / "suburban_rail_stations.geojson")
    write_json(sources, src / "suburban_rail.sources.json", indent=1)

    note = " (network largely UNDER CONSTRUCTION)" if CONSTRUCTION.get(city) else ""
    print(f"[{city}] {n_lines} route lines · {n_stations} stations{note}", file=sys.stderr)
    return n_lines, n_stations


if __name__ == "__main__":
    for c in (sys.argv[1:] or ["kolkata"]):
        if c not in BBOX:
            sys.exit(f"unknown city {c}; known: {list(BBOX)}")
        run(c)
