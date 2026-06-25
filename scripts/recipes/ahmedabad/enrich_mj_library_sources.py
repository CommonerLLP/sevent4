#!/usr/bin/env python3
"""Enrich the M.J. Library source archive: fetch the official disclosure PDFs +
content.js, extract text/TSV/OCR, and write the normalized curated CSVs
(documents manifest, service locations, staff establishment, RTI officers,
governance roster, membership requirements, RTI form fields, civic centres).

Thin CLI wrapper: TSV-word column parsing, curated overrides, and the
content.js-driven row builders live in sevent4.domain.mj_library /
sevent4.application.mj_library; curl/pdftotext/pdftoppm/tesseract/CSV IO in the
M.J. Library store adapter.
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.mj_library_filesystem import MjLibraryStore
from sevent4.application.mj_library import enrich_mj_library

REPO = Path(__file__).resolve().parents[3]


def main() -> None:
    enrich_mj_library(MjLibraryStore(REPO))
    print("wrote M.J. Library source-document manifest and normalized source tables")


if __name__ == "__main__":
    main()
