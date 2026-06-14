#!/usr/bin/env python3
"""
build_budget_db.py — build the canonical municipal budget database (Ahmedabad first).

Reproducible: `python scripts/budget_db/build_budget_db.py`
Inputs  (verified, in-repo):
    data/cities/ahmedabad/source/budget/amc_budget_22yr.csv
    data/cities/ahmedabad/source/budget/amc_civic_lines.json
    data/cities/ahmedabad/source/budget/amts_income_expenditure.json
Inputs  (optional, best-effort text extraction if PDFs are found on disk):
    AMC budget PDFs under the PDF_DIRS below (gitignored data).
Outputs (data/cities/ahmedabad/db/):
    amc_budget.sqlite        canonical store
    amc_budget.duckdb        DuckDB mirror
    budget_line.parquet      columnar
    budget_line.csv          flat
    amc_budget.json          full dump (source_doc + budget_line)
    amc_budget.xlsx          spreadsheet (budget_line + entity_timeseries + coverage)
No figure is invented: every row carries source_pdf, page, extraction_method, confidence.
"""
import sqlite3, json, csv, re, os, subprocess, glob, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC  = ROOT / "data/cities/ahmedabad/source/budget"
DB   = ROOT / "data/cities/ahmedabad/db"
SCHEMA = Path(__file__).parent / "schema.sql"
DB.mkdir(parents=True, exist_ok=True)

# PDF search dirs: local-only source archive first; extra dirs via env
# (colon-separated). Example:
#   AMC_PDF_DIRS="$HOME/Downloads:/path/to/archive" python build_budget_db.py
PDF_DIRS = [
    ROOT / "data/cities/ahmedabad/source/budget/amc_pdfs",
    ROOT / "data/sources/budget/amc_pdfs",
]
PDF_DIRS += [Path(d).expanduser() for d in os.environ.get("AMC_PDF_DIRS","").split(os.pathsep) if d.strip()]

# ---- survey of the 22-year archive (from the extractability audit) -------------
SOURCE_DOCS = [   # (fy, edition, script_kind, extractability, file-glob)
    ("2005-06","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2005-06.pdf"),
    ("2006-07","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2006-07.pdf"),
    ("2007-08","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2007-08.pdf"),
    ("2008-09","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2008-09.pdf"),
    ("2009-10","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2009-10.pdf"),
    ("2010-11","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2010-11.pdf"),
    ("2011-12","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2011-12.pdf"),
    ("2012-13","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2012-13.pdf"),
    ("2013-14","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2013-14.pdf"),
    ("2014-15","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2014-15.pdf"),
    ("2015-16","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2015-16.pdf"),
    ("2016-17","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2016-17.pdf"),
    ("2017-18","gujarati","gujarati_legacy","ocr_needed","AMCbudget_2017-18.pdf"),
    ("2018-19","english","english","text","AMC_Budget_2018-19_English9026.pdf"),
    ("2019-20","english","english","text","AMC_Budget_2019-20_English9594.pdf"),
    ("2021-22","english","english","text","amc_budget_2021-22.pdf"),
    ("2022-23","english","english","text","AMC_Budget_2022-23_English2679.pdf"),
    ("2023-24","english","english","text","AMC_Budget_2023-24_English (1)6444.pdf"),
    ("2024-25","gujarati","gujarati_legacy","ocr_needed","amc_budget_2024-25.pdf"),
    ("2025-26","gujarati","gujarati_legacy","ocr_needed","amc_budget_2025-26.pdf"),
    ("2026-27","gujarati","gujarati_unicode","text","amc_budget_2026-27.pdf"),
]

def fy_start(fy): return int(fy.split("-")[0])

def find_pdf(name):
    for d in PDF_DIRS:
        p = d / name
        if p.exists(): return str(p)
    return None

