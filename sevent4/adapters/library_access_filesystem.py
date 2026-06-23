from __future__ import annotations

import csv
from pathlib import Path

from sevent4.ports.library_access import CityLibraryComparison, CityLibraryComparisonInput, CityLibrarySummary, CityLibrarySummaryInput


class CsvLibraryLocationRepository:
    def __init__(
        self,
        path: Path | str,
        *,
        city: str,
        source_path: str,
        fixed_library_policy: str,
        pending_status: str,
        complete_status: str,
        notes: str,
    ) -> None:
        self.path = Path(path)
        self.city = city
        self.source_path = source_path
        self.fixed_library_policy = fixed_library_policy
        self.pending_status = pending_status
        self.complete_status = complete_status
        self.notes = notes

    def load(self) -> CityLibrarySummaryInput:
        return CityLibrarySummaryInput(
            city=self.city,
            source_path=self.source_path,
            rows=read_csv(self.path),
            fixed_library_policy=self.fixed_library_policy,
            pending_status=self.pending_status,
            complete_status=self.complete_status,
            notes=self.notes,
        )


class CsvLibrarySummaryWriter:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def write(self, summary: CityLibrarySummary) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_csv(self.path, summary.rows, summary.fields)


class FileLibraryComparisonInputRepository:
    def __init__(self, cities_root: Path | str, cities: list[str]) -> None:
        self.cities_root = Path(cities_root)
        self.cities = cities

    def load(self) -> CityLibraryComparisonInput:
        summaries: dict[str, dict[str, str]] = {}
        for city in self.cities:
            path = self.cities_root / city / "derived" / "library_access" / "library_access_summary.csv"
            if not path.exists():
                continue
            rows = read_csv(path)
            if rows:
                summaries[city] = rows[0]
        return CityLibraryComparisonInput(cities=self.cities, summaries=summaries)


class CsvLibraryComparisonWriter:
    def __init__(self, out_dir: Path | str) -> None:
        self.out_dir = Path(out_dir)

    def write(self, comparison: CityLibraryComparison) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        write_csv(self.out_dir / "library_access_summary.csv", comparison.rows, comparison.fields)
        for row in comparison.rows:
            write_csv(self.out_dir / f"{row['pair']}_access_comparison.csv", [row], comparison.fields)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
