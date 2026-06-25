#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.library_access_filesystem import CsvLibraryLocationRepository, CsvLibrarySummaryWriter
from sevent4.application.library_access import build_city_library_summary
from sevent4.ports.library_access import SUMMARY_FIELDS


REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "data" / "cities" / "ahmedabad" / "source" / "libraries" / "ahmedabad_library_locations.csv"
OUT_DIR = REPO / "data" / "cities" / "ahmedabad" / "derived" / "library_access"


def main() -> None:
    result = build_city_library_summary(_repository(SOURCE).load())
    CsvLibrarySummaryWriter(OUT_DIR / "library_access_summary.csv").write(result)
    print(f"wrote {OUT_DIR / 'library_access_summary.csv'} ({len(result.rows)} rows)")


def summarize_ahmedabad_libraries(source: Path = SOURCE) -> list[dict[str, str]]:
    return build_city_library_summary(_repository(source).load()).rows


def _repository(source: Path) -> CsvLibraryLocationRepository:
    return CsvLibraryLocationRepository(
        source,
        city="ahmedabad",
        source_path=str(source.relative_to(REPO)),
        fixed_library_policy="count_all_as_fixed",
        pending_status="population_origins_required",
        complete_status="population_origins_required",
        notes="Location coverage summary only; population-weighted access waits for population origin grid.",
    )


if __name__ == "__main__":
    main()
