from __future__ import annotations

from typing import Any, Iterator, Mapping, Protocol, Sequence


class AmcBudgetBookSource(Protocol):
    """Yields (year, pdf_path_str, page_texts) for each budget book present on
    disk; warns about missing books."""

    def iter_books(self) -> Iterator[tuple[str, str, Sequence[str]]]:
        ...


class RoadSpendArchive(Protocol):
    def write_code_rows(self, rows: Sequence[Mapping[str, Any]]) -> None:
        ...

    def write_page_index(self, index: Mapping[str, Any]) -> None:
        ...

    def write_dump(self, year: str, page: int, text: str) -> None:
        ...
