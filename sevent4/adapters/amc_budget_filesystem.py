from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import subprocess
from pathlib import Path

from sevent4.domain.amc_budget import BUDGET_LINE_COLS, SOURCE_DOCS, source_pdf_fiscal_year


class AmcBudgetRepository:
    """Reads the verified budget inputs, the clean-year PDF text, and builds the
    canonical SQLite store plus the DuckDB/parquet/CSV/JSON/xlsx exports."""

    def __init__(self, repo_root: str | Path, env_var: str = "AMC_PDF_DIRS") -> None:
        root = Path(repo_root)
        self.src = root / "data/cities/ahmedabad/source/budget"
        self.db = root / "data/cities/ahmedabad/db"
        self.schema = root / "scripts/budget_db/schema.sql"
        self.pdf_dirs = [
            root / "data/cities/ahmedabad/source/budget/amc_pdfs",
            root / "data/sources/budget/amc_pdfs",
        ]
        self.pdf_dirs += [
            Path(d).expanduser() for d in os.environ.get(env_var, "").split(os.pathsep) if d.strip()
        ]

    def find_pdf(self, name: str) -> str | None:
        for directory in self.pdf_dirs:
            candidate = directory / name
            if candidate.exists():
                return str(candidate)
        return None

    def read_inputs(self):
        civic = json.loads((self.src / "amc_civic_lines.json").read_text())
        ie = json.loads((self.src / "amts_income_expenditure.json").read_text())
        with (self.src / "amc_budget_22yr.csv").open() as handle:
            csv_rows = list(csv.DictReader(handle))
        return civic, ie, csv_rows

    def grant_texts(self):
        for fy, ed, _sk, ex, fn in SOURCE_DOCS:
            if ex == "text" and ed == "english":
                p = self.find_pdf(fn)
                if not p:
                    continue
                try:
                    txt = subprocess.run(
                        ["pdftotext", "-layout", p, "-"], capture_output=True, text=True, timeout=120
                    ).stdout
                except Exception:
                    continue
                yield fy, os.path.basename(p), txt

    def _pdf_pages(self, path: str) -> int | None:
        try:
            info = subprocess.run(["pdfinfo", path], capture_output=True, text=True, timeout=20).stdout
            mm = re.search(r"Pages:\s+(\d+)", info)
            return int(mm.group(1)) if mm else None
        except Exception:
            return None

    def build_database(self, rows: list[dict]) -> dict:
        self.db.mkdir(parents=True, exist_ok=True)
        sqlite_path = self.db / "amc_budget.sqlite"
        if sqlite_path.exists():
            sqlite_path.unlink()
        con = sqlite3.connect(sqlite_path)
        con.executescript(self.schema.read_text())

        for fy, ed, sk, ex, fn in SOURCE_DOCS:
            p = self.find_pdf(fn)
            pages = self._pdf_pages(p) if p else None
            con.execute(
                "INSERT OR REPLACE INTO source_doc(source_pdf,city,fiscal_year,edition,"
                "script_kind,extractability,pages,abs_path) VALUES(?,?,?,?,?,?,?,?)",
                (fn, "ahmedabad", fy, ed, sk, ex, pages, p),
            )
        known = {fn for _fy, _ed, _sk, _ex, fn in SOURCE_DOCS}
        for spdf in sorted({r["source_pdf"] for r in rows if r.get("source_pdf")} - known):
            con.execute(
                "INSERT OR IGNORE INTO source_doc(source_pdf,city,fiscal_year,edition,"
                "script_kind,extractability,abs_path,note) VALUES(?,?,?,?,?,?,?,?)",
                (spdf, "ahmedabad", source_pdf_fiscal_year(spdf), "english", "english", "text",
                 self.find_pdf(spdf), "auto-registered from referenced data"),
            )
        con.executemany(
            f"INSERT INTO budget_line({','.join(BUDGET_LINE_COLS)}) "
            f"VALUES({','.join('?' * len(BUDGET_LINE_COLS))})",
            [[r.get(c) for c in BUDGET_LINE_COLS] for r in rows],
        )
        con.commit()

        import pandas as pd

        bl = pd.read_sql("SELECT * FROM budget_line", con)
        sd = pd.read_sql("SELECT * FROM source_doc", con)
        ets = pd.read_sql("SELECT * FROM v_entity_timeseries", con)
        cov = pd.read_sql("SELECT * FROM v_coverage", con)

        bl.to_csv(self.db / "budget_line.csv", index=False)
        bl.to_parquet(self.db / "budget_line.parquet", index=False)
        json.dump(
            {"source_doc": sd.to_dict("records"), "budget_line": bl.to_dict("records")},
            open(self.db / "amc_budget.json", "w"), indent=1, ensure_ascii=False,
        )

        import duckdb

        dpath = self.db / "amc_budget.duckdb"
        if dpath.exists():
            dpath.unlink()
        dk = duckdb.connect(str(dpath))
        dk.execute("CREATE TABLE budget_line AS SELECT * FROM read_parquet(?)", [str(self.db / "budget_line.parquet")])
        dk.register("sd_df", sd)
        dk.execute("CREATE TABLE source_doc AS SELECT * FROM sd_df")
        dk.close()

        xlsx_ok, xlsx_err = True, None
        try:
            with pd.ExcelWriter(self.db / "amc_budget.xlsx", engine="openpyxl") as xl:
                bl.to_excel(xl, sheet_name="budget_line", index=False)
                ets.to_excel(xl, sheet_name="entity_timeseries", index=False)
                cov.to_excel(xl, sheet_name="coverage", index=False)
                sd.to_excel(xl, sheet_name="source_doc", index=False)
                xl.book.active = 0
        except Exception as e:
            xlsx_ok, xlsx_err = False, f"{type(e).__name__}: {e}"
        con.close()

        return {
            "sqlite_path": sqlite_path,
            "n_budget_lines": len(bl),
            "n_source_docs": len(sd),
            "n_pdf_on_disk": int(sd["abs_path"].notna().sum()),
            "xlsx_ok": xlsx_ok,
            "xlsx_err": xlsx_err,
        }