# ---- entity / category mapping -------------------------------------------------
LINE_MAP = {   # civic_lines 'line' -> (entity, head_category, head_name, section, flow)
    "AMTS":               ("AMTS","department_support","Loan/support to AMTS (city bus)","capital","expenditure"),
    "ajl_brts":           ("AJL_BRTS","department_support","Support to Ahmedabad Janmarg Ltd (BRTS)","capital","expenditure"),
    "library_mj":         ("MJ_LIBRARY","grant_contribution","Grant to Sheth M.J. Library","revenue","expenditure"),
    "library_branch_total":("LIBRARY_BRANCHES","grant_contribution","Grant to branch libraries","revenue","expenditure"),
    "vs_hospital":        ("VS_HOSPITAL","grant_contribution","Grant to V.S. Hospital","revenue","expenditure"),
    "riverfront_srfdcl":  ("SRFDCL","capital_works","Sabarmati Riverfront (SRFDCL)","capital","expenditure"),
    "school_board":       ("SCHOOL_BOARD","grant_contribution","Grant to Municipal School Board","revenue","expenditure"),
    "parks_gardens":      ("PARKS","maintenance","Parks & gardens","revenue","expenditure"),
}

rows = []          # list of dicts -> budget_line
seen = set()       # dedup key

def add(fy, basis, section, flow, cat, name, amount, *, entity=None, raw=None,
        pdf=None, page=None, method="text", conf="medium", note=None):
    # dedup on the full identity: same (year, basis, entity, head) loaded twice = dup;
    # different heads for the same entity/year (e.g. AMTS total-budget vs loan vs income
    # components) are DISTINCT rows and must coexist.
    key = ("ahmedabad", fy, basis, entity or "", name)
    if key in seen:   # first loader (most authoritative) wins
        return False
    seen.add(key)
    rows.append(dict(city="ahmedabad", fiscal_year=fy, fy_start=fy_start(fy),
        estimate_basis=basis, section=section, flow=flow, head_category=cat,
        head_name=name, head_name_raw=raw, entity=entity,
        amount_cr=(round(float(amount),4) if amount is not None else None),
        amount_raw=raw, source_pdf=pdf, page=page,
        extraction_method=method, confidence=conf, note=note))
    return True

# ============================================================================
# LOADER 1 — civic_lines.json  (verified, detailed, 2018-24; most authoritative)
# ============================================================================
cv = json.load(open(SRC/"amc_civic_lines.json"))
for r in cv["data"]:
    ent, cat, name, sec, flow = LINE_MAP.get(r["line"], (None,"other_expenditure",r["line"],None,None))
    ah = (r.get("account_head") or "").lower()
    basis = "actual" if ("actual" in ah or "spend" in ah) else ("RE" if "revised" in ah else "BE")
    add(r["year"], basis, sec, flow, cat, name, r.get("amount_cr"),
        entity=ent, raw=r.get("raw"), pdf=r.get("source_pdf"), page=r.get("page"),
        method="manual_verified", conf=r.get("confidence","high"),
        note=r.get("exact_line"))

# ============================================================================
# LOADER 2 — amts_income_expenditure.json  (AMTS internal I&E, verified-from-press)
# ============================================================================
ie = json.load(open(SRC/"amts_income_expenditure.json"))
for y in ie["amts_income_expenditure"]:
    fy = y["year"]; src = y.get("source")
    inc = y.get("income_components_cr",{})
    for k,v in inc.items():
        if isinstance(v,(int,float)):
            add(fy,"BE","revenue","income","non_tax_revenue",
                f"AMTS income — {k.replace('_',' ')}", v, entity="AMTS",
                raw=str(v), pdf=None, method="text", conf="medium", note=src)
    exp = y.get("expenditure_components_cr",{})
    for k,v in exp.items():
        if isinstance(v,(int,float)):
            add(fy,"BE","revenue","expenditure","establishment",
                f"AMTS expenditure — {k.replace('_',' ')}", v, entity="AMTS",
                raw=str(v), pdf=None, method="text", conf="medium", note=src)
    for k,lbl,cat,flow,sec in [("income_total_cr","AMTS total income","non_tax_revenue","income","revenue"),
                                ("total_budget_cr","AMTS total budget","department_support","expenditure","revenue"),
                                ("amc_loan_to_amts_cr","AMC deficit-loan to AMTS","department_support","expenditure","capital"),
                                ("accumulated_debt_cr","AMTS accumulated debt","loan_charges","expenditure","capital")]:
        if isinstance(y.get(k),(int,float)):
            add(fy,"BE",sec,flow,cat,lbl,y[k],entity="AMTS",raw=str(y[k]),
                method="text",conf="medium",note=src)

