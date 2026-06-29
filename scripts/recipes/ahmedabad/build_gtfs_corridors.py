#!/usr/bin/env python3
"""Build city transit route-corridor layers from GTFS, split per agency. Thin
CLI wrapper: corridor construction and agency splitting live in the transit
application service; GTFS reads and GeoJSON writes in the transit adapters.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from sevent4.adapters.transit_filesystem import (
    AgencyCorridorWriter,
    FileGtfsCorridorInputRepository,
    GeoJsonGtfsCorridorWriter,
)
from sevent4.application.transit import build_gtfs_corridors, split_corridors_by_agency

REPO = Path(__file__).resolve().parents[3]

# Ahmedabad is the first city recipe. The same wrapper can be reused when another
# city supplies a GTFS feed under data/cities/<city>/source/gtfs/.
DEFAULT_CITY = "ahmedabad"
AGENCY_OUTPUTS = {
    "AMTS": "corr_amts.geojson",
    "AJL": "corr_brts.geojson",
}
ALL_ROUTES = "gtfs_corridors.geojson"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build city transit route corridor layers from GTFS.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Defaults to Ahmedabad.")
    parser.add_argument("--gtfs-dir", help="Directory containing GTFS txt files.")
    parser.add_argument("--out-dir", help="Layer output directory.")
    parser.add_argument("--keep-all", action="store_true", help="Also write gtfs_corridors.geojson with all routes.")
    args = parser.parse_args()

    city = args.city.lower()
    gtfs_dir = Path(args.gtfs_dir) if args.gtfs_dir else REPO / "data" / "cities" / city / "source" / "gtfs" / "amts_janmarg"
    if not gtfs_dir.exists():
        raise SystemExit(
            f"GTFS feed not found at {gtfs_dir}. GTFS feeds are gitignored external inputs "
            f"— supply one with --gtfs-dir or place the txt files there."
        )
    out_dir = Path(args.out_dir) if args.out_dir else REPO / "data" / "cities" / city / "layers"
    all_routes_path = out_dir / ALL_ROUTES

    result = build_gtfs_corridors(
        FileGtfsCorridorInputRepository(gtfs_dir).load(),
        GeoJsonGtfsCorridorWriter(all_routes_path),
    )
    print(f"wrote {all_routes_path} ({len(result.document['features'])} route corridors)")

    agency_writer = AgencyCorridorWriter(out_dir)
    for filename, document in split_corridors_by_agency(result.document, AGENCY_OUTPUTS).items():
        count = agency_writer.write(filename, document)
        print(f"wrote {out_dir / filename} ({count} routes)")
    if not args.keep_all:
        agency_writer.remove(ALL_ROUTES)


if __name__ == "__main__":
    main()
