from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class OfficialsCity(Protocol):
    name: str
    layers_dir: Path


@dataclass(frozen=True)
class OfficialsInput:
    city: OfficialsCity
    as_of: str
    attribution: str
    records: list[dict[str, Any]]


class OfficialsInputRepository(Protocol):
    def load(self) -> OfficialsInput:
        ...


class HtmlDocumentWriter(Protocol):
    def write_html(self, html: str) -> None:
        ...


class OfficialsRenderer(Protocol):
    def __call__(
        self,
        city: OfficialsCity,
        as_of: str,
        attribution: str,
        records: list[dict[str, Any]],
    ) -> str:
        ...
