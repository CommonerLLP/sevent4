from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Mapping, Sequence


class FileBudgetOcrRepository:
    """Loads OCR text files (one per budget year) for the parse step."""

    def __init__(self, ocr_dir: str | Path) -> None:
        self.ocr_dir = Path(ocr_dir)

    def exists(self) -> bool:
        return self.ocr_dir.exists()

    def load_ocr_texts(self) -> list[tuple[str, list[str]]]:
        texts: list[tuple[str, list[str]]] = []
        for path in sorted(self.ocr_dir.glob("*.txt")):
            if path.name.startswith("_"):
                continue
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            texts.append((path.stem, lines))
        return texts


class FileBudgetCsvWriter:
    def __init__(self, out_path: str | Path) -> None:
        self.out_path = Path(out_path)

    def write_rows(self, columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> None:
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        with self.out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(columns))
            writer.writeheader()
            writer.writerows(rows)


class FinanceBookArchive:
    """Holds the output paths for a fetched finance-book kind and writes the PDFs
    plus the JSON manifest."""

    def __init__(self, repo_root: str | Path, pdf_dir: str | Path, manifest_path: str | Path) -> None:
        self.repo_root = Path(repo_root)
        self.pdf_dir = Path(pdf_dir)
        self.manifest_path = Path(manifest_path)

    def ensure_dirs(self) -> None:
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def pdf_path(self, filename: str) -> Path:
        return self.pdf_dir / filename

    def relpath(self, path: Path) -> str:
        return str(Path(path).relative_to(self.repo_root))

    def write_pdf(self, path: Path, data: bytes) -> None:
        Path(path).write_bytes(data)

    def write_manifest(self, document: Mapping[str, object]) -> None:
        self.manifest_path.write_text(json.dumps(document, indent=2), encoding="utf-8")


class FileBudgetPdfRepository:
    """Lists budget PDFs for the OCR step."""

    def __init__(self, pdf_dir: str | Path) -> None:
        self.pdf_dir = Path(pdf_dir)

    def exists(self) -> bool:
        return self.pdf_dir.exists()

    def list_pdfs(self) -> list[Path]:
        return sorted(self.pdf_dir.glob("*.pdf"))


class BudgetOcrTextWriter:
    """Writes per-year OCR text and a running progress log for the OCR step."""

    def __init__(self, out_dir: str | Path) -> None:
        self.out_dir = Path(out_dir)
        self.progress = self.out_dir / "_progress.txt"

    @property
    def scratch_dir(self) -> Path:
        return self.out_dir / "_scratch_pages"

    def init(self) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.progress.write_text("", encoding="utf-8")

    def write_year_text(self, year: str, text: str) -> None:
        (self.out_dir / f"{year}.txt").write_text(text, encoding="utf-8")

    def append_progress(self, line: str) -> None:
        with self.progress.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def finish(self) -> None:
        self.append_progress("DONE")


def finance_paths(repo_root: str | Path, city: str, source_dir: str) -> tuple[Path, Path]:
    base = Path(repo_root) / "data" / "cities" / city / "source" / source_dir
    return base / "pdfs", base / f"{source_dir}_sources.json"


def default_ocr_dir(repo_root: str | Path, city: str) -> Path:
    return Path(repo_root) / "data" / "cities" / city / "source" / "budget" / "ocr_capex_opex"


def default_budget_csv(repo_root: str | Path, city: str) -> Path:
    return Path(repo_root) / "data" / "cities" / city / "layers" / "budget_capex_opex.csv"


def default_pdf_dir(repo_root: str | Path, city: str) -> Path:
    return Path(repo_root) / "data" / "cities" / city / "source" / "budget" / "pdfs"
