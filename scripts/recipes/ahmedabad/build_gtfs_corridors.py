#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from sevent4.transit.gtfs_corridors import build_corridors

# Ahmedabad is the first city recipe. The same wrapper can be reused when another
# city supplies a GTFS feed under data/cities/<city>/source/gtfs/.
DEFAULT_CITY = "ahmedabad"
AGENCY_OUTPUTS = {
    "AMTS": "corr_amts.geojson",
    "AJL": "corr_brts.geojson",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build city transit route corridor layers from GTFS.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Defaults to Ahmedabad.")
    parser.add_argument("--gtfs-dir", help="Directory containing GTFS txt files.")
    parser.add_argument("--out-dir", help="Layer output directory.")
    parser.add_argument("--keep-all", action="store_true", help="Also write gtfs_corridors.geojson with all routes.")
    args = parser.parse_args()

    city = args.city.lower()
    gtfs_dir = Path(args.gtfs_dir) if args.gtfs_dir else REPO / "data" / "cities" / city / "source" / "gtfs" / "amts_janmarg"
    out_dir = Path(args.out_dir) if args.out_dir else REPO / "data" / "cities" / city / "layers"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_routes = out_dir / "gtfs_corridors.geojson"
    build_corridors(gtfs_dir, all_routes)
    split_by_agency(all_routes, out_dir)
    if not args.keep_all:
        all_routes.unlink(missing_ok=True)


def split_by_agency(all_routes: Path, out_dir: Path) -> None:
    data = json.loads(all_routes.read_text(encoding="utf-8"))
    features = data.get("features", [])
    for agency, filename in AGENCY_OUTPUTS.items():
        selected = []
        for feature in features:
            props = feature.get("properties") or {}
            if props.get("agency_id") == agency:
                selected.append({
                    "type": "Feature",
                    "properties": {"kind": agency},
                    "geometry": feature.get("geometry"),
                })
        out = out_dir / filename
        out.write_text(json.dumps({"type": "FeatureCollection", "features": selected}, separators=(",", ":")), encoding="utf-8")
        print(f"wrote {out} ({len(selected)} routes)")


if __name__ == "__main__":
    main()
