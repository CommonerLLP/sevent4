from __future__ import annotations

from typing import Protocol


class CityBuildInputRepository(Protocol):
    def load(self):
        ...


class CityBuildArtifactWriter(Protocol):
    def write(self, artifacts) -> None:
        ...
