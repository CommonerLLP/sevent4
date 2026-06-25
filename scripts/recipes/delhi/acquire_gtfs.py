#!/usr/bin/env python3
"""Ingest a GTFS feed (zip or extracted dir) into atlas layer GeoJSONs.

Builds bus_routes.geojson (one LineString per route, from shapes.txt if present
else reconstructed from the longest trip's stop sequence) + bus_stops.geojson.
The OTD Delhi static GTFS download needs no key; realtime feeds need OTD_API_KEY
(read only from the environment, never committed).

Thin CLI wrapper: the GTFS geometry shaping lives in sevent4.domain.delhi_acquire /
sevent4.application.delhi_acquire; feed loading, the OTD download, and JSON IO in
the delhi-acquire adapter.

    .venv/bin/python scripts/recipes/delhi/acquire_gtfs.py --zip /path/to/GTFS.zip
    .venv/bin/python scripts/recipes/delhi/acquire_gtfs.py --dir /path/to/extracted
    .venv/bin/python scripts/recipes/delhi/acquire_gtfs.py --download   # public OTD static
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sevent4.adapters.delhi_acquire_filesystem import download_otd_static, load_gtfs_feed, write_geojson
from sevent4.application.delhi_acquire import acquire_gtfs_layers

ROOT = Path(__file__).resolve().parents[3]
LAYERS = ROOT / "data/cities/delhi/layers"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--zip", help="path to a GTFS .zip")
    g.add_argument("--dir", help="path to an extracted GTFS dir")
    ap.add_argument("--download", action="store_true", help="download the public OTD static GTFS bundle (no key)")
    ap.add_argument("--prefix", default="bus", help="output basename prefix (default 'bus')")
    ap.add_argument("--out", default=str(LAYERS), help="output layers dir")
    ap.add_argument("--insecure", action="store_true", help="skip TLS verification for --download (expired OTD cert)")
    args = ap.parse_args()

    zip_path = args.zip
    if args.download and not zip_path and not args.dir:
        import tempfile

        zip_path = str(Path(tempfile.gettempdir()) / "otd_gtfs.zip")
        print(f"downloading OTD static GTFS -> {zip_path}", file=sys.stderr)
        download_otd_static(Path(zip_path), verify=not args.insecure)

    if not zip_path and not args.dir:
        ap.error("provide --zip, --dir, or --download")

    tables = load_gtfs_feed(zip_path, args.dir)
    for required in ("routes", "trips", "stops"):
        if required not in tables:
            ap.error(f"feed is missing {required}.txt")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        n_routes, n_stops, method = acquire_gtfs_layers(
            tables, lambda fc, base: write_geojson(fc, out / f"{base}.geojson"), args.prefix
        )
    except ValueError as e:
        ap.error(str(e))
    print(f"{args.prefix}: {n_routes} routes ({method}), {n_stops} stops")


if __name__ == "__main__":
    main()
