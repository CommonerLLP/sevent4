#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]

# Ahmedabad is the first city budget OCR recipe. Other cities can reuse the OCR
# runner once their PDFs are placed under data/cities/<city>/source/budget/pdfs.
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

    _require_tools(["pdfinfo", "pdftotext", "pdftoppm", "tesseract"])

    city = args.city.lower()
    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else REPO / "data" / "cities" / city / "source" / "budget" / "pdfs"
    out_dir = Path(args.out_dir) if args.out_dir else REPO / "data" / "cities" / city / "source" / "budget" / "ocr_capex_opex"
    if not pdf_dir.exists():
        sys.exit(f"No budget PDF directory found: {pdf_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    progress = out_dir / "_progress.txt"
    progress.write_text("", encoding="utf-8")

    seen_years: set[str] = set()
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs found under {pdf_dir}")

    for pdf in pdfs:
        year = parse_year(pdf.name)
        if not year:
            print(f"skip {pdf.name}: no budget year in filename", file=sys.stderr)
            continue
        if not args.no_dedupe_year and year in seen_years:
            print(f"skip {pdf.name}: already OCRed {year}")
            continue
        seen_years.add(year)
        numlines, page_count, pages = ocr_pdf(
            pdf=pdf,
            year=year,
            out_dir=out_dir,
            top_pages=args.top_pages,
            min_numbers=args.min_numbers,
            dpi=args.dpi,
            lang=args.lang,
        )
        line = f"{year}: {numlines} numeric tokens, {page_count} pages, dense_pages={pages}"
        with progress.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        print(line)

    with progress.open("a", encoding="utf-8") as handle:
        handle.write("DONE\n")


def ocr_pdf(
    *,
    pdf: Path,
    year: str,
    out_dir: Path,
    top_pages: int,
    min_numbers: int,
    dpi: int,
    lang: str,
) -> tuple[int, int, list[int]]:
    keep, page_count = dense_pages(pdf, top_pages=top_pages, min_numbers=min_numbers)
    if not keep:
        return 0, page_count, []

    scratch = out_dir / "_scratch_pages"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)

    out_txt = out_dir / f"{year}.txt"
    try:
        with out_txt.open("w", encoding="utf-8") as handle:
            for page in keep:
                png_prefix = scratch / "page"
                subprocess.run(
                    ["pdftoppm", "-r", str(dpi), "-png", "-f", str(page), "-l", str(page), str(pdf), str(png_prefix)],
                    check=True,
                    stderr=subprocess.DEVNULL,
                )
                pngs = sorted(scratch.glob("*.png"))
                if not pngs:
                    continue
                png = pngs[0]
                result = subprocess.run(
                    ["tesseract", str(png), "-", "-l", lang, "--psm", "6"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                handle.write(f"=== page {page} ===\n{result.stdout}\n")
                png.unlink()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    text = out_txt.read_text(encoding="utf-8", errors="ignore")
    numlines = len(re.findall(r"[0-9૦-૯]{3,}", text))
    return numlines, page_count, keep


def dense_pages(pdf: Path, *, top_pages: int, min_numbers: int) -> tuple[list[int], int]:
    page_count = pdf_pages(pdf)
    scored: list[tuple[int, int]] = []
    for page in range(1, page_count + 1):
        result = subprocess.run(
            ["pdftotext", "-f", str(page), "-l", str(page), str(pdf), "-"],
            check=False,
            capture_output=True,
            text=True,
        )
        scored.append((page, len(re.findall(r"\d{3,}", result.stdout))))
    scored.sort(key=lambda item: item[1], reverse=True)
    keep = sorted(page for page, count in scored[:top_pages] if count >= min_numbers)
    return keep, page_count


def pdf_pages(pdf: Path) -> int:
    result = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1])
    raise RuntimeError(f"Could not read page count from {pdf}")


def parse_year(filename: str) -> str | None:
    match = re.search(r"(20\d{2})[-_ ](\d{2})", filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    match = re.search(r"\b(\d{2})[-_](\d{2})\b", filename)
    if match:
        return f"20{match.group(1)}-{match.group(2)}"
    return None


def _require_tools(names: list[str]) -> None:
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        sys.exit(f"Missing required command-line tools: {', '.join(missing)}")


if __name__ == "__main__":
    main()
