from __future__ import annotations

from typing import Any

from sevent4.domain.roads import scan_book_pages


def mine_road_spend(book_source, archive) -> tuple[list[dict], dict, list[str]]:
    """Scan every budget book for road code-rows, writing flagged-page dumps via
    the archive port. Returns (code rows, page index, per-book log lines)."""
    rows: list[dict] = []
    page_index: dict[str, Any] = {}
    log_lines: list[str] = []
    for year, pdf_str, page_texts in book_source.iter_books():
        scan = scan_book_pages(year, page_texts)
        rows.extend(scan.rows)
        page_index[year] = {"pdf": pdf_str, **scan.classification}
        for page, text in scan.dump_pages:
            archive.write_dump(year, page, text)
        info = scan.classification
        log_lines.append(
            f"{year}: {info['pages']}p  narrative={len(info['narrative'])} "
            f"ward={len(info['ward-table'])} contractor={len(info['contractor-candidate'])} "
            f"code-rows-pages={len(info['code-table'])}"
        )
    return rows, page_index, log_lines
