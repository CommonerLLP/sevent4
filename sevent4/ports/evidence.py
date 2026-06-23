from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Mapping, Protocol

from sevent4.domain.evidence import EvidenceBundle
from sevent4.domain.pollution import PollutionBoardCapacityRecord


class EvidenceBundleRepository(Protocol):
    def load(self) -> EvidenceBundle:
        ...


class PollutionBoardCapacityRepository(Protocol):
    def list_capacity_records(self) -> Sequence[PollutionBoardCapacityRecord]:
        ...


class PublicJsonDocumentWriter(Protocol):
    def write_json(self, document: Mapping[str, Any]) -> None:
        ...
