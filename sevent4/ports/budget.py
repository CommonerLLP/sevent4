from __future__ import annotations

from typing import Mapping, Protocol, Sequence


class FinanceBookSource(Protocol):
    """Fetches finance-book index HTML and PDF bytes from a public municipal
    source (direct HTTP with a curl fallback)."""

    def fetch_text(self, url: str) -> str:
        ...

    def fetch_bytes(self, url: str) -> bytes:
        ...


class OcrEngine(Protocol):
    """Runs the local PDF/OCR toolchain (pdfinfo/pdftotext/pdftoppm/tesseract)."""

    def page_count(self, pdf) -> int:
        ...

    def page_text(self, pdf, page: int) -> str:
        ...

    def ocr_page(self, pdf, page: int, dpi: int, lang: str) -> str:
        ...


class BudgetOcrRepository(Protocol):
    def load_ocr_texts(self) -> Sequence[tuple[str, Sequence[str]]]:
        ...


class BudgetCsvWriter(Protocol):
    def write_rows(self, columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> None:
        ...
