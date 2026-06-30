#!/usr/bin/env python3
"""Write each city's tiny ward_heat_summary.json (top hottest wards) from its
ward_heat.geojson, so the console heat strip reads it at runtime.

Decoupled from the console build on purpose: the scheduled heat refresh re-runs
this (no geo deps, no console rebuild) and the live strips update on deploy.

    .venv/bin/python scripts/recipes/build_heat_summaries.py            # public tree
    .venv/bin/python scripts/recipes/build_heat_summaries.py --tree data

Thin CLI wrapper: the read + write live in the heat filesystem adapter, the
ranking in the heat domain.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from sevent4.adapters.heat_filesystem import (
    load_ward_heat,
    remove_ward_heat_summary,
    write_ward_heat_summary,
)
from sevent4.domain.heat import hottest_wards

REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build per-city ward heat summaries.")
    parser.add_argument("--tree", default="public", help='Layer tree: "public" (default) or "data".')
    parser.add_argument("cities", nargs="*", help="City ids (default: every city under the tree).")
    args = parser.parse_args()

    cities_root = REPO / args.tree / "cities"
    cities = args.cities or sorted(p.name for p in cities_root.iterdir() if (p / "layers").is_dir())

    written = 0
    for city in cities:
        layers_dir = cities_root / city / "layers"
        document = load_ward_heat(layers_dir)
        summary = hottest_wards(document.get("features", [])) if document else None
        if summary is None:
            # No usable ward data — remove any stale sidecar so the strip hides
            # rather than rendering obsolete hottest wards.
            if remove_ward_heat_summary(layers_dir):
                print(f"{city}: no ward_heat — removed stale summary", flush=True)
            else:
                print(f"{city}: no ward_heat — skipped", flush=True)
            continue
        out = write_ward_heat_summary(layers_dir, summary)
        written += 1
        print(f"{city}: {summary['top'][0]['ward']} {summary['top'][0]['lst']}C -> {out}", flush=True)
    print(f"\nwrote {written} heat summaries")


if __name__ == "__main__":
    main()
