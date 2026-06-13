#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "data" / "cities" / "ahmedabad" / "source" / "libraries" / "ahmedabad_library_locations.csv"
OUT_DIR = REPO / "data" / "cities" / "ahmedabad" / "derived" / "library_access"
SUMMARY_FIELDS = [
    "city",
    "source_path",
    "library_locations",
    "fixed_library_locations",
    "mobile_service_points",
    "coordinate_verified_locations",
    "coordinate_pending_locations",
    "coordinate_coverage_pct",
    "coordinate_coverage_status",
    "routing_tier",
    "access_status",
    "confidence",
    "notes",
]


def main() -> None:
    rows = summarize_ahmedabad_libraries()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_DIR / "library_access_summary.csv", rows, SUMMARY_FIELDS)
    print(f"wrote {OUT_DIR / 'library_access_summary.csv'} ({len(rows)} rows)")


def summarize_ahmedabad_libraries(source: Path = SOURCE) -> list[dict[str, str]]:
    rows = read_csv(source)
    total = len(rows)
    verified = sum(1 for row in rows if row.get("latitude") and row.get("longitude"))
    pending = total - verified
    coverage = verified / total * 100 if total else 0.0
    return [
        {
            "city": "ahmedabad",
            "source_path": str(source.relative_to(REPO)),
            "library_locations": str(total),
            "fixed_library_locations": str(total),
            "mobile_service_points": "0",
            "coordinate_verified_locations": str(verified),
            "coordinate_pending_locations": str(pending),
            "coordinate_coverage_pct": f"{coverage:.1f}",
            "coordinate_coverage_status": "complete" if pending == 0 else "partial",
            "routing_tier": "not_computed",
            "access_status": "population_origins_required",
            "confidence": "high" if pending == 0 else "medium",
            "notes": "Location coverage summary only; population-weighted access waits for population origin grid.",
        }
    ]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