# audited cumulative cross-check (one-off, FY mark 2023-24)
ax = ie.get("audited_cumulative_cross_check",{})
for k,lbl,ent in [("amts_cumulative_amc_subsidy_loans_cr","AMTS cumulative AMC subsidy-loans","AMTS"),
                  ("ajl_brts_capex_loan_cr","AJL BRTS capex loan (cumulative)","AJL_BRTS"),
                  ("ajl_brts_operating_gap_loan_cr","AJL operating-gap loan (cumulative)","AJL_BRTS")]:
    if isinstance(ax.get(k),(int,float)):
        add("2023-24","actual","capital","expenditure","loan_charges",lbl,ax[k],
            entity=ent,raw=str(ax[k]),method="manual_verified",conf="high",
            note=ax.get("source"))

# ============================================================================
# LOADER 3 — amc_budget_22yr.csv  (headline lines 2005-2026; fills gaps L1 lacks)
# ============================================================================
for r in csv.DictReader(open(SRC/"amc_budget_22yr.csv")):
    fy = r["year"]; conf = r.get("confidence","medium"); pg = r.get("amts_page") or None
    pg = int(pg) if (pg and str(pg).isdigit()) else None
    def num(x):
        x=(x or "").strip(); return float(x) if x else None
    if num(r.get("amts_cr")) is not None:
        add(fy,"BE","capital","expenditure","department_support","Loan/support to AMTS (city bus)",
            num(r["amts_cr"]),entity="AMTS",raw=r.get("notes"),page=pg,
            method="manual_verified",conf=conf,note=r.get("notes"))
    if num(r.get("mj_library_cr")) is not None:
        add(fy,"BE","revenue","expenditure","grant_contribution","Grant to Sheth M.J. Library",
            num(r["mj_library_cr"]),entity="MJ_LIBRARY",method="manual_verified",conf=conf)
    if num(r.get("property_tax_cr")) is not None:
        add(fy,"BE","revenue","income","tax_revenue","Property tax (general tax)",
            num(r["property_tax_cr"]),raw=r.get("property_tax_basis"),
            method="manual_verified",conf=conf,note=r.get("property_tax_basis"))
    if num(r.get("riverfront_cr")) is not None:
        add(fy,"BE","capital","expenditure","capital_works","Sabarmati Riverfront (SRFDCL)",
            num(r["riverfront_cr"]),entity="SRFDCL",method="manual_verified",conf=conf)
    if num(r.get("total_cr")) is not None:
        add(fy,"BE","revenue",None,"total","Total revenue budget",
            num(r["total_cr"]),method="manual_verified",conf=conf)

# ============================================================================
# LOADER 4 — best-effort TEXT extraction of narrative grant lines (clean years)
#   pattern: "Grant to/for <X> .... Rs.<N> crore"  -> grant_contribution
# ============================================================================
GRANT_RE = re.compile(r"Grant (?:to|for)\s+([A-Z][A-Za-z .,&'-]{3,60}?)\s+Rs\.?\s*([\d,]+\.?\d*)\s*crore", re.I)
text_years = [(fy,fn) for (fy,ed,sk,ex,fn) in SOURCE_DOCS if ex=="text" and ed=="english"]
extracted_text = 0
for fy, fn in text_years:
    p = find_pdf(fn)
    if not p: continue
    try:
        txt = subprocess.run(["pdftotext","-layout",p,"-"],capture_output=True,text=True,timeout=120).stdout
    except Exception:
        continue
    for m in GRANT_RE.finditer(txt):
        name = re.sub(r"\s+"," ",m.group(1)).strip(" .,")
        amt  = float(m.group(2).replace(",",""))
        if amt > 100000:   # guard against mis-parses (lakh/typo)
            continue
        ok = add(fy,"BE","revenue","expenditure","grant_contribution",f"Grant to {name}",amt,
                 raw=m.group(0), pdf=os.path.basename(p), method="text", conf="low",
                 note="auto-extracted narrative grant line (low confidence; HITL verify)")
        if ok: extracted_text += 1

