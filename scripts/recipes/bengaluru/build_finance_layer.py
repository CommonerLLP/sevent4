#!/usr/bin/env python3
"""Process the BBMP ward work-order ledgers into a teachable ward-spend layer.

Reads the 198 by-ward CSVs (raw, on the external volume), aggregates per ward, and writes:
  - ward_workorders.json   per-ward: total/median spend, work count, top contractors,
                            top budget heads, and the top-N NAMED works (for the popup)
  - a join report to wards_bbmp198.geojson by normalised ward name (match rate stated, not assumed)

This is the "layer now" deliverable; the contractor-concentration investigation is deferred.

Run:  .venv/bin/python scripts/recipes/bengaluru/build_finance_layer.py
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = Path(os.environ.get("OPENCITY_ARCHIVE", str(ROOT / "data" / "sources" / "opencity")))
RAW = ARCHIVE / "bengaluru" / "raw" / "bbmp-work-orders-by-ward-2013-2022"
CITY = ROOT / "data" / "cities" / "bengaluru"
OUT = CITY / "source" / "finance"


def num(s) -> int:
    s = re.sub(r"[^0-9]", "", str(s or ""))
    return int(s) if s else 0


def norm_ward(s: str) -> str:
    """'001 Kempegowda Ward' -> ('1','kempegowda'); returns (num, name_key)."""
    s = (s or "").strip()
    m = re.match(r"^0*(\d+)\s+(.*?)(?:\s+ward)?\s*$", s, re.I)
    if m:
        return m.group(1), re.sub(r"[^a-z]", "", m.group(2).lower())
    return "", re.sub(r"[^a-z]", "", s.lower())


def ward_from_filename(path: str) -> tuple[str, str]:
    """'Work_Orders_for_A_Narayanapura_Num-56_Ward.csv' -> ('56', 'A Narayanapura')."""
    b = Path(path).stem
    m = re.search(r"Work_Orders_for_(.+?)_Num-(\d+)_Ward", b)
    if m:
        return m.group(2), m.group(1).replace("_", " ").strip()
    return "", b


def read_rows(path: str):
    """Yield dict rows, skipping the BBMP title preamble by finding the real header line."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    hdr = next((i for i, ln in enumerate(lines)
                if "Name of Work" in ln or "Job Number" in ln), 0)
    rd = csv.DictReader(lines[hdr:])
    yield from rd


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(str(RAW / "*.csv")))
    wards: dict[str, dict] = {}

    for f in files:
        fnum, fname = ward_from_filename(f)
        key = fnum or re.sub(r"[^a-z]", "", fname.lower())
        if not key:
            continue
        w = wards.setdefault(key, {
            "ward_num": fnum, "ward_name": f"{int(fnum):03d} {fname}" if fnum.isdigit() else fname,
            "total_nett": 0, "count": 0,
            "contractors": Counter(), "heads": Counter(), "works": [],
        })
        for row in read_rows(f):
                nett = num(row.get("Nett"))
                w["total_nett"] += nett
                w["count"] += 1
                ct = (row.get("Contractor") or "").strip()
                if ct:
                    w["contractors"][ct] += nett
                head = (row.get("Budget Head") or "").strip()
                if head:
                    w["heads"][head[:70]] += nett
                name = (row.get("Name of Work") or "").strip()
                if name and nett > 0:
                    w["works"].append((nett, name, ct, head[:40]))

    # finalise: keep top works/contractors/heads, drop the Counters
    table = []
    for key, w in wards.items():
        works = sorted(w["works"], reverse=True)[:8]
        table.append({
            "ward_num": w["ward_num"],
            "ward_name": w["ward_name"],
            "total_nett_cr": round(w["total_nett"] / 1e7, 2),
            "work_count": w["count"],
            "top_contractors": [{"name": c, "cr": round(v / 1e7, 2)}
                                for c, v in w["contractors"].most_common(3)],
            "top_budget_heads": [{"head": h, "cr": round(v / 1e7, 2)}
                                 for h, v in w["heads"].most_common(3)],
            "flagged_works": [{"name": n, "contractor": c, "head": h, "lakh": round(v / 1e5)}
                              for v, n, c, h in works],
        })
    table.sort(key=lambda x: -x["total_nett_cr"])
    (OUT / "ward_workorders.json").write_text(json.dumps(table, indent=2, ensure_ascii=False))

    # join report against the BBMP-2023 boundary (vintage check)
    bnd = CITY / "source" / "boundaries" / "wards_bbmp198.geojson"
    bkeys = {}
    if bnd.exists():
        g = json.load(open(bnd))
        for ft in g["features"]:
            p = ft["properties"]
            nm = p.get("name_en") or p.get("proposed_ward_name_en") or p.get("Name") or ""
            bkeys[re.sub(r"[^a-z]", "", str(nm).lower())] = nm
    matched = sum(1 for w in table if re.sub(r"[^a-z]", "", w["ward_name"].split(" ", 1)[-1].replace("Ward", "").lower()) in bkeys)

    tot = sum(w["total_nett_cr"] for w in table)
    print(f"wards in ledger: {len(table)}  | total Nett: Rs {tot:,.0f} cr | works: {sum(w['work_count'] for w in table):,}")
    print(f"BBMP-2023 boundary names: {len(bkeys)} | name-matched to ledger wards: {matched}/{len(table)}")
    print(f"wrote {OUT/'ward_workorders.json'}")
    print("\nTop 5 wards by spend:")
    for w in table[:5]:
        print(f"  {w['ward_name'][:24]:26} Rs {w['total_nett_cr']:7,.1f} cr  {w['work_count']:4} works  "
              f"top: {w['top_contractors'][0]['name'][:22] if w['top_contractors'] else '-'}")


if __name__ == "__main__":
    main()
