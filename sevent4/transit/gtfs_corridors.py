from __future__ import annotations

import argparse
from pathlib import Path

from sevent4.adapters.transit_filesystem import FileGtfsCorridorInputRepository, GeoJsonGtfsCorridorWriter
from sevent4.application.transit import build_gtfs_corridors


def main() -> None:
    parser = argparse.ArgumentParser(description="Build route corridor GeoJSON from a GTFS feed.")
    parser.add_argument("--gtfs-dir", required=True, help="Directory containing GTFS txt files")
    parser.add_argument("--out", required=True, help="Output GeoJSON path")
    args = parser.parse_args()
    build_corridors(Path(args.gtfs_dir), Path(args.out))


def build_corridors(gtfs_dir: Path, out: Path) -> None:
    result = build_gtfs_corridors(
        FileGtfsCorridorInputRepository(gtfs_dir).load(),
        GeoJsonGtfsCorridorWriter(out),
    )
    print(f"wrote {out} ({len(result.document['features'])} route corridors)")


if __name__ == "__main__":
    main()