# ============================================================================
# BUILD SQLITE
# ============================================================================
sqlite_path = DB/"amc_budget.sqlite"
if sqlite_path.exists(): sqlite_path.unlink()
con = sqlite3.connect(sqlite_path)
con.executescript(SCHEMA.read_text())
# source_doc registry
for fy,ed,sk,ex,fn in SOURCE_DOCS:
    p = find_pdf(fn)
    pages=None
    if p:
        try:
            info=subprocess.run(["pdfinfo",p],capture_output=True,text=True,timeout=20).stdout
            mm=re.search(r"Pages:\s+(\d+)",info); pages=int(mm.group(1)) if mm else None
        except Exception: pass
    con.execute("INSERT OR REPLACE INTO source_doc(source_pdf,city,fiscal_year,edition,script_kind,extractability,pages,abs_path) VALUES(?,?,?,?,?,?,?,?)",
                (fn,"ahmedabad",fy,ed,sk,ex,pages,p))
# auto-register any source_pdf referenced in the data but not in the survey list
known = {fn for fy,ed,sk,ex,fn in SOURCE_DOCS}
for spdf in sorted({r["source_pdf"] for r in rows if r.get("source_pdf")} - known):
    yrm = re.search(r"(20\d\d)[-_](\d\d)", spdf)
    fy = f"{yrm.group(1)}-{yrm.group(2)}" if yrm else None
    con.execute("INSERT OR IGNORE INTO source_doc(source_pdf,city,fiscal_year,edition,script_kind,extractability,abs_path,note) VALUES(?,?,?,?,?,?,?,?)",
                (spdf,"ahmedabad",fy,"english","english","text",find_pdf(spdf),
                 "auto-registered from referenced data"))
# budget_line rows
cols=["city","fiscal_year","fy_start","estimate_basis","section","flow","head_category",
      "head_name","head_name_raw","entity","amount_cr","amount_raw","source_pdf","page",
      "extraction_method","confidence","note"]
con.executemany(f"INSERT INTO budget_line({','.join(cols)}) VALUES({','.join('?'*len(cols))})",
                [[r.get(c) for c in cols] for r in rows])
con.commit()

# ============================================================================
# EXPORTS
# ============================================================================
import pandas as pd
bl = pd.read_sql("SELECT * FROM budget_line", con)
sd = pd.read_sql("SELECT * FROM source_doc", con)
ets= pd.read_sql("SELECT * FROM v_entity_timeseries", con)
cov= pd.read_sql("SELECT * FROM v_coverage", con)

bl.to_csv(DB/"budget_line.csv", index=False)
bl.to_parquet(DB/"budget_line.parquet", index=False)
json.dump({"source_doc":sd.to_dict("records"),"budget_line":bl.to_dict("records")},
          open(DB/"amc_budget.json","w"), indent=1, ensure_ascii=False)
# duckdb mirror (native parquet/sql; the analytics surface)
import duckdb
dpath = DB/"amc_budget.duckdb"
if dpath.exists(): dpath.unlink()
dk = duckdb.connect(str(dpath))
dk.execute("CREATE TABLE budget_line AS SELECT * FROM read_parquet(?)", [str(DB/'budget_line.parquet')])
dk.register("sd_df", sd); dk.execute("CREATE TABLE source_doc AS SELECT * FROM sd_df")
dk.close()
# excel (resilient: openpyxl/pandas-3 can be finicky)
xlsx_ok = True
try:
    with pd.ExcelWriter(DB/"amc_budget.xlsx", engine="openpyxl") as xl:
        bl.to_excel(xl, sheet_name="budget_line", index=False)
        ets.to_excel(xl, sheet_name="entity_timeseries", index=False)
        cov.to_excel(xl, sheet_name="coverage", index=False)
        sd.to_excel(xl, sheet_name="source_doc", index=False)
        xl.book.active = 0
except Exception as e:
    xlsx_ok = False; print(f"  ! xlsx export skipped ({type(e).__name__}: {e})")
con.close()

print(f"✓ built {sqlite_path}")
print(f"  budget_line rows : {len(bl)}")
print(f"  source_docs      : {len(sd)}  (pdf-on-disk: {sd['abs_path'].notna().sum()})")
print(f"  text-extracted   : {extracted_text} narrative grant lines")
print(f"  exports          : sqlite, duckdb, parquet, csv, json, xlsx -> {DB}")
