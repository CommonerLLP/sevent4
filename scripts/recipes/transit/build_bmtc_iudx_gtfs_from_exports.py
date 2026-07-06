#!/usr/bin/env python3
"""Build a BMTC static GTFS zip from approved IUDX table exports."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sevent4.transit.iudx_gtfs_export import (
    REQUIRED_GTFS_FILES,
    load_static_gtfs_tables_from_json_dir,
    summarize_static_gtfs_quality,
    write_static_gtfs_zip_from_tables,
)


def build_bmtc_iudx_gtfs_from_exports(
    *,
    input_dir: str | Path,
    out_zip: str | Path,
    provenance_path: str | Path,
    manifest_row_path: str | Path | None = None,
    feed_manifest_path: str | Path | None = None,
    generated_at: str,
) -> dict[str, Any]:
    tables = load_static_gtfs_tables_from_json_dir(input_dir)
    row_counts = write_static_gtfs_zip_from_tables(tables, out_zip)
    quality_checks = summarize_static_gtfs_quality(tables)
    provenance = {
        "schema": "sevent4.bengaluru_bmtc_iudx_gtfs_export.sources.v1",
        "feed_id": "bengaluru_bmtc_iudx_full_gtfs",
        "status": "iudx_policy_approved_export",
        "generated_at": generated_at,
        "input_dir": str(input_dir),
        "gtfs_zip": str(out_zip),
        "required_input_tables": [filename.replace(".txt", ".json") for filename in REQUIRED_GTFS_FILES],
        "row_counts": row_counts,
        "quality_checks": quality_checks,
        "notes": (
            "Static GTFS built from BMTC IUDX table exports after policy access. "
            "The export requires stop_times.json; without it route geometry remains incomplete."
        ),
    }
    path = Path(provenance_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(provenance, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if manifest_row_path is not None:
        row_path = Path(manifest_row_path)
        row_path.parent.mkdir(parents=True, exist_ok=True)
        row_path.write_text(
            json.dumps(build_bmtc_iudx_manifest_feed_row(provenance), ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
    if feed_manifest_path is not None:
        manifest_path = Path(feed_manifest_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "schema": "sevent4.multimodal_transit.manifest.v1",
                    "feeds": [build_bmtc_iudx_manifest_feed_row(provenance)],
                },
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )
    return provenance


def build_bmtc_iudx_manifest_feed_row(provenance: dict[str, Any]) -> dict[str, Any]:
    quality_checks = provenance.get("quality_checks", {})
    if not isinstance(quality_checks, dict) or not quality_checks.get("route_geometry_ready"):
        raise ValueError("BMTC IUDX provenance quality_checks.route_geometry_ready must be true")
    return {
        "feed_id": "bengaluru_bmtc_iudx_full_gtfs",
        "city": "bengaluru",
        "mode": "bus",
        "operator": "Bangalore Metropolitan Transport Corporation",
        "status": "ok",
        "source_url": "https://catalogue.iudx.org.in/bengaluru",
        "license": "IUDX policy-approved BMTC static GTFS export.",
        "path": str(provenance["gtfs_zip"]),
        "stop_layer": "bus_stops",
        "route_layer": "bus_routes",
        "stop_features": int(quality_checks.get("stop_count", 0)),
        "route_features": int(quality_checks.get("route_count", 0)),
        "quality_checks": quality_checks,
        "notes": (
            "Replace the gated BMTC IUDX row only after this exported GTFS has "
            "been converted into public stop and route layers."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build BMTC GTFS from approved IUDX JSON table exports.")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--out-zip", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--manifest-row", type=Path)
    parser.add_argument("--feed-manifest", type=Path)
    parser.add_argument("--generated-at")
    args = parser.parse_args()

    generated_at = args.generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    result = build_bmtc_iudx_gtfs_from_exports(
        input_dir=args.input_dir,
        out_zip=args.out_zip,
        provenance_path=args.provenance,
        manifest_row_path=args.manifest_row,
        feed_manifest_path=args.feed_manifest,
        generated_at=generated_at,
    )
    print(json.dumps({"gtfs_zip": result["gtfs_zip"], "row_counts": result["row_counts"]}, indent=1))


if __name__ == "__main__":
    main()
