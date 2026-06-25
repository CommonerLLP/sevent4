from __future__ import annotations

from typing import Any, Protocol


class RbiPdfTextSource(Protocol):
    """Reads a -layout pdftotext rendering of an RBI report PDF + its hash."""

    def text(self, pdf) -> str:
        ...

    def sha256(self, pdf) -> str:
        ...


class RbiHtmlTableSource(Protocol):
    """Reads the HTML tables of an RBI PublicationsView page + the file hash."""

    def read_tables(self, path) -> list:
        ...

    def sha256(self, path) -> str:
        ...


class RbiReportWriter(Protocol):
    def write(self, out_path, result: dict[str, Any]) -> None:
        ...
