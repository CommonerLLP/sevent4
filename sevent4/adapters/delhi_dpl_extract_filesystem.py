"""Filesystem adapter for Delhi Public Library extraction."""
from __future__ import annotations

import csv
from pathlib import Path

from sevent4.domain.delhi_dpl_extract import (
    annual_row_from_text,
    assign_location_ids,
    parse_dpl_mobile_points_from_html,
    parse_dpl_zone_locations,
)

REPO = Path(__file__).resolve().parents[2]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def build_manifest_rows(source_dir: Path, manifest: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in manifest:
        local_path = Path(row["local_path"].removeprefix("targeted/"))
        local = Path(source_dir) / local_path
        valid_pdf = ""
        if local.exists() and local.suffix.lower() == ".pdf":
            valid_pdf = "1" if local.read_bytes()[:5] == b"%PDF-" else "0"
        rows.append(
            {
                "kind": row["kind"],
                "text": row["text"],
                "url": row["url"],
                "local_path": row["local_path"],
                "status": row["status"],
                "bytes": row["bytes"],
                "sha256": row["sha256"],
                "valid_pdf": valid_pdf,
                "repo_storage": "manifest_only",
                "notes": "Raw targeted source artifact retained outside git under /private/tmp unless promoted separately.",
            }
        )
    return rows


def extract_dpl_locations(html_dir: Path, source_by_stem: dict[str, str] | None = None) -> list[dict[str, str]]:
    source_by_stem = source_by_stem or {}
    rows: list[dict[str, str]] = []
    html_dir = Path(html_dir)
    for path in sorted(html_dir.glob("operations__*_zone.html")):
        page_html = path.read_text(encoding="utf-8", errors="ignore")
        rows.extend(
            parse_dpl_zone_locations(
                path.name,
                zone_from_path(path),
                page_html,
                source_by_stem.get(path.stem, ""),
            )
        )

    mobile_path = html_dir / "operations__schedule_and_points_of_mobile_van.html"
    if mobile_path.exists():
        rows.extend(
            parse_dpl_mobile_points_from_html(
                mobile_path.name,
                mobile_path.read_text(encoding="utf-8", errors="ignore"),
                source_by_stem.get(mobile_path.stem, ""),
            )
        )
    return assign_location_ids(rows)


def extract_annual_rows(text_dir: Path, source_by_stem: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(Path(text_dir).glob("annual__*.txt")):
        if "account" in path.name.lower():
            continue
        row = annual_row_from_text(
            path.name,
            source_by_stem.get(path.stem, ""),
            path.read_text(encoding="utf-8", errors="ignore"),
        )
        if row is not None:
            rows.append(row)
    return sorted(rows, key=lambda row: row["year"])


def primary_delhi_population() -> int:
    path = REPO / "data" / "cities" / "delhi" / "source" / "demographics" / "delhi_population_denominators.csv"
    if not path.exists():
        return 19_000_000
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["role"] == "primary_service_area_denominator":
                return int(row["population"])
    return 19_000_000


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def zone_from_path(path: Path) -> str:
    return Path(path).stem.removeprefix("operations__").removesuffix("_zone").replace("_", " ")
