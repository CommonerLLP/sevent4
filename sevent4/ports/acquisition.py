from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

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

