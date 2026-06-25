#!/usr/bin/env python3
"""Build a 30m Landsat surface-heat layer for a city. Thin CLI wrapper: the STAC
fetch + raster IO live in the heat adapters, the median/colour logic in the heat
application/domain layers.

    python3 scripts/recipes/ahmedabad/build_heat_layer.py --city ahmedabad
"""
from __future__ import annotations

import argparse
from pathlib import Path

from sevent4.adapters.heat_filesystem import FileHeatArtifactWriter, summary_json
from sevent4.adapters.heat_planetary import PlanetaryComputerHeatSource
from sevent4.application.heat import build_city_heat

REPO = Path(__file__).resolve().parents[3]

DEFAULT_CITY = "ahmedabad"
DEFAULT_BBOX = [72.45, 22.90, 72.74, 23.18]
DEFAULT_DATETIME = "2023-04-01/2025-06-30"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a 30m Landsat surface-heat layer for a city.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Defaults to Ahmedabad.")
    parser.add_argument("--bbox", nargs=4, type=float, default=DEFAULT_BBOX, metavar=("W", "S", "E", "N"))
    parser.add_argument("--datetime", default=DEFAULT_DATETIME, help="STAC datetime window.")
    parser.add_argument("--out-dir", help="Layer output directory.")
    parser.add_argument("--cloud-cover", type=float, default=20.0)
    args = parser.parse_args()

    city = args.city.lower()
    grid = PlanetaryComputerHeatSource().median_grid(args.bbox, args.datetime, args.cloud_cover)
    artifacts = build_city_heat(city, grid)
    FileHeatArtifactWriter(REPO, city, layers_dir=args.out_dir).write_raster_artifacts(artifacts)
    print(summary_json(artifacts.summary))


if __name__ == "__main__":
    main()
