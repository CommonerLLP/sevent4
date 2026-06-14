#!/usr/bin/env python3
"""Comb all AMC budget books (2005-06 -> 2026-27) for road-spend evidence.

Reads budget PDFs from local-only source archives. Set AMC_PDF_DIRS to one or
more colon-separated directories when the PDFs are stored outside this repo.

Outputs into data/cities/ahmedabad/source/budget/roads/:
  code_rows_raw.csv   - every code-table line matching the road vocabulary,
                        with year, source pdf, page, raw line (no column
                        interpretation here; that happens downstream with
                        per-era column maps)
  page_index.json     - per book: pages classified as narrative / ward-table /
                        contractor-candidate / code-table, for manual reading
  dumps/<book>/pNNN.txt - extracted text of every flagged page

Rule Zero: this script never interprets a figure; it only locates and
preserves raw text with page cites.
"""

import csv
import json
import os
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/cities/ahmedabad/source/budget/roads"
PDF_DIRS = [
    ROOT / "data/cities/ahmedabad/source/budget/amc_pdfs",
    ROOT / "data/sources/budget/amc_pdfs",
    ROOT / "data/raw/budget",
]
PDF_DIRS += [
    Path(d).expanduser()
    for d in os.environ.get("AMC_PDF_DIRS", "").split(os.pathsep)
    if d.strip()
]


def budget_pdf(name):
    for directory in PDF_DIRS:
        candidate = directory / name
        if candidate.exists():
            return candidate
    return PDF_DIRS[0] / name

# year -> canonical PDF (duplicates in the corpus resolved to one file each)
BOOKS = {
    "2005-06": budget_pdf("AMCbudget_2005-06.pdf"),
    "2006-07": budget_pdf("AMCbudget_2006-07.pdf"),
    "2007-08": budget_pdf("AMCbudget_2007-08.pdf"),
    "2008-09": budget_pdf("AMCbudget_2008-09.pdf"),
    "2009-10": budget_pdf("AMCbudget_2009-10.pdf"),
    "2010-11": budget_pdf("AMCbudget_2010-11.pdf"),
    "2011-12": budget_pdf("AMCbudget_2011-12.pdf"),
    "2012-13": budget_pdf("AMCbudget_2012-13.pdf"),
    "2013-14": budget_pdf("AMCbudget_2013-14.pdf"),
    "2014-15": budget_pdf("AMCbudget_2014-15.pdf"),
    "2015-16": budget_pdf("AMCbudget_2015-16.pdf"),
    "2016-17": budget_pdf("AMCbudget_2016-17.pdf"),
    "2017-18": budget_pdf("AMCbudget_2017-18.pdf"),
    "2018-19": budget_pdf("AMCbudget_2018-19.pdf"),
    "2019-20": budget_pdf("AMCbudget_2019-20.pdf"),
    # NOTE: amc_budget_2021-22.pdf is byte-identical (md5 e9608bef...) to
    # Budget_2020_21_English.pdf - the corpus holds NO genuine 2021-22 book.
    "2024-25": budget_pdf("AMCbudget_2024-25.pdf"),
    "2025-26": budget_pdf("AMCbudget_2025-26.pdf"),
    "2026-27": budget_pdf("AMCbudget_2026-27.pdf"),
    # English editions (narrative + clean code tables)
    "2018-19-EN": budget_pdf("Budget_2018_19_English.pdf"),
    "2019-20-EN": budget_pdf("Budget_2019_20_English.pdf"),
    "2020-21-EN": budget_pdf("Budget_2020_21_English.pdf"),
    "2022-23-EN": budget_pdf("Budget_2022_23_English.pdf"),
    "2023-24-EN": budget_pdf("Budget_2023_24_English.pdf"),
}

# Road-money account-code vocabulary (learned from the 2023-24 English code
# tables; the same scheme keys the Gujarati books, whose labels are
# legacy-font garble).
ROAD_CODES = {
    # dept 381 revenue expenditure
    "38401": "ROADS STREETS AND PAVEMENTS (rev exp)",
    "38407": "FOOT-PATH PAVEMENTS (rev exp)",
    "38413": "POLE PAVEMENTS (rev exp)",
    # capital expenditure road heads (appear under dept 381 AND under
    # dept 962 ZONAL CAPITAL WORKS and dept 968 WORKS TAKEN UNDER C.M. -
    # the three road-money streams)
    "64401": "ROADS AND STREETS RESURFACING (capex)",
    "64406": "ROADS AND STREETS - GENERAL (capex)",
    "64407": "FOOTPATH AND PAVEMENTS (capex)",
    "64410": "NALA - GENERAL (capex)",
    "64414": "TRAFFIC CONTROL BLOCK (capex)",
    "64452": "70:20:10 SCHEME ROAD IN SOC (capex)",
    "64453": "R.C.C. ROAD (capex)",
    "64729": "HOT MIX PLANT (capex)",
    # dept 382 bridges
    "64402": "OTHER BRIDGES (capex)",
    # road-related incomes
    "10301": "VEHICLE TAX (rev inc, dept 381)",
    "13423": "ROAD CUT RESTORATION CHARGES (rev inc)",
    "23306": "PENALTY RECOVERED FROM CONTRACTORS (rev inc)",
    "23311": "COST OF WORK DONE ON CAPITAL A/C LSR (rev inc)",
    "86244": "40% PUBLIC CONTRIB FOR ROADS (cap inc)",
    "86269": "70:20:10 SCHEME ROAD CONTRIB (cap inc)",
    "86275": "ROAD AT 80:20 SCHEME (cap inc)",
}
# No leading boundary: amounts merge into codes in the tables
# ("2000.0064406", and in pre-2009 books "100064206" with integer thousands).
# False positives are filtered downstream during column interpretation.
CODE_RE = re.compile(r"(" + "|".join(ROAD_CODES) + r")(?!\d)")

