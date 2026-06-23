#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from sevent4.adapters.acquisition_filesystem import CsvJsonAtlasInventoryWriter, JsonCatalogueRepository
from sevent4.application.acquisition import (
    INVENTORY_FIELDS,
    build_atlas_source_inventory,
    city_catalogue_candidate,
    classify_dataset as classify_catalogue_dataset,
    enrich_catalogue_datasets,
    flatten_catalogue_inventory_rows,
    opencity_atlas_axis_labels,
    shortlist_dataset,
)

DEFAULT_CATALOGUE = REPO / "data" / "sources" / "opencity" / "_catalogue" / "opencity_catalogue.json"
DEFAULT_OUT_DIR = REPO / "data" / "cities" / "delhi" / "source" / "opencity"
INVENTORY_FILENAME = "delhi_opencity_inventory.csv"
SHORTLIST_FILENAME = "delhi_opencity_atlas_shortlist.csv"
MANIFEST_FILENAME = "delhi_opencity_manifest.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Delhi OpenCity source inventory for the municipality atlas.")
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    inventory = build_atlas_source_inventory(
        JsonCatalogueRepository(args.catalogue, REPO).load(),
        city="delhi",
        classify=opencity_atlas_axis_labels,
        inventory_filename=INVENTORY_FILENAME,
        shortlist_filename=SHORTLIST_FILENAME,
    )
    CsvJsonAtlasInventoryWriter(
        args.out_dir,
        inventory_filename=INVENTORY_FILENAME,
        shortlist_filename=SHORTLIST_FILENAME,
        manifest_filename=MANIFEST_FILENAME,
    ).write(inventory)

    print(f"wrote {args.out_dir / INVENTORY_FILENAME} ({len(inventory.inventory_rows)} resource rows)")
    print(f"wrote {args.out_dir / SHORTLIST_FILENAME} ({len(inventory.shortlist_rows)} resource rows)")
    print(f"wrote {args.out_dir / MANIFEST_FILENAME} ({inventory.manifest['dataset_count']} datasets)")


def delhi_candidate(dataset: dict[str, Any]) -> bool:
    return city_catalogue_candidate(dataset, "delhi")


def classify_dataset(dataset: dict[str, Any]) -> list[str]:
    return classify_catalogue_dataset(dataset, opencity_atlas_axis_labels)


def enrich_datasets(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return enrich_catalogue_datasets(datasets, opencity_atlas_axis_labels)


def shortlist_flag(dataset: dict[str, Any]) -> bool:
    row = dict(dataset)
    if not row.get("axis_labels"):
        row["axis_labels"] = classify_dataset(dataset)
    return shortlist_dataset(row)


def flatten_inventory_rows(datasets: list[dict[str, Any]]) -> list[dict[str, str]]:
    return flatten_catalogue_inventory_rows(datasets)


if __name__ == "__main__":
    main()
