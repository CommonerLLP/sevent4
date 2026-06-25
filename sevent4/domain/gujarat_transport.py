"""Pure parsing of Gujarat STATE budget detailed-demand text for city-transport
scheme lines. Two line shapes:
  (A) single-line schemes: (N) <desc> <amt> <amt> <amt> <pageref>
  (B) block schemes: a Sub-Head "Gross Total | <BE_total>" line whose description
      accumulates from the preceding "Sub Head :" block.
No filesystem or subprocess IO lives here (the adapter supplies pdftotext text).
"""
from __future__ import annotations

import re

YEARS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26", "2026-27"]
DEMAND_GLOBS = [
    "*Urban Development*_en.pdf", "*Ports & Transport*_en.pdf",
    "*Ports and Transport*_en.pdf", "*Roads & Buildings*_en.pdf",
]

KEEP = re.compile(
    r"metro|GMRC|MEGA|e-?bus|bus depot|BRTS|janmarg|swarnim|SJMMSVY|octroi|"
    r"grant.?in.?lieu|public transport|mass transit|bus rapid|behind-the.?meter",
    re.I,
)


def tag(d):
    d = d.lower()
    if "metro" in d or "gmrc" in d or "mega" in d:
        return "GMRC_METRO"
    if "e-bus" in d or "ebus" in d or "bus depot" in d or "behind-the" in d or "substation" in d:
        return "PM_EBUS_SEWA"
    if "brts" in d or "janmarg" in d or "bus rapid" in d:
        return "BRTS"
    if "octroi" in d or "grant in lieu" in d:
        return "OCTROI_GRANT"
    if "swarnim" in d or "sjmmsvy" in d:
        return "SJMMSVY_URBAN_BUS"
    return "URBAN_TRANSPORT_OTHER"


def central_share(d):
    m = re.search(r"\((\d{1,3})%\s*(Central|State)\s*[Ss]hare\)", d)
    return f"{m.group(1)}% {m.group(2)}" if m else None


def english_run(s):
    runs = re.findall(r"[A-Za-z0-9 ,.&'’()/%\-]{6,}", s)
    return max(runs, key=len).strip() if runs else ""


def amount(value):
    value = str(value or "").strip()
    if not value or value == "--":
        return None
    return float(value.replace(",", ""))


def is_demand_gross_total(line):
    return bool(re.search(r"Gross Total\s*:\s*Demand No\.?", line, re.I))


def gross_total_be_amount(line):
    if is_demand_gross_total(line):
        return None
    m = re.search(r"Gross Total\s*:?\s+([\d,]+\.\d{2,4}|--)(?:\s+\*)?\s*$", line)
    return amount(m.group(1)) if m else None


SINGLE = re.compile(
    r"^\s*\(?(\d{1,3})\)?\s+(.+?)\s+([\d,]+\.\d{2,4}|--)\s+([\d,]+\.\d{2,4}|--)\s+([\d,]+\.\d{2,4}|--)\s+(\d{1,4})\s*$"
)
CODE = re.compile(r"\b(\d{4}\s+\d{2}\s+\d{3}\s+\d{1,3})\b")


def extract_rows_from_text(txt, fy, source_pdf):
    rows = []
    sub_buf = []
    code = None
    for ln in txt.splitlines():
        # shape A: single-line scheme
        m = SINGLE.match(ln)
        if m and KEEP.search(m.group(2)):
            desc = re.sub(r"\s+", " ", m.group(2)).strip()
            amt = amount(m.group(5))
            if amt is not None:
                rows.append(dict(
                    fiscal_year=fy, entity=tag(desc), description_en=english_run(desc),
                    description_raw=desc, amount_total_cr=amt, central_share=central_share(desc),
                    shape="single", account_code=None, source_pdf=source_pdf, raw_line=ln.strip()[:300],
                ))
            continue

        # shape B: accumulate Sub Head block, fire on sub-head Gross Total
        if "Sub Head" in ln:
            sub_buf = []
            code = None
        cm = CODE.search(ln)
        if cm:
            code = cm.group(1)
        eng = english_run(ln)
        if eng and "Gross Total" not in eng and "Detailed Head" not in eng and "Object Head" not in eng:
            sub_buf.append(eng)
        if "Gross Total" in ln:
            amt = gross_total_be_amount(ln)
            desc = " ".join(sub_buf).strip()
            if amt is not None and KEEP.search(desc):
                rows.append(dict(
                    fiscal_year=fy, entity=tag(desc), description_en=desc[:200],
                    description_raw=desc[:300], amount_total_cr=amt, central_share=central_share(desc),
                    shape="block", account_code=code, source_pdf=source_pdf, raw_line=ln.strip()[:200],
                ))
            sub_buf = []
            code = None
    return rows


def dedupe_rows(rows):
    seen = set()
    uniq = []
    for r in rows:
        k = (r["fiscal_year"], r["entity"], (r["description_en"] or "")[:50], r["amount_total_cr"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    return uniq


def build_output(rows):
    uniq = dedupe_rows(rows)
    return {
        "_meta": {
            "title": "Gujarat STATE budget — city-transport scheme allocations (v2 block-aware)",
            "built": "2026-06-12",
            "source": "budget-crawler finance_dept detailed demands (English)",
            "note": "amount_total_cr = budget-year total (BE) per scheme; block rows from Gross-Total lines. HITL verify.",
            "years_found": sorted({r["fiscal_year"] for r in uniq}),
        },
        "rows": uniq,
    }
