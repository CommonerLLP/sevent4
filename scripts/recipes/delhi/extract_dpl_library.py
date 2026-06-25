#!/usr/bin/env python3
"""Extract Delhi Public Library finance, operations, and location tables.

Thin CLI wrapper: pure parsing and derived metrics live in
sevent4.domain.delhi_dpl_extract; build order lives in
sevent4.application.delhi_dpl_extract; filesystem/CSV IO lives in
sevent4.adapters.delhi_dpl_extract_filesystem.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import sevent4.adapters.delhi_dpl_extract_filesystem as dpl_store
from sevent4.application.delhi_dpl_extract import build_dpl_library

# Re-exported for existing tests/importers.
from sevent4.adapters.delhi_dpl_extract_filesystem import extract_dpl_locations  # noqa: F401
from sevent4.domain.delhi_dpl_extract import (  # noqa: F401
    ANNUAL_FIELDS,
    DPL_LOCATION_FIELDS,
    GEOCODE_CACHE_FIELDS,
    MANIFEST_FIELDS,
    METRICS_LONG_FIELDS,
    TIME_SERIES_FIELDS,
    geocode_cache_rows,
)

REPO = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_DIR = Path("/private/tmp/dpl-targeted-20260613")
DEFAULT_OUT_DIR = REPO / "data" / "cities" / "delhi" / "source" / "libraries"
DEFAULT_GEOCODE_DIR = REPO / "data" / "cities" / "delhi" / "source" / "geocoding"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Delhi Public Library finance/operations metrics.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--geocode-dir", type=Path, default=DEFAULT_GEOCODE_DIR)
    args = parser.parse_args()

    result = build_dpl_library(dpl_store, args.source_dir, args.out_dir, args.geocode_dir)
    out_dir = result["out_dir"]
    geocode_dir = result["geocode_dir"]
    print(f"wrote {out_dir / 'dpl_fetch_manifest.csv'} ({result['manifest_rows']} rows)")
    print(f"wrote {out_dir / 'dpl_annual_metrics.csv'} ({result['annual_rows']} rows)")
    print(f"wrote {out_dir / 'dpl_ten_year_time_series.csv'} ({result['ten_year_rows']} rows)")
    print(f"wrote {out_dir / 'dpl_online_annual_time_series.csv'} ({result['online_rows']} rows)")
    print(f"wrote {out_dir / 'dpl_metrics_long.csv'} ({result['long_rows']} rows)")
    print(f"wrote {out_dir / 'dpl_library_locations.csv'} ({result['location_rows']} rows)")
    print(f"wrote {geocode_dir / 'geocode_cache.csv'} ({result['geocode_cache_rows']} rows)")


if __name__ == "__main__":
    main()
