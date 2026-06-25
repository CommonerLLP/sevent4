#!/usr/bin/env python3
"""Generic city build: turn acquired source/ data into the layers/ + manifest +
city.yaml the console renders. Normalises field names across cities, merges the
councillor roster onto wards, and writes a city-level governance.json (council
status + Municipal Commissioner) for the power-map popup.

Proven on Chennai; parameterised by --city so it scales to the rest.

    python3 scripts/recipes/build_city.py --city chennai
"""
from __future__ import annotations
import argparse
from pathlib import Path

from sevent4.adapters.city_build_filesystem import FileCityBuildArtifactWriter, FileCityBuildRepository
from sevent4.application.city_build import build_city_from_repository, city_build_summary_lines

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True)
    args = ap.parse_args()
    try:
        artifacts = build_city_from_repository(
            FileCityBuildRepository(ROOT, args.city),
            FileCityBuildArtifactWriter(ROOT, args.city),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    for line in city_build_summary_lines(artifacts):
        print(line)


if __name__ == "__main__":
    main()
