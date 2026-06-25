from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from sevent4.domain.roads import CODE_ROW_FIELDS, BUDGET_BOOK_FILES


class AmcBudgetBookRepository:
    """Resolves AMC budget-book PDFs across the local source archives (plus the
    AMC_PDF_DIRS env override) and reads their page text via pypdf."""

    def __init__(self, repo_root: str | Path, env_var: str = "AMC_PDF_DIRS") -> None:
        root = Path(repo_root)
        self.pdf_dirs = [
            root / "data/cities/ahmedabad/source/budget/amc_pdfs",
            root / "data/sources/budget/amc_pdfs",
            root / "data/raw/budget",
        ]
        self.pdf_dirs += [
            Path(d).expanduser()
            for d in os.environ.get(env_var, "").split(os.pathsep)
            if d.strip()
        ]

    def _resolve(self, name: str) -> Path:
        for directory in self.pdf_dirs:
            candidate = directory / name
            if candidate.exists():
                return candidate
        return self.pdf_dirs[0] / name

    def iter_books(self) -> Iterator[tuple[str, str, Sequence[str]]]:
        import sys

        from pypdf import PdfReader

        for year, filename in BUDGET_BOOK_FILES.items():
            path = self._resolve(filename)
            if not path.exists():
                print(f"!! missing {path}", file=sys.stderr)
                continue
            reader = PdfReader(str(path))
            page_texts = [(page.extract_text() or "") for page in reader.pages]
            yield year, str(path), page_texts


class RoadSpendArchive:
    def __init__(self, out_dir: str | Path) -> None:
        self.out_dir = Path(out_dir)
        self.dumps_dir = self.out_dir / "dumps"

    @property
    def code_rows_path(self) -> Path:
        return self.out_dir / "code_rows_raw.csv"

    def write_code_rows(self, rows: Sequence[Mapping[str, Any]]) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        with open(self.code_rows_path, "w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CODE_ROW_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def write_page_index(self, index: Mapping[str, Any]) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "page_index.json").write_text(json.dumps(index, indent=2))

    def write_dump(self, year: str, page: int, text: str) -> None:
        book_dump = self.dumps_dir / year
        book_dump.mkdir(parents=True, exist_ok=True)
        (book_dump / f"p{page:03d}.txt").write_text(text)
