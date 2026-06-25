#!/usr/bin/env python3
"""Parse selected RBI Report on Municipal Finances tables from pdftotext output.

The parser is deliberately narrow: it extracts only the table rows that the
The Unelected City research note relies on. It uses fixed table titles and row
labels from the RBI PDF, so layout changes surface as missing rows instead of
silent guesses. Thin CLI wrapper: the table parsing lives in
sevent4.domain.rbi_finance / sevent4.application.rbi_finance; pdftotext, hashing,
and JSON IO live in the RBI finance adapter.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from sevent4.adapters.rbi_finance_filesystem import PdftotextRbiSource, write_rbi_report
from sevent4.application.rbi_finance import build_rbi_2024_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    source = PdftotextRbiSource()
    result = build_rbi_2024_report(source.text(args.pdf), str(args.pdf), source.sha256(args.pdf))
    write_rbi_report(args.out, result)


if __name__ == "__main__":
    main()
