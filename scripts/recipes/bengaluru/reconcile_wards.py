#!/usr/bin/env python3
"""Build Bengaluru's four-axis ward-analysis layer.

Thin CLI wrapper: feature and manifest shaping live in
sevent4.domain.bengaluru_ward_analysis, orchestration in
sevent4.application.bengaluru_ward_analysis, and geospatial/filesystem IO in
sevent4.adapters.bengaluru_ward_analysis_geospatial.
"""
from __future__ import annotations

import sevent4.adapters.bengaluru_ward_analysis_geospatial as ward_store
from sevent4.application.bengaluru_ward_analysis import reconcile_ward_analysis
from sevent4.domain.bengaluru_ward_analysis import correlation, correlation_rows, nk  # noqa: F401


def main() -> None:
    result = reconcile_ward_analysis(ward_store)
    print(
        f"canonical wards: {result['wards']} (BBMP-2023) | spend-joined: {result['spend_joined']} "
        f"| heat-transferred: {result['heat_transferred']}"
    )
    print("\n── cross-axis correlations (Pearson r, n) ──")
    for label, value, count in result["correlations"]:
        print(f"  {label:42} r={value}  (n={count})")
    print("\nwrote ward_analysis.geojson + patched manifest (group 'Four-axis')")


if __name__ == "__main__":
    main()
