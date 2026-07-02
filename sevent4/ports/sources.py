from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class SourcesCity(Protocol):
    id: str
    name: str
    source_dir: Path


@dataclass(frozen=True)
class SourcesInput:
    city: SourcesCity
    compiled: str
    entries: list[dict[str, Any]]


class SourcesInputRepository(Protocol):
    def load(self) -> SourcesInput:
        ...


class SourcesHtmlWriter(Protocol):
    def write_html(self, html: str) -> None:
        ...


class SourcesJsonWriter(Protocol):
    def write_json(self, payload: dict[str, Any]) -> None:
        ...


class SourcesRenderer(Protocol):
    def __call__(
        self,
        city: SourcesCity,
        compiled: str,
        entries: list[dict[str, Any]],
    ) -> str:
        ...
