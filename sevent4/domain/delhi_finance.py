"""Pure parsing for Delhi's three civic budgets (GNCTD / MCD / NDMC) into one
comparable finance series. The adapter supplies pdftotext/OCR text + filenames;
these functions own the number parsing, fiscal-year inference, plausibility
floors, per-body row building, and the output meta. No filesystem/subprocess IO.
"""
from __future__ import annotations

import re

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")  # plain or comma-grouped, optional decimal

FIELDS = [
    "body", "fy", "scope", "total_receipts_cr", "total_income_cr", "total_expenditure_cr",
    "own_tax_revenue_cr", "property_tax_cr", "govt_grants_cr", "estimate", "unit",
]


def nums(line: str) -> list[float]:
    out = []
    for tok in NUM.findall(line):
        try:
            out.append(float(tok.replace(",", "")))
        except ValueError:
            pass
    return out


def fy_from_name(name: str) -> str:
    be = re.search(r"(?<!R)BE[_ ]?(?:20)?(\d{2})-(\d{2})", name)
    if be:
        return f"20{be.group(1)}-{be.group(2)}"
    yrs = re.findall(r"(20\d{2})-(\d{2})", name)
    return f"{yrs[0][0]}-{yrs[0][1]}" if yrs else ""


def last_total(text: str, *patterns: str) -> float | None:
    """Rightmost numeric on the last line matching any pattern (latest BE column)."""
    val = None
    for ln in text.splitlines():
        if any(p in ln.lower() for p in patterns):
            n = nums(ln)
            if n:
                val = n[-1]
    return val


def plausible(cr: float | None, floor: float) -> float | None:
    return cr if (cr is not None and abs(cr) >= floor) else None


def gnctd_row(text: str, name: str, ocr: bool, overlay: dict, rel_pdf: str) -> dict | None:
    if "glance" not in name.lower():
        return None
    fy = fy_from_name(name)
    rec_total = plausible(last_total(text, "total receipts (") or last_total(text, "total receipts"), 5000)
    exp_total = plausible(last_total(text, "total expenditure (") or last_total(text, "total expenditure"), 5000)
    own_tax = plausible(last_total(text, "own tax revenue"), 1000)
    if rec_total and exp_total and not (0.6 <= exp_total / rec_total <= 1.7):
        exp_total = None
    if exp_total and rec_total and not (0.6 <= rec_total / exp_total <= 1.7):
        rec_total = None
    vision = fy in overlay
    if vision:
        exp_total = overlay[fy].get("exp", exp_total)
        rec_total = overlay[fy].get("rec", rec_total)
    if not (rec_total or exp_total):
        return None
    return {"body": "GNCTD", "body_full": "Government of NCT of Delhi", "fy": fy,
            "total_receipts_cr": rec_total, "total_expenditure_cr": exp_total,
            "own_tax_revenue_cr": own_tax, "unit": "INR_crore",
            "estimate": "latest BE column in Budget-at-a-Glance",
            "ocr_sourced": ocr and not vision, "vision_verified": vision,
            "source_pdf": rel_pdf, "scope": "whole NCT (territorial govt)"}


def parse_gnctd_rows(docs, overlay: dict) -> list[dict]:
    """docs = iterable of (text, name, ocr, rel_pdf)."""
    rows = []
    for text, name, ocr, rel_pdf in docs:
        row = gnctd_row(text, name, ocr, overlay, rel_pdf)
        if row:
            rows.append(row)
    return rows


def parse_mcd_rows(docs) -> list[dict]:
    """docs = iterable of (text, name, rel_pdf), already sorted."""
    by_fy: dict[str, dict] = {}
    for text, name, rel_pdf in docs:
        fy = fy_from_name(name)
        if not fy:
            continue
        south = "south" in name.lower() or "sdmc" in name.lower()
        r = by_fy.setdefault(fy, {"body": "MCD", "body_full": "Municipal Corporation of Delhi", "fy": fy,
                                  "unit": "INR_crore", "estimate": "latest BE column", "source_pdfs": [],
                                  "scope": ""})
        r["source_pdfs"].append(rel_pdf)
        r["scope"] = "South MCD only (trifurcation era)" if south else "unified MCD"
        gt = last_total(text, "grand total")
        ptax = last_total(text, "property tax")
        grants = last_total(text, "contribution from govt. grants", "govt. grants")
        gt_cr = plausible(round(gt / 100, 1) if gt else None, 500)
        ptax_cr = plausible(round(ptax / 100, 1) if ptax else None, 30)
        grants_cr = plausible(round(grants / 100, 1) if grants else None, 10)
        if "income" in name.lower() or "receipt" in name.lower():
            if gt_cr:
                r["total_income_cr"] = gt_cr
            if ptax_cr:
                r["property_tax_cr"] = ptax_cr
            if grants_cr:
                r["govt_grants_cr"] = grants_cr
        elif "expenditure" in name.lower():
            if gt_cr:
                r["total_expenditure_cr"] = gt_cr
        else:
            if gt_cr:
                r["total_income_cr"] = gt_cr
            if ptax_cr:
                r["property_tax_cr"] = ptax_cr
    return [by_fy[k] for k in sorted(by_fy)]


def ndmc_row(text: str, rel_pdf: str) -> dict:
    return {"body": "NDMC", "body_full": "New Delhi Municipal Council", "fy": "2025-26",
            "total_receipts_cr": last_total(text, "total receipt"),
            "total_expenditure_cr": last_total(text, "total expenditure"),
            "unit": "INR_crore", "estimate": "FY25-26 BE", "council": "nominated (no elected member)",
            "source_pdf": rel_pdf, "scope": "New Delhi enclave (~42.7 km², ~258k residents)"}


def finance_meta(rows: list[dict]) -> dict:
    return {
        "city": "delhi", "generated": "2026-06-20",
        "what": "Headline budget totals for Delhi's three civic bodies (GNCTD / MCD / NDMC), to show the municipal-finance fragmentation.",
        "caveats": [
            "Units normalised to INR crore (GNCTD/NDMC native crore; MCD native lakh ÷100).",
            "MCD pre-2022 rows are SOUTH MCD only (the corporation was trifurcated 2012-2022; unified 2022). Scope flagged per row — do NOT sum across the discontinuity.",
            "Headline value = the latest Budget-Estimate column in each document; mixed Actuals/RE/BE bases across docs. Estimate basis recorded per row.",
            "27 of 102 source PDFs were scanned and OCR'd (older GNCTD) by tesseract. The GNCTD years with OCR digit-drops/misses (2008-09, 2009-10, 2014-15, 2015-16, 2017-18, 2018-19) were re-read by a visual review pass and corrected (vision_verified:true; values in gnctd_vision_verified.json); other tesseract years (ocr_sourced:true) were validated against vision spot-checks but not each individually.",
        ],
        "rows": rows,
    }
