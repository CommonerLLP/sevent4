#!/usr/bin/env python3
"""Turn Delhi's mappable OpenCity downloads into committed atlas layers (thin CLI).

From data/cities/delhi/source/opencity/_raw/ (pulled by acquire_opencity.py):
  - villages-maps-of-delhi/*.kml  -> layers/villages.geojson (2022, district-tagged)
  - dissolve villages by district -> layers/districts.geojson (11 districts)
  - delhi-water-bodies-census-data/*.kml -> layers/water.geojson (893 points, 2023)

Microwatersheds (2,324 polys / 7 MB) is left in _raw — too heavy/niche for the
default console. Geometry simplification/repair and GeoJSON/manifest IO live in
sevent4.adapters.delhi_opencity_geospatial; the build order and manifest merge in
sevent4.application.delhi_opencity; the layer specs in sevent4.domain.delhi_opencity.

    .venv/bin/python scripts/recipes/delhi/build_opencity_layers.py
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.delhi_opencity_geospatial import DelhiOpenCityLayers
from sevent4.application.delhi_opencity import build_opencity_layers

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data/cities/delhi/source/opencity/_raw"
LAYERS = ROOT / "data/cities/delhi/layers"


def main() -> None:
    counts = build_opencity_layers(DelhiOpenCityLayers(RAW, LAYERS))
    print(f"delhi OpenCity layers: villages {counts['villages']}, "
          f"districts {counts['districts']}, water {counts['water']} -> {LAYERS}")


if __name__ == "__main__":
    main()
