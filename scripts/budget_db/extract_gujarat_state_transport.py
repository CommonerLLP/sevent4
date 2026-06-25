#!/usr/bin/env python3
"""
extract_gujarat_state_transport.py  (v2 — block-aware)
Parse Gujarat STATE budget detailed-demand PDFs for city-transport scheme lines.
Two line shapes are handled:
  (A) single-line schemes:  (N) <desc> <amt> <amt> <amt> <pageref>
  (B) block schemes (wrapped Sub Head): a "... Gross Total | <BE_total>" line whose
      description accumulates from the preceding "Sub Head :" block.
Source: budget-crawler/data/gujarat/finance_dept/<FY>/budget/*_en.pdf
Output: sevent4/data/cities/gujarat/source/budget/gujarat_state_transport.json

Thin CLI wrapper: the line parsing lives in sevent4.domain.gujarat_transport /
sevent4.application.gujarat_transport; pdftotext discovery and JSON IO live in
the gujarat-transport adapter.
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.gujarat_transport_filesystem import (
    BudgetCrawlerDemandSource,
    write_gujarat_transport,
)
from sevent4.application.gujarat_transport import extract_gujarat_transport, summary_lines

# Re-exported so existing importers (tests) keep a stable path.
from sevent4.domain.gujarat_transport import (  # noqa: F401
    extract_rows_from_text,
    gross_total_be_amount,
)

REPO = Path(__file__).resolve().parents[2]
BC = Path(__file__).resolve().parents[3] / "budget-crawler"
OUT_DIR = REPO / "data/cities/gujarat/source/budget"


def main():
    source = BudgetCrawlerDemandSource(BC)
    out = extract_gujarat_transport(source.iter_demand_texts())
    write_gujarat_transport(OUT_DIR, out)
    for line in summary_lines(out):
        print(line)


if __name__ == "__main__":
    main()
