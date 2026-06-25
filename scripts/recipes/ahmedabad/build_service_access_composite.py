#!/usr/bin/env python3
"""Build Ahmedabad ward and AC service-access composite fields."""
from __future__ import annotations

import argparse
from pathlib import Path

from sevent4.adapters.metrics_filesystem import (
    FileServiceAccessCompositeInputRepository,
    GeoJsonServiceAccessCompositeWriter,
)
from sevent4.application.metrics import build_service_access_composite


REPO = Path(__file__).resolve().parents[3]
LAYERS = REPO / "data/cities/ahmedabad/layers"
WARDS = LAYERS / "wards.geojson"
ACS = LAYERS / "acs.geojson"
CROSSWALK = LAYERS / "jurisdiction_crosswalk.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Ahmedabad ward and AC service-access composite fields.")
    parser.add_argument("--wards", type=Path, default=WARDS)
    parser.add_argument("--acs", type=Path, default=ACS)
    parser.add_argument("--crosswalk", type=Path, default=CROSSWALK)
    args = parser.parse_args()

    result = build_service_access_composite(
        FileServiceAccessCompositeInputRepository(args.wards, args.acs, args.crosswalk).load(),
        GeoJsonServiceAccessCompositeWriter(args.wards, args.acs),
    )
    _print_summary(result.summary)


def _print_summary(summary: dict) -> None:
    print(f"composite components (equal-weight): {', '.join(summary['components'])}")
    print(f"wards scored: {summary['wards_scored']}  |  ACs with AMC wards scored: {summary['acs_scored']}\n")
    print("ASSEMBLY CONSTITUENCIES by service gap (worst first) - gap, AMC wards, MLA:")
    for row in summary["ac_rankings"]:
        print(
            f"  gap {row['service_gap']:.3f}  ({row['amc_wards']:2d} wards)  "
            f"{row['ac_name']:22s} {row['representative']} [{row['party']}]"
        )
    print("\nWARDS by composite gap (worst first):")
    for row in summary["worst_wards"]:
        print(
            f"  gap {row['composite_gap']:.3f}  {row['name']:26s} "
            f"lib={row['libraries']} sch={row['schools']} hlth={row['health']} "
            f"buses/stop={row['buses_per_stop']} dep={row['deprivation']}"
        )


if __name__ == "__main__":
    main()
