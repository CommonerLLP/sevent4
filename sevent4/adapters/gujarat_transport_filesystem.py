from __future__ import annotations

import json
import subprocess
from pathlib import Path

from sevent4.domain.gujarat_transport import DEMAND_GLOBS, YEARS


class BudgetCrawlerDemandSource:
    """Yields (fiscal_year, pdf_name, pdftotext) for each Gujarat detailed-demand
    PDF found in the sibling budget-crawler checkout."""

    def __init__(self, bc_root: str | Path) -> None:
        self.bc_root = Path(bc_root)

    def iter_demand_texts(self):
        for fy in YEARS:
            bdir = self.bc_root / "data/gujarat/finance_dept" / fy / "budget"
            if not bdir.exists():
                continue
            pdfs = []
            for glob in DEMAND_GLOBS:
                pdfs += list(bdir.glob(glob))
            for pdf in sorted(set(pdfs)):
                try:
                    txt = subprocess.run(
                        ["pdftotext", "-layout", str(pdf), "-"],
                        capture_output=True, text=True, timeout=200,
                    ).stdout
                except Exception:
                    continue
                yield fy, pdf.name, txt


def write_gujarat_transport(out_dir: str | Path, out: dict) -> None:
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "gujarat_state_transport.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False)
    )
