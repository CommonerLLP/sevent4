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
