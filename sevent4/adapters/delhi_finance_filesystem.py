from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path


class DelhiFinanceSource:
    """pdftotext (with OCR-sidecar fallback) over Delhi's GNCTD/MCD/NDMC budget PDFs."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.budget = self.root / "data/cities/delhi/source/budget"
        self.ocr = self.root / "data/cities/delhi/derived/finance/_ocr_text"

    def _text_of(self, pdf: Path) -> str:
        try:
            t = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                               capture_output=True, text=True, timeout=120).stdout
        except Exception:
            t = ""
        if len(t.replace(" ", "").strip()) > 1000:
            return t
        sidecar = self.ocr / (str(pdf.relative_to(self.budget)).replace("/", "__")[:-4] + ".txt")
        return sidecar.read_text(encoding="utf-8", errors="ignore") if sidecar.exists() else t

    def _is_ocr(self, pdf: Path) -> bool:
        try:
            t = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                               capture_output=True, text=True, timeout=120).stdout
        except Exception:
            return True
        return len(t.replace(" ", "").strip()) <= 1000

    def _rel(self, pdf: Path) -> str:
        return str(pdf.relative_to(self.root))

    def vision_overlay(self) -> dict:
        p = self.budget / "gnctd_vision_verified.json"
        return json.loads(p.read_text(encoding="utf-8")).get("verified", {}) if p.exists() else {}

    def gnctd_docs(self):
        for pdf in sorted((self.budget / "gnctd").rglob("*.pdf")):
            yield self._text_of(pdf), pdf.name, self._is_ocr(pdf), self._rel(pdf)

    def mcd_docs(self):
        for pdf in sorted((self.budget / "mcd").rglob("*.pdf")):
            yield self._text_of(pdf), pdf.name, self._rel(pdf)

    def ndmc_doc(self):
        glance = next((self.budget / "ndmc").rglob("*Glance*"), None) or next((self.budget / "ndmc").rglob("*lance*.pdf"), None)
        if glance:
            return self._text_of(glance), self._rel(glance)
        return None


def write_json(obj, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def write_finance_csv(rows, path: Path, fields: list[str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
