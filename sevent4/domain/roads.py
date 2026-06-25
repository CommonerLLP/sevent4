"""Pure AMC budget-book road-spend mining: the road-money account-code
vocabulary, page classification across the corpus's four text encodings, and
per-book code-row extraction with page cites. Rule Zero: this never interprets a
figure; it locates and preserves raw text. No filesystem or PDF IO lives here.

(The resurfaced-register parser, with its contractor/ward decoders, is a
local-only OPSEC-sensitive recipe under scripts/recipes/ahmedabad/_local/ and is
deliberately NOT part of the tracked architecture.)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

# year -> canonical budget-book filename (resolved against PDF dirs by adapter)
BUDGET_BOOK_FILES: dict[str, str] = {
    "2005-06": "AMCbudget_2005-06.pdf",
    "2006-07": "AMCbudget_2006-07.pdf",
    "2007-08": "AMCbudget_2007-08.pdf",
    "2008-09": "AMCbudget_2008-09.pdf",
    "2009-10": "AMCbudget_2009-10.pdf",
    "2010-11": "AMCbudget_2010-11.pdf",
    "2011-12": "AMCbudget_2011-12.pdf",
    "2012-13": "AMCbudget_2012-13.pdf",
    "2013-14": "AMCbudget_2013-14.pdf",
    "2014-15": "AMCbudget_2014-15.pdf",
    "2015-16": "AMCbudget_2015-16.pdf",
    "2016-17": "AMCbudget_2016-17.pdf",
    "2017-18": "AMCbudget_2017-18.pdf",
    "2018-19": "AMCbudget_2018-19.pdf",
    "2019-20": "AMCbudget_2019-20.pdf",
    # NOTE: amc_budget_2021-22.pdf is byte-identical to Budget_2020_21_English.pdf
    # - the corpus holds NO genuine 2021-22 book.
    "2024-25": "AMCbudget_2024-25.pdf",
    "2025-26": "AMCbudget_2025-26.pdf",
    "2026-27": "AMCbudget_2026-27.pdf",
    # English editions (narrative + clean code tables)
    "2018-19-EN": "Budget_2018_19_English.pdf",
    "2019-20-EN": "Budget_2019_20_English.pdf",
    "2020-21-EN": "Budget_2020_21_English.pdf",
    "2022-23-EN": "Budget_2022_23_English.pdf",
    "2023-24-EN": "Budget_2023_24_English.pdf",
}

ROAD_CODES = {
    "38401": "ROADS STREETS AND PAVEMENTS (rev exp)",
    "38407": "FOOT-PATH PAVEMENTS (rev exp)",
    "38413": "POLE PAVEMENTS (rev exp)",
    "64401": "ROADS AND STREETS RESURFACING (capex)",
    "64406": "ROADS AND STREETS - GENERAL (capex)",
    "64407": "FOOTPATH AND PAVEMENTS (capex)",
    "64410": "NALA - GENERAL (capex)",
    "64414": "TRAFFIC CONTROL BLOCK (capex)",
    "64452": "70:20:10 SCHEME ROAD IN SOC (capex)",
    "64453": "R.C.C. ROAD (capex)",
    "64729": "HOT MIX PLANT (capex)",
    "64402": "OTHER BRIDGES (capex)",
    "10301": "VEHICLE TAX (rev inc, dept 381)",
    "13423": "ROAD CUT RESTORATION CHARGES (rev inc)",
    "23306": "PENALTY RECOVERED FROM CONTRACTORS (rev inc)",
    "23311": "COST OF WORK DONE ON CAPITAL A/C LSR (rev inc)",
    "86244": "40% PUBLIC CONTRIB FOR ROADS (cap inc)",
    "86269": "70:20:10 SCHEME ROAD CONTRIB (cap inc)",
    "86275": "ROAD AT 80:20 SCHEME (cap inc)",
}
CODE_RE = re.compile(r"(" + "|".join(ROAD_CODES) + r")(?!\d)")

DEPT_HEADER_RE = re.compile(r"^\s*(\d{3})\s+(\S.*)$")
DEPTS_OF_INTEREST = {"381", "382", "962", "963", "964", "965", "966",
                     "967", "968", "969", "371"}

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

CODE_ROW_FIELDS = ["year", "code", "head", "page", "dept", "dept_name", "raw_line"]


@dataclass
class BookScan:
    rows: list[dict]
    classification: dict
    dump_pages: list[tuple[int, str]]


def classify_page(text: str) -> set[str]:
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


def scan_book_pages(year: str, page_texts: Sequence[str]) -> BookScan:
    """Classify every page and extract road code-rows + dept totals with page
    cites. Returns rows, the page classification index, and the pages whose text
    should be dumped."""
    classification = {
        "pages": len(page_texts),
        "narrative": [], "ward-table": [], "contractor-candidate": [], "code-table": [],
    }
    rows: list[dict] = []
    dump_pages: list[tuple[int, str]] = []
    current_dept = None
    for i, text in enumerate(page_texts):
        tags = classify_page(text)
        for tag in tags:
            classification[tag].append(i + 1)
        if tags & {"narrative", "ward-table", "contractor-candidate"}:
            dump_pages.append((i + 1, text))
        for line in text.splitlines():
            dm = DEPT_HEADER_RE.match(line)
            if dm:
                digits_after = sum(c.isdigit() for c in dm.group(2))
                if digits_after <= 4:
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
    return BookScan(rows=rows, classification=classification, dump_pages=dump_pages)
