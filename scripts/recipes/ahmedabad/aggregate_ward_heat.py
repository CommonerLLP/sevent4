#!/usr/bin/env python3
"""Aggregate the 30m Landsat LST raster (heat30m.tif) to ward polygons.

For each ward in wards.geojson, computes mean and max land-surface temperature
(degrees C) over the heat raster and writes ward_heat.geojson. Thin CLI wrapper:
raster sampling + GeoJSON IO live in the heat adapters, the per-ward statistics
in the heat application/domain layers.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sevent4.adapters.heat_filesystem import (
    FileHeatArtifactWriter,
    FileWardHeatRepository,
    summary_json,
)
from sevent4.application.heat import aggregate_ward_heat

REPO = Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate LST raster to wards.")
    parser.add_argument("--city", required=True)
    parser.add_argument("--layers-dir", help="Override layers dir.")
    args = parser.parse_args()

    city = args.city.lower()
    repository = FileWardHeatRepository(REPO, city, layers_dir=args.layers_dir)
    if not repository.heat_tif_exists():
        sys.exit(f"No heat raster at {repository.layers_dir / 'heat30m.tif'}")
    if not repository.wards_exist():
        sys.exit(f"No wards at {repository.layers_dir / 'wards.geojson'}")

    wards = repository.load_wards()
    with repository.open_sampler() as (sample, nodata):
        document, summary = aggregate_ward_heat(wards, sample, nodata)
    FileHeatArtifactWriter(REPO, city, layers_dir=args.layers_dir).write_ward_heat(document)
    print(summary_json({"city": city, **summary}, indent=None))


if __name__ == "__main__":
    main()
