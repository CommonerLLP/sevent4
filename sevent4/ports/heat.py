from __future__ import annotations

from typing import Any, Callable, Mapping, Protocol

import numpy as np


class HeatSceneSource(Protocol):
    """Produces the median summer land-surface-temperature grid for a city from
    an upstream scene archive (e.g. the Planetary Computer STAC API)."""

    def median_grid(self, bbox, datetime: str, cloud_cover: float):
        ...


class WardHeatRepository(Protocol):
    """Loads ward polygons and yields a per-geometry raster sampler bound to a
    city's heat raster."""

    def load_wards(self) -> Mapping[str, Any]:
        ...

    def open_sampler(self) -> tuple[Callable[[Any], "np.ndarray | None"], "float | None"]:
        ...


class HeatArtifactWriter(Protocol):
    def write_raster_artifacts(self, artifacts) -> None:
        ...

    def write_ward_heat(self, document: Mapping[str, Any]) -> None:
        ...


class ManifestStore(Protocol):
    def has_heat_outputs(self) -> bool:
        ...

    def load_manifest(self) -> Mapping[str, Any]:
        ...

    def write_manifest(self, manifest: Mapping[str, Any]) -> None:
        ...
