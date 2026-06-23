#!/usr/bin/env python3
"""Scope (do NOT download) the OpenCity catalogue against the 74th-Amendment atlas frame.

Usage:
  python3 scripts/recipes/scope_opencity_for_atlas.py \
    --catalogue data/sources/opencity/_catalogue/opencity_catalogue.json \
    --cities bengaluru chennai kolkata mumbai \
    --out docs/opencity-atlas-scope.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from sevent4.application.acquisition import (
    build_opencity_atlas_scope_markdown,
    opencity_atlas_axis_labels,
    opencity_cut_hits,
    opencity_has_structured_resource,
    opencity_resource_formats,
)


def classify(dataset: dict[str, Any]) -> set[str]:
    return opencity_atlas_axis_labels(dataset)


def cut_hits(dataset: dict[str, Any]) -> dict[str, bool]:
    return opencity_cut_hits(dataset)


def fmts_of(dataset: dict[str, Any]) -> str:
    return opencity_resource_formats(dataset)


def has_structured(dataset: dict[str, Any]) -> bool:
    return opencity_has_structured_resource(dataset)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--cities", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    datasets = json.loads(Path(args.catalogue).read_text(encoding="utf-8"))["datasets"]
    markdown, axis_totals = build_opencity_atlas_scope_markdown(
        datasets,
        cities=args.cities,
        generator_path="scripts/recipes/scope_opencity_for_atlas.py",
    )
    Path(args.out).write_text(markdown, encoding="utf-8")

    print(f"wrote {args.out}")
    print("axis totals across cities:", axis_totals)


if __name__ == "__main__":
    main()
