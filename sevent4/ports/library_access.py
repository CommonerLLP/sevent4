from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


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

LIBRARY_COMPARISON_FIELDS = [
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

LIBRARY_SERVICE_DETAIL_FIELDS = [
    "city",
    "library_system",
    "detail_field",
    "locations_with_value",
    "total_locations",
    "status",
    "source_path",
    "notes",
    "request_priority",
]


@dataclass(frozen=True)
class CityLibrarySummaryInput:
    city: str
    source_path: str
    rows: list[dict[str, str]]
    fixed_library_policy: str
    pending_status: str
    complete_status: str
    notes: str


@dataclass(frozen=True)
class CityLibrarySummary:
    rows: list[dict[str, str]]
    fields: list[str]


@dataclass(frozen=True)
class CityLibraryComparisonInput:
    cities: list[str]
    summaries: dict[str, dict[str, str]]


@dataclass(frozen=True)
class CityLibraryComparison:
    rows: list[dict[str, str]]
    fields: list[str]


@dataclass(frozen=True)
class CityLibraryServiceDetailInput:
    city: str
    library_system: str
    total_locations: str
    source_path: str
    values: dict[str, str]


class LibraryLocationRepository(Protocol):
    def load(self) -> CityLibrarySummaryInput:
        ...


class LibrarySummaryWriter(Protocol):
    def write(self, summary: CityLibrarySummary) -> None:
        ...


class LibraryComparisonInputRepository(Protocol):
    def load(self) -> CityLibraryComparisonInput:
        ...


class LibraryComparisonWriter(Protocol):
    def write(self, comparison: CityLibraryComparison) -> None:
        ...
