from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class OverlapCrosswalkInput:
    city: str
    state: str
    records: tuple[Mapping[str, Any], ...]
    thresholds: Mapping[str, float]
    excluded_acs: tuple[str, ...] = ()


class RepresentativePointJurisdictionRepository(Protocol):
    def load_representative_point_records(self, city: str) -> tuple[Mapping[str, Any], ...]:
        ...


class OverlapJurisdictionRepository(Protocol):
    def load_overlap_crosswalk_input(self, city: str) -> OverlapCrosswalkInput:
        ...


class JurisdictionCrosswalkWriter(Protocol):
    def write_crosswalk(self, city: str, document: Mapping[str, Any]) -> Any:
        ...
