from __future__ import annotations

from typing import Protocol


class KanpurWardRepository(Protocol):
    def load_source_wards(self) -> dict:
        ...

    def load_heat(self) -> dict:
        ...

    def write_source_wards(self, wards: dict) -> None:
        ...

    def propagate_ward_fields(self, wards: dict) -> None:
        ...

    def propagate_heat_fields(self, wards: dict) -> None:
        ...
