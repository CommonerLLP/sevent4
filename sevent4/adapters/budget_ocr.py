from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def require_tools(names: list[str]) -> None:
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        sys.exit(f"Missing required command-line tools: {', '.join(missing)}")


class PdfToolchainOcrEngine:
    """Runs the poppler + tesseract command-line toolchain to read and OCR
    budget-PDF pages. A per-engine scratch directory holds rasterized pages."""

    def __init__(self, scratch_dir: str | Path) -> None:
        self.scratch_dir = Path(scratch_dir)

    def page_count(self, pdf: Path) -> int:
        result = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":", 1)[1])
        raise RuntimeError(f"Could not read page count from {pdf}")

    def page_text(self, pdf: Path, page: int) -> str:
        result = subprocess.run(
            ["pdftotext", "-f", str(page), "-l", str(page), str(pdf), "-"],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def ocr_page(self, pdf: Path, page: int, dpi: int, lang: str) -> str:
        scratch = self.scratch_dir
        if scratch.exists():
            shutil.rmtree(scratch)
        scratch.mkdir(parents=True)
        try:
            subprocess.run(
                ["pdftoppm", "-r", str(dpi), "-png", "-f", str(page), "-l", str(page), str(pdf), str(scratch / "page")],
                check=True,
                stderr=subprocess.DEVNULL,
            )
            pngs = sorted(scratch.glob("*.png"))
            if not pngs:
                return ""
            result = subprocess.run(
                ["tesseract", str(pngs[0]), "-", "-l", lang, "--psm", "6"],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.stdout
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
