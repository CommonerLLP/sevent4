#!/usr/bin/env python3
"""Parse selected RBI 2022 municipal-finance HTML tables.

The full RBI 2022 PDF URL is published on the official RBI page, but direct
asset downloads can return anti-automation HTML in this environment. The RBI
PublicationsView HTML pages contain the same chapter and appendix tables. This
parser uses those HTML tables structurally and fails if expected rows are absent.
Thin CLI wrapper: the table parsing lives in sevent4.application.rbi_finance /
sevent4.domain.rbi_finance; pandas HTML reads, hashing, and JSON IO live in the
RBI finance adapter.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from sevent4.adapters.rbi_finance_filesystem import PandasRbiHtmlSource, write_rbi_report
from sevent4.application.rbi_finance import build_rbi_2022_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter2-html", type=Path, required=True)
    parser.add_argument("--appendix-revenue-html", type=Path, required=True)
    parser.add_argument("--publication-page-html", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    source = PandasRbiHtmlSource()
    source_files = {
        "chapter2_html": {"path": str(args.chapter2_html), "sha256": source.sha256(args.chapter2_html)},
        "appendix_revenue_delhi_html": {
            "path": str(args.appendix_revenue_html),
            "sha256": source.sha256(args.appendix_revenue_html),
        },
    }
    if args.publication_page_html is not None:
        source_files["publication_page_html"] = {
            "path": str(args.publication_page_html),
            "sha256": source.sha256(args.publication_page_html),
        }

    result = build_rbi_2022_report(
        source.read_tables(args.chapter2_html),
        source.read_tables(args.appendix_revenue_html),
        source_files,
    )
    write_rbi_report(args.out, result)


if __name__ == "__main__":
    main()
