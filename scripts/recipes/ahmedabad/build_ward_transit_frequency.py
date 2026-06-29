#!/usr/bin/env python3
"""Build Ahmedabad ward-level AMTS/Janmarg frequency fields."""
from __future__ import annotations

import argparse
from pathlib import Path

from sevent4.adapters.metrics_filesystem import (
    FileWardTransitFrequencyInputRepository,
    GeoJsonWardTransitFrequencyWriter,
)
from sevent4.application.metrics import build_ward_transit_frequency


REPO = Path(__file__).resolve().parents[3]
GTFS = REPO / "data/cities/ahmedabad/source/gtfs/amts_janmarg"
WARDS = REPO / "data/cities/ahmedabad/layers/wards.geojson"


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge AMTS/Janmarg frequency fields onto Ahmedabad wards.")
    parser.add_argument("buffer_m", nargs="?", type=float, default=2500.0)
    parser.add_argument("--gtfs-dir", type=Path, default=GTFS)
    parser.add_argument("--wards", type=Path, default=WARDS)
    args = parser.parse_args()
    if not args.gtfs_dir.exists():
        raise SystemExit(
            f"GTFS feed not found at {args.gtfs_dir}. GTFS feeds are gitignored external inputs "
            f"— supply one with --gtfs-dir or place the txt files there."
        )

    result = build_ward_transit_frequency(
        FileWardTransitFrequencyInputRepository(args.wards, args.gtfs_dir, buffer_m=args.buffer_m).load(),
        GeoJsonWardTransitFrequencyWriter(args.wards),
    )
    _print_summary(result.summary)


def _print_summary(summary: dict) -> None:
    print(
        f"stops with service: {summary['service_stops']}  |  "
        f"strict in-ward: {summary['strict_assigned_stops']}  |  "
        f"outside AMC wards: {summary['outside_ward_stops']}"
    )
    print(f"closing the hole (nearest ward within {summary['buffer_m']:.0f} m):")
    for label, count in summary["distance_buckets"].items():
        print(f"    {label:20s} {count:5d}")
    print(
        f"    -> reassigned {summary['reassigned_stops']} stops "
        f"({summary['reassigned_amts_events']:,} extra AMTS buses/day pulled in)"
    )
    print()
    print("CORRELATION  (deprivation higher = more deprived; negative = deprived get less)")
    for label, correlations in (
        ("strict (in-ward)", summary["strict_correlations"]),
        ("incl. peri-urban", summary["inclusive_correlations"]),
    ):
        print(
            f"  {label:18s}  dep x buses/day  "
            f"r={correlations['deprivation_buses_pearson']:+.2f} "
            f"rho={correlations['deprivation_buses_spearman']:+.2f}   |  "
            f"dep x buses/stop  r={correlations['deprivation_buses_per_stop_pearson']:+.2f} "
            f"rho={correlations['deprivation_buses_per_stop_spearman']:+.2f}"
        )
    print()
    print("by deprivation quartile (Q4 = most deprived), INCLUSIVE:")
    print("  quartile   mean buses/day   mean buses/stop")
    for row in summary["deprivation_quartiles"]:
        print(f"  {row['quartile']:8s}   {row['mean_buses_day']:12.0f}   {row['mean_buses_per_stop']:15.1f}")
    print()
    print("lowest buses/stop wards (name, deprivation, buses/day, buses/stop, brts):")
    for row in summary["lowest_buses_per_stop"]:
        print(
            f"  {row['name']:28s} dep={row['deprivation']:.3f}  "
            f"buses/day={row['amts_buses_day']:6d}  "
            f"buses/stop={row['buses_per_stop']:5.1f}  brts={row['brts_stops']}"
        )


if __name__ == "__main__":
    main()
