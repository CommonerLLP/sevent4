from __future__ import annotations

from typing import Protocol


class RepresentativeManifestWriter(Protocol):
    def write_manifest(self, document: dict) -> None:
        ...


class CouncillorRowWriter(Protocol):
    def write_rows(self, rows: list[dict[str, str]]) -> None:
        ...


class OfficerWriter(Protocol):
    def write_officers(self, city: str, officers: list[dict[str, str]]) -> None:
        ...


class WardRepresentativeLayerWriter(Protocol):
    def write_document(self, document: dict) -> None:
        ...
