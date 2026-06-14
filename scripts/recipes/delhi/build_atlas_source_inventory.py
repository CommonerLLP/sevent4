#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.recipes.scope_opencity_for_atlas import classify as classify_for_atlas

DEFAULT_CATALOGUE = REPO / "data" / "sources" / "opencity" / "_catalogue" / "opencity_catalogue.json"
DEFAULT_OUT_DIR = REPO / "data" / "cities" / "delhi" / "source" / "opencity"
STRUCTURED_FORMATS = {"CSV", "GEOJSON", "KML", "KMZ", "XLSX", "XLS", "JSON", "SHP", "ZIP"}
SHORTLIST_AXES = {"base", "decides", "pays", "function"}
SHORTLIST_TERMS = (
    "budget",
    "ward",
    "boundary",
    "map",
    "statistical handbook",
    "birth",
    "death",
    "transport",
    "bus",
    "metro",
    "vehicle",
    "road",
    "crash",
    "master plan",
    "building bye",
    "air quality",
    "library",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Delhi OpenCity source inventory for the municipality atlas.")
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))
    datasets = enrich_datasets([dataset for dataset in catalogue["datasets"] if delhi_candidate(dataset)])
    inventory_rows = flatten_inventory_rows(datasets)
    shortlist_rows = [row for row in inventory_rows if row["shortlist"] == "1"]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "delhi_opencity_inventory.csv", inventory_rows, INVENTORY_FIELDS)
    write_csv(args.out_dir / "delhi_opencity_atlas_shortlist.csv", shortlist_rows, INVENTORY_FIELDS)
    write_json(
        args.out_dir / "delhi_opencity_manifest.json",
        {
            "source_catalogue": str(args.catalogue.relative_to(REPO) if args.catalogue.is_relative_to(REPO) else args.catalogue),
            "dataset_count": len(datasets),
            "resource_row_count": len(inventory_rows),
            "shortlist_resource_row_count": len(shortlist_rows),
            "outputs": {
                "inventory_csv": "delhi_opencity_inventory.csv",
                "shortlist_csv": "delhi_opencity_atlas_shortlist.csv",
            },
            "notes": (
                "Inventory only. Resource downloads/promotions must preserve publisher, OpenCity URL, "
                "resource URL, checksum, rights text where available, and atlas-axis labels."
            ),
        },
    )

    print(f"wrote {args.out_dir / 'delhi_opencity_inventory.csv'} ({len(inventory_rows)} resource rows)")
    print(f"wrote {args.out_dir / 'delhi_opencity_atlas_shortlist.csv'} ({len(shortlist_rows)} resource rows)")
    print(f"wrote {args.out_dir / 'delhi_opencity_manifest.json'} ({len(datasets)} datasets)")


def delhi_candidate(dataset: dict[str, Any]) -> bool:
    groups = [str(group).lower() for group in dataset.get("groups", [])]
    if "delhi" in groups:
        return True
    if groups:
        return False
    haystack = f"{dataset.get('name', '')} {dataset.get('title', '')}".lower()
    return "delhi" in haystack


def classify_dataset(dataset: dict[str, Any]) -> list[str]:
    return sorted(classify_for_atlas(dataset))


def enrich_datasets(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for dataset in datasets:
        row = dict(dataset)
        row["axis_labels"] = classify_dataset(dataset)
        row["shortlist"] = shortlist_flag(row)
        enriched.append(row)
    return sorted(enriched, key=lambda item: (not item["shortlist"], item.get("title") or item.get("name") or ""))


def shortlist_flag(dataset: dict[str, Any]) -> bool:
    axes = set(dataset.get("axis_labels") or classify_dataset(dataset))
    title = f"{dataset.get('title', '')} {dataset.get('name', '')}".lower()
    has_structured = any(
        str(resource.get("format", "")).upper() in STRUCTURED_FORMATS for resource in dataset.get("resources", [])
    )
    if axes & {"base", "decides", "pays"}:
        return True
    if has_structured and axes & SHORTLIST_AXES:
        return True
    return any(term in title for term in SHORTLIST_TERMS)


def flatten_inventory_rows(datasets: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for dataset in datasets:
        resources = dataset.get("resources") or [{}]
        for resource in resources:
            rows.append(
                {
                    "dataset_name": str(dataset.get("name") or ""),
                    "dataset_title": str(dataset.get("title") or ""),
                    "opencity_url": str(dataset.get("url") or ""),
                    "organization": str(dataset.get("organization") or ""),
                    "groups": ";".join(str(group) for group in dataset.get("groups", [])),
                    "tags": ";".join(str(tag) for tag in dataset.get("tags", [])),
                    "metadata_modified": str(dataset.get("metadata_modified") or ""),
                    "axis_labels": ";".join(dataset.get("axis_labels") or []),
                    "shortlist": "1" if dataset.get("shortlist") else "0",
                    "resource_id": str(resource.get("id") or ""),
                    "resource_name": str(resource.get("name") or ""),
                    "resource_format": str(resource.get("format") or ""),
                    "resource_url": str(resource.get("url") or ""),
                    "resource_size_bytes": str(resource.get("size_bytes") or ""),
                    "resource_last_modified": str(resource.get("last_modified") or ""),
                    "resource_mimetype": str(resource.get("mimetype") or ""),
                    "download_status": "not_downloaded",
                    "local_path": "",
                    "sha256": "",
                    "notes": "OpenCity catalogue inventory row; resource not promoted into city source tree yet.",
                }
            )
    return rows


INVENTORY_FIELDS = [
    "dataset_name",
    "dataset_title",
    "opencity_url",
    "organization",
    "groups",
    "tags",
    "metadata_modified",
    "axis_labels",
    "shortlist",
    "resource_id",
    "resource_name",
    "resource_format",
    "resource_url",
    "resource_size_bytes",
    "resource_last_modified",
    "resource_mimetype",
    "download_status",
    "local_path",
    "sha256",
    "notes",
]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
