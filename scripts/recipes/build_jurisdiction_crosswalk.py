#!/usr/bin/env python3
"""Build jurisdiction_crosswalk.json for ward/AC/PC console filters.

Run:
    .venv/bin/python scripts/recipes/build_jurisdiction_crosswalk.py <city> [<city> ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

from sevent4.adapters.jurisdiction_geospatial import RepresentativePointJurisdictionRepository
from sevent4.application.jurisdiction import publish_representative_point_crosswalk


ROOT = Path(__file__).resolve().parents[2]


def build(city: str):
    repository = RepresentativePointJurisdictionRepository(ROOT)
    result = publish_representative_point_crosswalk(city, repository, repository)
    print(
        f"[{city}] crosswalk: {result.ward_count} wards -> "
        f"{result.ac_count} ACs, {result.pc_count} PCs",
        file=sys.stderr,
    )
    return result.document


if __name__ == "__main__":
    for city in (sys.argv[1:] or ["kolkata", "chennai"]):
        build(city)
