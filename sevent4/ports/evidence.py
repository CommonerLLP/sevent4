from __future__ import annotations

from typing import Any, Mapping, Protocol

from sevent4.domain.evidence import EvidenceBundle


class EvidenceBundleRepository(Protocol):
    def load(self) -> EvidenceBundle:
        ...


class PollutionBoardCapacityRepository(Protocol):
    def list_capacity_records(self) -> Mapping[str, Mapping[str, Any]]:
        ...


class PublicJsonDocumentWriter(Protocol):
    def write_json(self, document: Mapping[str, Any]) -> None:
        ...

