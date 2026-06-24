from __future__ import annotations

from html.parser import HTMLParser
from typing import Mapping, Sequence
from urllib.parse import urljoin

from sevent4.domain.budget import (
    FinanceBookLink,
    budget_columns,
    budget_row,
    count_ascii_numbers,
    count_numeric_tokens,
    finance_book_filename,
    finance_link_year,
    parse_ocr_lines,
    select_dense_pages,
)


class _FinanceBookHTMLParser(HTMLParser):
    """Collects anchor (label, url) pairs that look like finance-book PDFs."""

    def __init__(self, page_url: str, keywords: tuple[str, ...]) -> None:
        super().__init__()
        self.page_url = page_url
        self.keywords = keywords
        self._href: str | None = None
        self._text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "a" or not self._href:
            return
        label = " ".join("".join(self._text).split())
        href = self._href
        haystack = f"{label} {href}".lower()
        if any(keyword in haystack for keyword in self.keywords) and (".pdf" in haystack or "viewfile" in haystack):
            self.links.append((label, urljoin(self.page_url, href)))
        self._href = None
        self._text = []


def discover_finance_links(
    html: str, kind: str, page_url: str, keywords: tuple[str, ...]
) -> list[FinanceBookLink]:
    """Parse a finance index page into deduped, year-tagged finance-book links."""
    parser = _FinanceBookHTMLParser(page_url, keywords)
    parser.feed(html)
    links: list[FinanceBookLink] = []
    seen: set[tuple[str, str]] = set()
    for label, url in parser.links:
        year = finance_link_year(label, url)
        if not year:
            continue
        key = (year, url)
        if key in seen:
            continue
        seen.add(key)
        links.append(FinanceBookLink(kind=kind, year=year, label=label or f"{kind} {year}", url=url))
    return sorted(links, key=lambda item: item.year, reverse=True)


def finance_row(city: str, kind: str, link: FinanceBookLink, path_rel: str) -> dict[str, str]:
    return {
        "city": city,
        "kind": kind,
        "year": link.year,
        "label": link.label,
        "url": link.url,
        "path": path_rel,
    }


def finance_manifest(city: str, kind: str, page_url: str, rows: Sequence[Mapping[str, str]]) -> dict:
    return {"city": city, "kind": kind, "source_page": page_url, "items": list(rows)}


def budget_book_filename(city: str, link: FinanceBookLink, seen: set[str]) -> str:
    return finance_book_filename(city, link, seen)


def ocr_budget_pdf(
    engine, pdf, top_pages: int, min_numbers: int, dpi: int, lang: str
) -> tuple[str | None, int, int, list[int]]:
    """OCR one budget PDF via the OCR engine port: score every page, keep the
    densest numeric pages, and OCR them. Returns (text-or-None, page_count,
    numeric-token-count, kept-pages). Text is None when no page is dense enough."""
    page_count = engine.page_count(pdf)
    scored = [(page, count_ascii_numbers(engine.page_text(pdf, page))) for page in range(1, page_count + 1)]
    keep = select_dense_pages(scored, top_pages, min_numbers)
    if not keep:
        return None, page_count, 0, []
    text = "".join(
        f"=== page {page} ===\n{engine.ocr_page(pdf, page, dpi, lang)}\n" for page in keep
    )
    return text, page_count, count_numeric_tokens(text), keep


def parse_budget_ocr(
    ocr_texts: Sequence[tuple[str, Sequence[str]]], labels: Mapping[str, str]
) -> tuple[list[str], list[dict[str, str]], list[tuple[str, list[str]]]]:
    """Turn (year, lines) OCR inputs into (columns, rows, found-labels-per-year)."""
    columns = budget_columns(labels)
    rows: list[dict[str, str]] = []
    found_per_year: list[tuple[str, list[str]]] = []
    for year, lines in ocr_texts:
        record = parse_ocr_lines(lines, labels)
        rows.append(budget_row(year, record, labels))
        found_per_year.append((year, [key for key in labels if key in record]))
    return columns, rows, found_per_year
