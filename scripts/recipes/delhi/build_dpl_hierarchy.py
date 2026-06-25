#!/usr/bin/env python3
"""Build the Delhi Public Library service-hierarchy detail + summary CSVs.

DPL is a hierarchy (headquarters / zonal / branch / special-fixed / sub-branch /
community / mobile), not a flat point set. Thin CLI wrapper: tier classification,
provenance grouping, and the summary live in sevent4.domain.dpl_hierarchy /
sevent4.application.dpl_hierarchy; CSV IO in the dpl-hierarchy adapter.
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.dpl_hierarchy_filesystem import read_csv, write_csv
from sevent4.application.dpl_hierarchy import build_dpl_service_hierarchy

# Re-exported so the existing test (imports these from this module) stays stable.
from sevent4.domain.dpl_hierarchy import (  # noqa: F401
    DETAIL_FIELDS,
    SUMMARY_FIELDS,
    TIER_RANK,
    classify_service_tier,
    coordinate_provenance_group,
    count_present,
    hierarchy_rows,
    notes_for_row,
    physical_access_model,
    summarize_hierarchy,
    value,
)

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "data" / "cities" / "delhi" / "source" / "libraries" / "dpl_library_locations.csv"
GEOCODED = REPO / "data" / "cities" / "delhi" / "derived" / "geocoding" / "dpl_geocoded.csv"
OUT_DIR = REPO / "data" / "cities" / "delhi" / "derived" / "library_access"
DETAIL_OUT = OUT_DIR / "dpl_service_hierarchy.csv"
SUMMARY_OUT = OUT_DIR / "dpl_service_hierarchy_summary.csv"


def main() -> None:
    source_rows = read_csv(SOURCE)
    geocoded_rows = read_csv(GEOCODED) if GEOCODED.exists() else []
    detail_rows, summary = build_dpl_service_hierarchy(source_rows, geocoded_rows)
    write_csv(DETAIL_OUT, detail_rows, DETAIL_FIELDS)
    write_csv(SUMMARY_OUT, [summary], SUMMARY_FIELDS)
    print(f"wrote {DETAIL_OUT.relative_to(REPO)} ({len(detail_rows)} rows)")
    print(f"wrote {SUMMARY_OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
