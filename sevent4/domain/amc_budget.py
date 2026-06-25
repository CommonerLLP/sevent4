"""Pure row-building for the canonical AMC municipal-budget database.

Four loaders turn verified in-repo inputs (civic_lines.json, AMTS income/
expenditure, the 22-year headline CSV) plus best-effort narrative-grant text into
normalised `budget_line` rows, with provenance on every figure. No filesystem,
subprocess, or DB IO lives here — the adapter loads inputs and writes the stores.
"""
from __future__ import annotations

import re

BUDGET_LINE_COLS = [
    "city", "fiscal_year", "fy_start", "estimate_basis", "section", "flow", "head_category",
    "head_name", "head_name_raw", "entity", "amount_cr", "amount_raw", "source_pdf", "page",
    "extraction_method", "confidence", "note",
]

SOURCE_DOCS = [  # (fy, edition, script_kind, extractability, file-glob)
    ("2005-06", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2005-06.pdf"),
    ("2006-07", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2006-07.pdf"),
    ("2007-08", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2007-08.pdf"),
    ("2008-09", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2008-09.pdf"),
    ("2009-10", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2009-10.pdf"),
    ("2010-11", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2010-11.pdf"),
    ("2011-12", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2011-12.pdf"),
    ("2012-13", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2012-13.pdf"),
    ("2013-14", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2013-14.pdf"),
    ("2014-15", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2014-15.pdf"),
    ("2015-16", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2015-16.pdf"),
    ("2016-17", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2016-17.pdf"),
    ("2017-18", "gujarati", "gujarati_legacy", "ocr_needed", "AMCbudget_2017-18.pdf"),
    ("2018-19", "english", "english", "text", "AMC_Budget_2018-19_English9026.pdf"),
    ("2019-20", "english", "english", "text", "AMC_Budget_2019-20_English9594.pdf"),
    ("2021-22", "english", "english", "text", "amc_budget_2021-22.pdf"),
    ("2022-23", "english", "english", "text", "AMC_Budget_2022-23_English2679.pdf"),
    ("2023-24", "english", "english", "text", "AMC_Budget_2023-24_English (1)6444.pdf"),
    ("2024-25", "gujarati", "gujarati_legacy", "ocr_needed", "amc_budget_2024-25.pdf"),
    ("2025-26", "gujarati", "gujarati_legacy", "ocr_needed", "amc_budget_2025-26.pdf"),
    ("2026-27", "gujarati", "gujarati_unicode", "text", "amc_budget_2026-27.pdf"),
]

LINE_MAP = {  # civic_lines 'line' -> (entity, head_category, head_name, section, flow)
    "AMTS": ("AMTS", "department_support", "Loan/support to AMTS (city bus)", "capital", "expenditure"),
    "ajl_brts": ("AJL_BRTS", "department_support", "Support to Ahmedabad Janmarg Ltd (BRTS)", "capital", "expenditure"),
    "library_mj": ("MJ_LIBRARY", "grant_contribution", "Grant to Sheth M.J. Library", "revenue", "expenditure"),
    "library_branch_total": ("LIBRARY_BRANCHES", "grant_contribution", "Grant to branch libraries", "revenue", "expenditure"),
    "vs_hospital": ("VS_HOSPITAL", "grant_contribution", "Grant to V.S. Hospital", "revenue", "expenditure"),
    "riverfront_srfdcl": ("SRFDCL", "capital_works", "Sabarmati Riverfront (SRFDCL)", "capital", "expenditure"),
    "school_board": ("SCHOOL_BOARD", "grant_contribution", "Grant to Municipal School Board", "revenue", "expenditure"),
    "parks_gardens": ("PARKS", "maintenance", "Parks & gardens", "revenue", "expenditure"),
}

GRANT_RE = re.compile(
    r"Grant (?:to|for)\s+([A-Z][A-Za-z .,&'-]{3,60}?)\s+Rs\.?\s*([\d,]+\.?\d*)\s*crore", re.I
)


def fy_start(fy):
    return int(fy.split("-")[0])


class BudgetLineBuilder:
    """Accumulates budget_line rows, deduping on the full identity
    (city, year, basis, entity, head) — the first loader to write a head wins."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.seen: set = set()

    def add(self, fy, basis, section, flow, cat, name, amount, *, entity=None, raw=None,
            pdf=None, page=None, method="text", conf="medium", note=None) -> bool:
        key = ("ahmedabad", fy, basis, entity or "", name)
        if key in self.seen:  # first loader (most authoritative) wins
            return False
        self.seen.add(key)
        self.rows.append(dict(
            city="ahmedabad", fiscal_year=fy, fy_start=fy_start(fy),
            estimate_basis=basis, section=section, flow=flow, head_category=cat,
            head_name=name, head_name_raw=raw, entity=entity,
            amount_cr=(round(float(amount), 4) if amount is not None else None),
            amount_raw=raw, source_pdf=pdf, page=page,
            extraction_method=method, confidence=conf, note=note,
        ))
        return True


def load_civic_lines(b: BudgetLineBuilder, cv: dict) -> None:
    """LOADER 1 — civic_lines.json (verified, detailed, most authoritative)."""
    for r in cv["data"]:
        ent, cat, name, sec, flow = LINE_MAP.get(r["line"], (None, "other_expenditure", r["line"], None, None))
        ah = (r.get("account_head") or "").lower()
        basis = "actual" if ("actual" in ah or "spend" in ah) else ("RE" if "revised" in ah else "BE")
        b.add(r["year"], basis, sec, flow, cat, name, r.get("amount_cr"),
              entity=ent, raw=r.get("raw"), pdf=r.get("source_pdf"), page=r.get("page"),
              method="manual_verified", conf=r.get("confidence", "high"), note=r.get("exact_line"))


def load_amts_income_expenditure(b: BudgetLineBuilder, ie: dict) -> None:
    """LOADER 2 — amts_income_expenditure.json (AMTS internal I&E)."""
    for y in ie["amts_income_expenditure"]:
        fy = y["year"]
        src = y.get("source")
        for k, v in y.get("income_components_cr", {}).items():
            if isinstance(v, (int, float)):
                b.add(fy, "BE", "revenue", "income", "non_tax_revenue",
                      f"AMTS income — {k.replace('_', ' ')}", v, entity="AMTS",
                      raw=str(v), pdf=None, method="text", conf="medium", note=src)
        for k, v in y.get("expenditure_components_cr", {}).items():
            if isinstance(v, (int, float)):
                b.add(fy, "BE", "revenue", "expenditure", "establishment",
                      f"AMTS expenditure — {k.replace('_', ' ')}", v, entity="AMTS",
                      raw=str(v), pdf=None, method="text", conf="medium", note=src)
        for k, lbl, cat, flow, sec in [
            ("income_total_cr", "AMTS total income", "non_tax_revenue", "income", "revenue"),
            ("total_budget_cr", "AMTS total budget", "department_support", "expenditure", "revenue"),
            ("amc_loan_to_amts_cr", "AMC deficit-loan to AMTS", "department_support", "expenditure", "capital"),
            ("accumulated_debt_cr", "AMTS accumulated debt", "loan_charges", "expenditure", "capital"),
        ]:
            if isinstance(y.get(k), (int, float)):
                b.add(fy, "BE", sec, flow, cat, lbl, y[k], entity="AMTS", raw=str(y[k]),
                      method="text", conf="medium", note=src)

    ax = ie.get("audited_cumulative_cross_check", {})
    for k, lbl, ent in [
        ("amts_cumulative_amc_subsidy_loans_cr", "AMTS cumulative AMC subsidy-loans", "AMTS"),
        ("ajl_brts_capex_loan_cr", "AJL BRTS capex loan (cumulative)", "AJL_BRTS"),
        ("ajl_brts_operating_gap_loan_cr", "AJL operating-gap loan (cumulative)", "AJL_BRTS"),
    ]:
        if isinstance(ax.get(k), (int, float)):
            b.add("2023-24", "actual", "capital", "expenditure", "loan_charges", lbl, ax[k],
                  entity=ent, raw=str(ax[k]), method="manual_verified", conf="high", note=ax.get("source"))


def load_budget_22yr_csv(b: BudgetLineBuilder, csv_rows) -> None:
    """LOADER 3 — amc_budget_22yr.csv (headline lines; fills gaps L1 lacks)."""
    def num(x):
        x = (x or "").strip()
        return float(x) if x else None

    for r in csv_rows:
        fy = r["year"]
        conf = r.get("confidence", "medium")
        pg = r.get("amts_page") or None
        pg = int(pg) if (pg and str(pg).isdigit()) else None
        if num(r.get("amts_cr")) is not None:
            b.add(fy, "BE", "capital", "expenditure", "department_support", "Loan/support to AMTS (city bus)",
                  num(r["amts_cr"]), entity="AMTS", raw=r.get("notes"), page=pg,
                  method="manual_verified", conf=conf, note=r.get("notes"))
        if num(r.get("mj_library_cr")) is not None:
            b.add(fy, "BE", "revenue", "expenditure", "grant_contribution", "Grant to Sheth M.J. Library",
                  num(r["mj_library_cr"]), entity="MJ_LIBRARY", method="manual_verified", conf=conf)
        if num(r.get("property_tax_cr")) is not None:
            b.add(fy, "BE", "revenue", "income", "tax_revenue", "Property tax (general tax)",
                  num(r["property_tax_cr"]), raw=r.get("property_tax_basis"),
                  method="manual_verified", conf=conf, note=r.get("property_tax_basis"))
        if num(r.get("riverfront_cr")) is not None:
            b.add(fy, "BE", "capital", "expenditure", "capital_works", "Sabarmati Riverfront (SRFDCL)",
                  num(r["riverfront_cr"]), entity="SRFDCL", method="manual_verified", conf=conf)
        if num(r.get("total_cr")) is not None:
            b.add(fy, "BE", "revenue", None, "total", "Total revenue budget",
                  num(r["total_cr"]), method="manual_verified", conf=conf)


def load_grant_text(b: BudgetLineBuilder, fy: str, txt: str, pdf_name: str) -> int:
    """LOADER 4 — best-effort narrative grant lines from clean-year PDF text."""
    extracted = 0
    for m in GRANT_RE.finditer(txt):
        name = re.sub(r"\s+", " ", m.group(1)).strip(" .,")
        amt = float(m.group(2).replace(",", ""))
        if amt > 100000:  # guard against mis-parses (lakh/typo)
            continue
        ok = b.add(fy, "BE", "revenue", "expenditure", "grant_contribution", f"Grant to {name}", amt,
                   raw=m.group(0), pdf=pdf_name, method="text", conf="low",
                   note="auto-extracted narrative grant line (low confidence; HITL verify)")
        if ok:
            extracted += 1
    return extracted


def source_pdf_fiscal_year(spdf: str) -> str | None:
    yrm = re.search(r"(20\d\d)[-_](\d\d)", spdf)
    return f"{yrm.group(1)}-{yrm.group(2)}" if yrm else None