# Department (3-digit) section headers inside code tables. English books:
# "381 ROADS,STREETS, PAVEMENTS"; Gujarati books: 3-digit code + legacy-font
# garble. A header line has no long digit runs after the name (totals lines
# repeat the header WITH figures - we keep those too, tagged dept-total).
DEPT_HEADER_RE = re.compile(r"^\s*(\d{3})\s+(\S.*)$")
DEPTS_OF_INTEREST = {"381", "382", "962", "963", "964", "965", "966",
                     "967", "968", "969", "371"}

# Narrative keywords across the four text encodings in the corpus:
#  - Latin (English editions)
#  - EklG-style legacy Gujarati (most books: htuz = road, hM<t/hM‚t = rasta,
#    heËhV/rhmhV = resurf..., btE¢tu = micro...)
#  - Saral-ASCII legacy (2005-08 era code tables: ZM0 = road, Z:TF = rasta,
#    ZL;Z = resurf..., 0FDZ = damar/asphalt)
#  - Unicode Gujarati (2026-27 book; pypdf mangles conjuncts:
#    "ર°તા" = રસ્તા, "Ëગિત" = પ્રગતિ)
NARRATIVE_KW = [
    "road project", "resurfac", "white topping", "micro surfac",
    "works in progress", "main works",
    "htuz", "hM<t", "hM‚t", "heËhV", "rhmhV", "btE¢tu",
    "ZM0", "Z:TF", "ZL;Z", "0FDZ",
    "રોડ", "રસ્તા", "ર°તા", "રીસરફેસ", "ડામર", "ફૂટપાથ",
    "પ્રગતિના કામ", "Ëગિતના કામ",
]
CONTRACTOR_KW = [
    "contractor", "tender", "agency",
    "ftuLx[t", "ftuLx²t", "xuLzh", "yusLËe", "yusLme",
    "SMg8=", "8[g0Z",
    "કોન્ટ્રા", "કાે¤ટĥા", "ટેન્ડર", "ટે¤ડર", "ઈજારા", "ભાવપત્રક",
]
WARD_TABLE_KW = [
    "Wardwise", "Ward No", "Zonewise",
    "Roadstreet", "Re-Surface", "Resurface",
]


def classify_page(text):
    tags = set()
    tl = text.lower()
    if CODE_RE.search(text):
        tags.add("code-table")
    if any(k.lower() in tl for k in NARRATIVE_KW):
        tags.add("narrative")
    if any(k.lower() in tl for k in CONTRACTOR_KW):
        tags.add("contractor-candidate")
    if sum(k.lower() in tl for k in WARD_TABLE_KW) >= 2:
        tags.add("ward-table")
    return tags


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dumps = OUT / "dumps"
    dumps.mkdir(exist_ok=True)

    rows = []
    page_index = {}

    for year, path in BOOKS.items():
        if not path.exists():
            print(f"!! missing {path}", file=sys.stderr)
            continue
        reader = PdfReader(str(path))
        info = {"pdf": str(path), "pages": len(reader.pages),
                "narrative": [], "ward-table": [], "contractor-candidate": [],
                "code-table": []}
        book_dump = dumps / year
        current_dept = None
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            tags = classify_page(text)
            for tag in tags:
                info[tag].append(i + 1)
            if tags & {"narrative", "ward-table", "contractor-candidate"}:
                book_dump.mkdir(exist_ok=True)
                (book_dump / f"p{i + 1:03d}.txt").write_text(text)
            for line in text.splitlines():
                dm = DEPT_HEADER_RE.match(line)
                if dm:
                    digits_after = sum(c.isdigit() for c in dm.group(2))
                    if digits_after <= 4:  # header, not a 5-digit code row
                        current_dept = (dm.group(1), dm.group(2).strip()[:60])
                    elif dm.group(1) in DEPTS_OF_INTEREST:
                        rows.append({
                            "year": year, "code": f"DEPT{dm.group(1)}",
                            "head": "DEPT TOTAL", "page": i + 1,
                            "dept": dm.group(1),
                            "dept_name": dm.group(2).strip()[:60],
                            "raw_line": line.strip(),
                        })
                m = CODE_RE.search(line)
                if m:
                    rows.append({
                        "year": year,
                        "code": m.group(1),
                        "head": ROAD_CODES[m.group(1)],
                        "page": i + 1,
                        "dept": current_dept[0] if current_dept else "",
                        "dept_name": current_dept[1] if current_dept else "",
                        "raw_line": line.strip(),
                    })
        page_index[year] = info
        print(f"{year}: {info['pages']}p  narrative={len(info['narrative'])} "
              f"ward={len(info['ward-table'])} contractor={len(info['contractor-candidate'])} "
              f"code-rows-pages={len(info['code-table'])}")

    with open(OUT / "code_rows_raw.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "code", "head", "page",
                                          "dept", "dept_name", "raw_line"])
        w.writeheader()
        w.writerows(rows)
    (OUT / "page_index.json").write_text(json.dumps(page_index, indent=2))
    print(f"\n{len(rows)} code rows -> {OUT / 'code_rows_raw.csv'}")


if __name__ == "__main__":
    main()
