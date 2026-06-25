#!/usr/bin/env python3
"""OCR dense budget-summary pages for a city. Thin CLI wrapper: year parsing,
dense-page selection, and token counting live in the budget domain layer; the
poppler/tesseract toolchain and file IO live in the budget adapters.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sevent4.adapters.budget_filesystem import (
    BudgetOcrTextWriter,
    FileBudgetPdfRepository,
    default_ocr_dir,
    default_pdf_dir,
)
from sevent4.adapters.budget_ocr import PdfToolchainOcrEngine, require_tools
from sevent4.application.budget import ocr_budget_pdf
from sevent4.domain.budget import parse_year_from_filename

REPO = Path(__file__).resolve().parents[3]
DEFAULT_CITY = "ahmedabad"
GUJARATI_ENGLISH = "guj+eng"


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR dense budget-summary pages for a city.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Defaults to Ahmedabad.")
    parser.add_argument("--pdf-dir", help="Directory containing budget PDFs.")
    parser.add_argument("--out-dir", help="OCR text output directory.")
    parser.add_argument("--top-pages", type=int, default=16, help="Number of dense numeric pages to OCR per PDF.")
    parser.add_argument("--min-numbers", type=int, default=8, help="Minimum numeric tokens required for a candidate page.")
    parser.add_argument("--dpi", type=int, default=230, help="Rasterization DPI for OCR.")
    parser.add_argument("--lang", default=GUJARATI_ENGLISH, help="Tesseract language string.")
    parser.add_argument("--no-dedupe-year", action="store_true", help="OCR every PDF even if years repeat.")
    args = parser.parse_args()

    require_tools(["pdfinfo", "pdftotext", "pdftoppm", "tesseract"])

    city = args.city.lower()
    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else default_pdf_dir(REPO, city)
    out_dir = Path(args.out_dir) if args.out_dir else default_ocr_dir(REPO, city)
    repository = FileBudgetPdfRepository(pdf_dir)
    if not repository.exists():
        sys.exit(f"No budget PDF directory found: {pdf_dir}")

    pdfs = repository.list_pdfs()
    if not pdfs:
        sys.exit(f"No PDFs found under {pdf_dir}")

    writer = BudgetOcrTextWriter(out_dir)
    writer.init()
    engine = PdfToolchainOcrEngine(writer.scratch_dir)

    seen_years: set[str] = set()
    for pdf in pdfs:
        year = parse_year_from_filename(pdf.name)
        if not year:
            print(f"skip {pdf.name}: no budget year in filename", file=sys.stderr)
            continue
        if not args.no_dedupe_year and year in seen_years:
            print(f"skip {pdf.name}: already OCRed {year}")
            continue
        seen_years.add(year)

        text, page_count, numlines, keep = ocr_budget_pdf(
            engine, pdf, args.top_pages, args.min_numbers, args.dpi, args.lang
        )
        if text is not None:
            writer.write_year_text(year, text)

        line = f"{year}: {numlines} numeric tokens, {page_count} pages, dense_pages={keep}"
        writer.append_progress(line)
        print(line)

    writer.finish()


if __name__ == "__main__":
    main()
