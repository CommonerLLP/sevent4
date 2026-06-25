#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.library_access_filesystem import CsvLibraryComparisonWriter, FileLibraryComparisonInputRepository
from sevent4.application.library_access import build_library_access_comparison, library_pair_key
from sevent4.ports.library_access import CityLibraryComparisonInput, LIBRARY_COMPARISON_FIELDS


REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "data" / "comparators" / "library_access"
CITIES = ["ahmedabad", "delhi", "toronto"]
FIELDS = LIBRARY_COMPARISON_FIELDS


def main() -> None:
    result = build_library_access_comparison(
        FileLibraryComparisonInputRepository(REPO / "data" / "cities", CITIES).load()
    )
    CsvLibraryComparisonWriter(OUT_DIR).write(result)
    print(f"wrote {OUT_DIR / 'library_access_summary.csv'} ({len(result.rows)} rows)")


def pair_key(city_a: str, city_b: str) -> str:
    return library_pair_key(city_a, city_b)


def comparison_rows(cities: list[str], summaries: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    return build_library_access_comparison(CityLibraryComparisonInput(cities=cities, summaries=summaries)).rows


def load_city_summaries(cities: list[str]) -> dict[str, dict[str, str]]:
    return FileLibraryComparisonInputRepository(REPO / "data" / "cities", cities).load().summaries


if __name__ == "__main__":
    main()
