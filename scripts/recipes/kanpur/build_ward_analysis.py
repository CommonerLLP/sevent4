#!/usr/bin/env python3
"""Per-ward analysis for Kanpur's PARTIAL ward layer (56 of 110 wards).

Honest-by-construction. Kanpur's only open ward vector (DataMeet, 2018) holds 56
of the city's 110 wards. Per-ward values are individually valid, but the SUM is
NOT the city total (Census-2011 KMC = 2,765,348 across 110 wards).

This recipe enriches each ward with area/density/heat and a `ward_coverage`
caveat, flags oversized (zone-sized) polygons, derives a heat-vulnerability flag
over clean wards only, propagates the fields into layers/ + public/, and prints
partial-only summary stats (NO city total claim).

Thin CLI wrapper: the area/density/heat-vulnerability math and field propagation
live in sevent4.domain.kanpur_wards / sevent4.application.kanpur; GeoJSON IO in
the Kanpur filesystem adapter.

Run (after the population join):  .venv/bin/python scripts/recipes/kanpur/build_ward_analysis.py
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.kanpur_filesystem import FileKanpurWardRepository
from sevent4.application.kanpur import analyze_kanpur_wards

REPO = Path(__file__).resolve().parents[3]


def main():
    repository = FileKanpurWardRepository(REPO)
    result = analyze_kanpur_wards(repository.load_source_wards(), repository.load_heat())
    repository.write_source_wards(result.wards)
    repository.propagate_ward_fields(result.wards)
    repository.propagate_heat_fields(result.wards)
    for line in result.summary_lines:
        print(line)


if __name__ == "__main__":
    main()
