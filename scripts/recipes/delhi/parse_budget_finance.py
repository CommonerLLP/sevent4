#!/usr/bin/env python3
"""Parse Delhi's three civic budgets into one comparable finance series.

Delhi's "unelected city" story is a money-fragmentation story: most of the city's
functions and spend sit with the GNCTD (the territorial government), not the elected
MCD — and a third enclave (NDMC) is run by a nominated council. This builds a single
per-(body, year) table of headline totals so that split is legible:

  - GNCTD  — Government of NCT of Delhi, from "Budget at a Glance" (₹ crore)
  - MCD    — Municipal Corporation of Delhi, income/expenditure budgets (₹ lakh → crore;
             pre-2022 docs are SOUTH MCD only — the trifurcation era — flagged per row)
  - NDMC   — New Delhi Municipal Council, Budget at a Glance 2025-26 (₹ crore)

Inputs: data/cities/delhi/source/budget/{gnctd,mcd,ndmc}/**.pdf (text-layer; scanned
ones OCR'd to derived/finance/_ocr_text/*.txt by the OCR pre-pass).
Outputs: data/cities/delhi/derived/finance/delhi_finance.{json,csv}

HONESTY: headline value per doc = the latest Budget-Estimate column in that document
(rightmost numeric on the total line); estimate basis + fiscal year are recorded per row,
and the unit/trifurcation caveats are carried in the output, not hidden.

Run: python3 scripts/recipes/delhi/parse_budget_finance.py
"""
from __future__ import annotations
import csv, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUDGET = ROOT / "data/cities/delhi/source/budget"
OCR = ROOT / "data/cities/delhi/derived/finance/_ocr_text"
OUT = ROOT / "data/cities/delhi/derived/finance"

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")  # plain or comma-grouped, optional decimal


def text_of(pdf: Path) -> str:
    """pdftotext -layout; fall back to the OCR sidecar for scanned PDFs."""
    try:
        t = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                           capture_output=True, text=True, timeout=120).stdout
    except Exception:
        t = ""
    if len(t.replace(" ", "").strip()) > 1000:
        return t
    sidecar = OCR / (str(pdf.relative_to(BUDGET)).replace("/", "__")[:-4] + ".txt")
    return sidecar.read_text(encoding="utf-8", errors="ignore") if sidecar.exists() else t


def is_ocr(pdf: Path) -> bool:
    """True if this PDF had no usable text layer (figures came from OCR — spot-check them)."""
    try:
        t = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                           capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return True
    return len(t.replace(" ", "").strip()) <= 1000


def nums(line: str) -> list[float]:
    out = []
    for tok in NUM.findall(line):
        try:
            out.append(float(tok.replace(",", "")))
        except ValueError:
            pass
    return out


def fy_from_name(name: str) -> str:
    # If the filename carries an explicit Budget-Estimate year (e.g. "RBE_18-19_BE_19-20"),
    # the MCD parse extracts the BE column, so label the row with the BE year — not the
    # leading/RBE year — so the value and its year stay in step. (?<!R) skips the BE in "RBE".
    be = re.search(r"(?<!R)BE[_ ]?(?:20)?(\d{2})-(\d{2})", name)
    if be:
        return f"20{be.group(1)}-{be.group(2)}"
    yrs = re.findall(r"(20\d{2})-(\d{2})", name)  # no \b: underscores aren't boundaries
    return f"{yrs[0][0]}-{yrs[0][1]}" if yrs else ""  # else filenames lead with the primary FY


def last_total(text: str, *patterns: str) -> float | None:
    """Rightmost numeric on the last line matching any pattern (the latest BE column).
    If the matched line carries no numbers (layout wrapped them onto the next line),
    look ahead up to 2 lines for the figures."""
    val = None
    for ln in text.splitlines():
        if any(p in ln.lower() for p in patterns):
            n = nums(ln)
            if n:
                val = n[-1]  # rightmost = latest BE column
    return val


def plausible(cr: float | None, floor: float) -> float | None:
    """Drop implausibly small parses (a footnote/fragment matched a total label).
    Better an honest null than a wrong number."""
    return cr if (cr is not None and abs(cr) >= floor) else None


def _vision_overlay() -> dict:
    """Headline GNCTD totals read by Claude vision off the scanned PDFs, to correct
    tesseract digit-drops/misses. Overrides the OCR value for the years it covers."""
    p = BUDGET / "gnctd_vision_verified.json"
    return json.loads(p.read_text(encoding="utf-8")).get("verified", {}) if p.exists() else {}


def parse_gnctd() -> list[dict]:
    overlay = _vision_overlay()
    rows = []
    for pdf in sorted((BUDGET / "gnctd").rglob("*.pdf")):
        if "glance" not in pdf.name.lower():
            continue
        t = text_of(pdf)
        fy = fy_from_name(pdf.name)
        # Prefer the canonical numbered summary line ("Total Receipts (1+4)",
        # "Total Expenditure (9+12)") over any sub-section total; fall back to the loose
        # label only if the formula line isn't present (e.g. mangled OCR).
        # A Delhi state-budget total is ≥ ₹5,000 cr; smaller = OCR/line mis-parse -> null.
        rec_total = plausible(last_total(t, "total receipts (") or last_total(t, "total receipts"), 5000)
        exp_total = plausible(last_total(t, "total expenditure (") or last_total(t, "total expenditure"), 5000)
        own_tax = plausible(last_total(t, "own tax revenue"), 1000)
        # a budget is ~balanced; if exp is wildly off receipts it's a mis-parse (usually OCR) -> null it
        if rec_total and exp_total and not (0.6 <= exp_total / rec_total <= 1.7):
            exp_total = None
        if exp_total and rec_total and not (0.6 <= rec_total / exp_total <= 1.7):
            rec_total = None
        ocr = is_ocr(pdf)
        vision = fy in overlay
        if vision:  # Claude-vision-read values override tesseract for these scanned years
            exp_total = overlay[fy].get("exp", exp_total)
            rec_total = overlay[fy].get("rec", rec_total)
        if not (rec_total or exp_total):
            continue
        rows.append({"body": "GNCTD", "body_full": "Government of NCT of Delhi", "fy": fy,
                     "total_receipts_cr": rec_total, "total_expenditure_cr": exp_total,
                     "own_tax_revenue_cr": own_tax, "unit": "INR_crore",
                     "estimate": "latest BE column in Budget-at-a-Glance",
                     "ocr_sourced": ocr and not vision, "vision_verified": vision,
                     "source_pdf": str(pdf.relative_to(ROOT)), "scope": "whole NCT (territorial govt)"})
    return rows


