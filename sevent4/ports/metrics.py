from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import geopandas as gpd


@dataclass(frozen=True)
class WardServiceAccessInput:
    wards: gpd.GeoDataFrame
    crs_metric: str
    service_points: dict[str, gpd.GeoDataFrame]
    builtup: gpd.GeoDataFrame | None
    population: gpd.GeoDataFrame | None


class WardServiceAccessInputRepository(Protocol):
    def load(self) -> WardServiceAccessInput:
        ...


class WardServiceAccessWriter(Protocol):
    def write_rows(self, rows: list[dict]) -> None:
        ...


@dataclass(frozen=True)
class WardTransitFrequencyInput:
    wards: dict
    gtfs_routes: list[dict[str, str]]
    gtfs_trips: list[dict[str, str]]
    gtfs_stops: list[dict[str, str]]
    gtfs_stop_times: list[dict[str, str]]
    buffer_m: float


class WardTransitFrequencyInputRepository(Protocol):
    def load(self) -> WardTransitFrequencyInput:
        ...


class WardTransitFrequencyWriter(Protocol):
    def write_wards(self, document: dict) -> None:
        ...


@dataclass(frozen=True)
class ServiceAccessCompositeInput:
    wards: dict
    acs: dict
    crosswalk_records: list[dict]


class ServiceAccessCompositeInputRepository(Protocol):
    def load(self) -> ServiceAccessCompositeInput:
        ...


class ServiceAccessCompositeWriter(Protocol):
    def write_documents(self, wards: dict, acs: dict) -> None:
        ...
