from __future__ import annotations

from pathlib import Path
from typing import Protocol


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

    def publish_layers(self, city, manifest) -> None:
        ...

    def write_index(self, html: str) -> None:
        ...
