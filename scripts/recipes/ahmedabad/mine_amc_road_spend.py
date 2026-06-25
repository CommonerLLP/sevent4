#!/usr/bin/env python3
"""Comb all AMC budget books (2005-06 -> 2026-27) for road-spend evidence.

Reads budget PDFs from local-only source archives. Set AMC_PDF_DIRS to one or
more colon-separated directories when the PDFs are stored outside this repo.

Outputs into data/cities/ahmedabad/source/budget/roads/:
  code_rows_raw.csv   - every code-table line matching the road vocabulary,
                        with year, source pdf, page, raw line (no column
                        interpretation here; that happens downstream with
                        per-era column maps)
  page_index.json     - per book: pages classified as narrative / ward-table /
                        contractor-candidate / code-table, for manual reading
  dumps/<book>/pNNN.txt - extracted text of every flagged page

Rule Zero: this script never interprets a figure; it only locates and
preserves raw text with page cites. Thin CLI wrapper: page classification and
code-row extraction live in sevent4.domain.roads; PDF/CSV/JSON IO in the roads
adapters.
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.roads_filesystem import AmcBudgetBookRepository, RoadSpendArchive
from sevent4.application.roads import mine_road_spend

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/cities/ahmedabad/source/budget/roads"


def main():
    source = AmcBudgetBookRepository(ROOT)
    archive = RoadSpendArchive(OUT)
    rows, page_index, log_lines = mine_road_spend(source, archive)
    for line in log_lines:
        print(line)
    archive.write_code_rows(rows)
    archive.write_page_index(page_index)
    print(f"\n{len(rows)} code rows -> {archive.code_rows_path}")


if __name__ == "__main__":
    main()
