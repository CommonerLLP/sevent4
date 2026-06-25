from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


GtfsRow = dict[str, str]


@dataclass(frozen=True)
class GtfsCorridorInput:
    stops: list[GtfsRow]
    routes: list[GtfsRow]
    trips: list[GtfsRow]
    shapes: list[GtfsRow]
    stop_times: list[GtfsRow]


class GtfsCorridorInputRepository(Protocol):
    def load(self) -> GtfsCorridorInput:
        ...


class GtfsCorridorWriter(Protocol):
    def write_geojson(self, document: dict) -> None:
        ...
