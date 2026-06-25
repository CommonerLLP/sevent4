from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from sevent4.domain.evidence import SourceProfile


@dataclass(frozen=True)
class SourceArtifact:
    source_profile_id: str
    local_path: Path
    sha256: str | None = None
    media_type: str | None = None


class SourceAcquisitionPort(Protocol):
    def acquire(self, profile: SourceProfile) -> SourceArtifact:
        ...


class DocumentExtractionPort(Protocol):
    def extract_text(self, artifact: SourceArtifact) -> str:
        ...


@dataclass(frozen=True)
class OpenDataCatalogueInput:
    source_catalogue: str
    datasets: list[dict[str, Any]]


@dataclass(frozen=True)
class AtlasSourceInventory:
    inventory_rows: list[dict[str, str]]
    shortlist_rows: list[dict[str, str]]
    manifest: dict[str, Any]


class OpenDataCatalogueRepository(Protocol):
    def load(self) -> OpenDataCatalogueInput:
        ...


class AtlasSourceInventoryWriter(Protocol):
    def write(self, inventory: AtlasSourceInventory) -> None:
        ...


@dataclass(frozen=True)
class SourceDocument:
    government: str
    document_type: str
    fiscal_year: str | None
    title: str
    url: str
    source_page: str
    local_path: str | None = None
    sha256: str | None = None
    status: str = "discovered"
