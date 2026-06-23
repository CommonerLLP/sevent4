from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class CityConsoleCity(Protocol):
    id: str
    name: str
    layers_dir: Path


class CityConsoleLayerSpec(Protocol):
    file: str
    bounds_file: str | None


class CityConsoleManifest(Protocol):
    layers: tuple[CityConsoleLayerSpec, ...]


@dataclass(frozen=True)
class CityConsoleInput:
    city: CityConsoleCity
    manifest: CityConsoleManifest


class CityConsoleInputRepository(Protocol):
    def load(self) -> CityConsoleInput:
        ...


class CityConsoleRenderer(Protocol):
    def __call__(self, city: CityConsoleCity, manifest: CityConsoleManifest, output_dir: Path) -> str:
        ...


class PublicPageRepository(Protocol):
    def page_ids(self) -> set[str]:
        ...

    def links_for_page(self, page_id: str) -> list[str]:
        ...


class CityConsolePublicSurface(Protocol):
    @property
    def output_dir(self) -> Path:
        ...

    def prepare(self) -> None:
        ...

    def publish_layers(self, city: CityConsoleCity, manifest: CityConsoleManifest) -> None:
        ...

    def write_index(self, html: str) -> None:
        ...