def parse_mcd() -> list[dict]:
    by_fy: dict[str, dict] = {}
    for pdf in sorted((BUDGET / "mcd").rglob("*.pdf")):
        t = text_of(pdf)
        fy = fy_from_name(pdf.name)
        if not fy:
            continue
        south = "south" in pdf.name.lower() or "sdmc" in pdf.name.lower()
        r = by_fy.setdefault(fy, {"body": "MCD", "body_full": "Municipal Corporation of Delhi", "fy": fy,
                                  "unit": "INR_crore", "estimate": "latest BE column", "source_pdfs": [],
                                  "scope": ""})
        r["source_pdfs"].append(str(pdf.relative_to(ROOT)))
        r["scope"] = "South MCD only (trifurcation era)" if south else "unified MCD"
        # values printed in LAKH in MCD docs -> /100 to crore
        gt = last_total(t, "grand total")
        ptax = last_total(t, "property tax")  # property-tax group subtotal
        grants = last_total(t, "contribution from govt. grants", "govt. grants")
        # MCD figures are native LAKH -> /100 to crore; floors reject footnote mis-parses
        gt_cr = plausible(round(gt / 100, 1) if gt else None, 500)        # a corp total is ≥ ₹500 cr
        ptax_cr = plausible(round(ptax / 100, 1) if ptax else None, 30)   # property-tax subtotal
        grants_cr = plausible(round(grants / 100, 1) if grants else None, 10)
        if "income" in pdf.name.lower() or "receipt" in pdf.name.lower():
            if gt_cr: r["total_income_cr"] = gt_cr
            if ptax_cr: r["property_tax_cr"] = ptax_cr
            if grants_cr: r["govt_grants_cr"] = grants_cr
        elif "expenditure" in pdf.name.lower():
            if gt_cr: r["total_expenditure_cr"] = gt_cr
        else:  # combined income+expenditure docs (post-2019): grand total = income side
            if gt_cr: r["total_income_cr"] = gt_cr
            if ptax_cr: r["property_tax_cr"] = ptax_cr
    return [by_fy[k] for k in sorted(by_fy)]


def parse_ndmc() -> list[dict]:
    rows = []
    glance = next((BUDGET / "ndmc").rglob("*Glance*"), None) or next((BUDGET / "ndmc").rglob("*lance*.pdf"), None)
    if glance:
        t = text_of(glance)
        rows.append({"body": "NDMC", "body_full": "New Delhi Municipal Council", "fy": "2025-26",
                     "total_receipts_cr": last_total(t, "total receipt"),
                     "total_expenditure_cr": last_total(t, "total expenditure"),
                     "unit": "INR_crore", "estimate": "FY25-26 BE", "council": "nominated (no elected member)",
                     "source_pdf": str(glance.relative_to(ROOT)), "scope": "New Delhi enclave (~42.7 km², ~258k residents)"})
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = parse_gnctd() + parse_mcd() + parse_ndmc()
    meta = {
        "city": "delhi", "generated": "2026-06-20",
        "what": "Headline budget totals for Delhi's three civic bodies (GNCTD / MCD / NDMC), to show the municipal-finance fragmentation.",
        "caveats": [
            "Units normalised to INR crore (GNCTD/NDMC native crore; MCD native lakh ÷100).",
            "MCD pre-2022 rows are SOUTH MCD only (the corporation was trifurcated 2012-2022; unified 2022). Scope flagged per row — do NOT sum across the discontinuity.",
            "Headline value = the latest Budget-Estimate column in each document; mixed Actuals/RE/BE bases across docs. Estimate basis recorded per row.",
            "27 of 102 source PDFs were scanned and OCR'd (older GNCTD) by tesseract. The GNCTD years with OCR digit-drops/misses (2008-09, 2009-10, 2014-15, 2015-16, 2017-18, 2018-19) were re-read by Claude vision and corrected (vision_verified:true; values in gnctd_vision_verified.json); other tesseract years (ocr_sourced:true) were validated against vision spot-checks but not each individually.",
        ],
        "rows": rows,
    }
    (OUT / "delhi_finance.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    # flat CSV
    fields = ["body", "fy", "scope", "total_receipts_cr", "total_income_cr", "total_expenditure_cr",
              "own_tax_revenue_cr", "property_tax_cr", "govt_grants_cr", "estimate", "unit"]
    with (OUT / "delhi_finance.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote delhi_finance.json + .csv — {len(rows)} rows "
          f"(GNCTD {sum(r['body']=='GNCTD' for r in rows)}, MCD {sum(r['body']=='MCD' for r in rows)}, NDMC {sum(r['body']=='NDMC' for r in rows)})")
    for r in rows:
        head = r.get("total_expenditure_cr") or r.get("total_receipts_cr") or r.get("total_income_cr")
        print(f"  {r['body']:<6} {r['fy']:<8} ~₹{head} cr  [{r.get('scope','')}]")


if __name__ == "__main__":
    main()
