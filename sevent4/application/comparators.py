from __future__ import annotations

import sys

from sevent4.domain.opencity_catalogue import build_catalogue, catalogue_markdown
from sevent4.domain.suburban_rail import (
    BBOX,
    collect_stations,
    collect_ways,
    line_features,
    q_rail,
    q_stations,
    rail_sources,
    station_features,
    tiles,
)


def build_opencity_catalogue(pkgs: list[dict]) -> tuple[dict, str]:
    cat = build_catalogue(pkgs)
    return cat, catalogue_markdown(cat)


def build_suburban_rail(city: str, overpass_fn):
    """overpass_fn(query)->overpass json. Tiles the bbox, dedups ways/stations,
    shapes GeoJSON. Returns (lines_fc, stations_fc, sources, (n_lines, n_stations))."""
    bbox = BBOX[city]
    ways: dict = {}
    for bb in tiles(bbox):
        try:
            j = overpass_fn(q_rail(bb))
        except RuntimeError as e:
            print(f"  [skip tile {bb}] {e}", file=sys.stderr)
            continue
        collect_ways(j.get("elements", []), ways)

    snodes: dict = {}
    for bb in tiles(bbox, 4, 4):
        try:
            j = overpass_fn(q_stations(bb))
        except RuntimeError as e:
            print(f"  [skip stn tile {bb}] {e}", file=sys.stderr)
            continue
        collect_stations(j.get("elements", []), snodes)

    lines = line_features(ways)
    stations = station_features(snodes)
    return (
        {"type": "FeatureCollection", "features": lines},
        {"type": "FeatureCollection", "features": stations},
        rail_sources(city),
        (len(lines), len(stations)),
    )
