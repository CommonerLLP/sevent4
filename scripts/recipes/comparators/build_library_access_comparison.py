#!/usr/bin/env python3
from __future__ import annotations

import csv
from itertools import combinations
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "data" / "comparators" / "library_access"
CITIES = ["ahmedabad", "delhi", "toronto"]
FIELDS = [
    "pair",
    "comparison_status",
    "city_a",
    "city_b",
    "city_a_library_locations",
    "city_b_library_locations",
    "city_a_access_status",
    "city_b_access_status",
    "notes",
]


def main() -> None:
    summaries = load_city_summaries(CITIES)
    rows = comparison_rows(CITIES, summaries)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_DIR / "library_access_summary.csv", rows, FIELDS)
    for row in rows:
        write_csv(OUT_DIR / f"{row['pair']}_access_comparison.csv", [row], FIELDS)
    print(f"wrote {OUT_DIR / 'library_access_summary.csv'} ({len(rows)} rows)")


def pair_key(city_a: str, city_b: str) -> str:
    return "_".join(sorted([city_a, city_b]))


def comparison_rows(cities: list[str], summaries: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for city_a, city_b in combinations(cities, 2):
        summary_a = summaries.get(city_a)
        summary_b = summaries.get(city_b)
        status = "available" if summary_a and summary_b else "missing_city_summary"
        rows.append(
            {
                "pair": pair_key(city_a, city_b),
                "comparison_status": status,
                "city_a": city_a,
                "city_b": city_b,
                "city_a_library_locations": (summary_a or {}).get("library_locations", ""),
                "city_b_library_locations": (summary_b or {}).get("library_locations", ""),
                "city_a_access_status": (summary_a or {}).get("access_status", ""),
                "city_b_access_status": (summary_b or {}).get("access_status", ""),
                "notes": comparison_notes(city_a, city_b, summary_a, summary_b),
            }
        )
    return rows


def comparison_notes(
    city_a: str,
    city_b: str,
    summary_a: dict[str, str] | None,
    summary_b: dict[str, str] | None,
) -> str:
    missing = [city for city, summary in [(city_a, summary_a), (city_b, summary_b)] if summary is None]
    if missing:
        return f"Missing library access summary for: {', '.join(missing)}."
    statuses = {summary_a.get("access_status", ""), summary_b.get("access_status", "")}
    if statuses - {"ready_for_population_origins"}:
        return "Location coverage comparison only; population-weighted travel-time comparison is not ready."
    return "Both city summaries are ready for population-origin travel-time modelling."


def load_city_summaries(cities: list[str]) -> dict[str, dict[str, str]]:
    summaries: dict[str, dict[str, str]] = {}
    for city in cities:
        path = REPO / "data" / "cities" / city / "derived" / "library_access" / "library_access_summary.csv"
        if not path.exists():
            continue
        rows = read_csv(path)
        if rows:
            summaries[city] = rows[0]
    return summaries


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
