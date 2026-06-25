#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.library_access_filesystem import CsvLibraryLocationRepository, CsvLibrarySummaryWriter
from sevent4.application.library_access import build_city_library_summary
from sevent4.ports.library_access import SUMMARY_FIELDS


REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "data" / "cities" / "delhi" / "source" / "libraries" / "dpl_library_locations.csv"
OUT_DIR = REPO / "data" / "cities" / "delhi" / "derived" / "library_access"


def main() -> None:
    result = build_city_library_summary(_repository(SOURCE).load())
    CsvLibrarySummaryWriter(OUT_DIR / "library_access_summary.csv").write(result)
    print(f"wrote {OUT_DIR / 'library_access_summary.csv'} ({len(result.rows)} rows)")


def summarize_delhi_libraries(source: Path = SOURCE) -> list[dict[str, str]]:
    return build_city_library_summary(_repository(source).load()).rows


def _repository(source: Path) -> CsvLibraryLocationRepository:
    return CsvLibraryLocationRepository(
        source,
        city="delhi",
        source_path=str(source.relative_to(REPO)),
        fixed_library_policy="exclude_mobile_service_points",
        pending_status="geocoding_required",
        complete_status="ready_for_population_origins",
        notes="DPL-published addresses parsed; access routing waits for geocoding and population origin grid.",
    )


if __name__ == "__main__":
    main()
