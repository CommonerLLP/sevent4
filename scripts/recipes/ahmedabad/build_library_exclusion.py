#!/usr/bin/env python3
"""Per-ward library exclusion cross for Ahmedabad.

The paper documents two exclusion mechanisms separately — administrative
gatekeeping (Aadhaar / guarantor / deposit) and spatial library deserts — but
never crosses them. This recipe runs that cross at the ward level.

Two axes, both already on wards.geojson:
  * deprivation (0-1, already ward-resolved)
  * nearest_library_km, computed SPATIALLY from the 83-point library inventory
    (centroid -> nearest library point, EPSG:32643).

The headline is the DOUBLE-LOCKED quadrant: wards above the median on BOTH axes
(high deprivation AND far from a library), reported with the count of wards and
the total population affected.

Writes:
  * data/cities/ahmedabad/derived/library_access/library_exclusion_index.csv
  * data/cities/ahmedabad/derived/library_access/library_exclusion_summary.csv
  * data/cities/ahmedabad/layers/ward_library_exclusion.geojson  (atlas layer)
  * additive keys (exclusion_index, nearest_library_km, double_locked) onto
    wards.geojson — new keys only, existing properties untouched.

Thin CLI wrapper: the deprivation x access cross and summary live in
sevent4.domain.library_exclusion / sevent4.application.library_exclusion; the
geopandas spatial join and JSON/CSV IO live in the library-exclusion adapter.

    .venv/bin/python scripts/recipes/ahmedabad/build_library_exclusion.py
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.library_exclusion_filesystem import LibraryExclusionRepository
from sevent4.application.library_exclusion import build_library_exclusion

# Re-exported so existing importers (tests, downstream tools) keep a stable path.
from sevent4.domain.library_exclusion import (  # noqa: F401
    build_index,
    fnum,
    min_max_norm,
    nearest_point_distance_m,
    summarize,
    weighted_median,
)

REPO = Path(__file__).resolve().parents[3]


def main() -> None:
    repository = LibraryExclusionRepository(REPO)
    result = build_library_exclusion(repository.nearest_library_km(), repository.load_wards())

    repository.write_wards(result.wards)
    repository.write_exclusion_layer(result.exclusion_layer)
    repository.write_index_csv(result.indexed)
    repository.write_summary_csv(result.summary)

    for line in result.report_lines:
        print(line)
    print(f"\nwrote {repository.index_csv_path} ({len(result.indexed)} wards)")
    print(f"wrote {repository.exclusion_layer_relpath}")


if __name__ == "__main__":
    main()
