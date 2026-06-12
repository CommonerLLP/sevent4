#!/usr/bin/env python3
"""Chennai who-pays layer from the Greater Chennai Corporation Finances (OpenCity).

HONESTY NOTE — VINTAGE: the GCC Finances dataset on data.opencity.in covers only
2012-13 → 2015-16. It is the *latest GCC finance OpenCity holds*; it is NOT current.
Every output is labelled with that vintage. A current layer needs newer GCC accounts
sourced elsewhere (not on OpenCity).

What it builds (zone resolution — GCC publishes its money by ZONE, not ward):
  - data/cities/chennai/layers/zone_finance.geojson  — 15 zones (dissolved from 200
        wards), each with 2013-14 capital-expenditure actuals, the GoTN(state)-grant
        share, and top account heads.  → a who-pays choropleth at the grain the city
        actually discloses.
  - data/cities/chennai/source/finance/chennai_budget.json — the city budget STRUCTURE
        (revenue vs capital, receipts vs expenditure) from the summary statement.

Raw CSVs land under $OPENCITY_ARCHIVE/chennai/raw/gcc-finances/ (external; gitignored
default = in-repo data/sources/opencity). Run:
    OPENCITY_ARCHIVE=<archive-root> .venv/bin/python scripts/recipes/chennai/build_finance.py
"""
from __future__ import annotations
import csv, json, os, re, sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
CATALOGUE = ROOT / "data" / "sources" / "opencity" / "_catalogue" / "opencity_catalogue.json"
ARCHIVE = Path(os.environ.get("OPENCITY_ARCHIVE", str(ROOT / "data" / "sources" / "opencity")))
RAW = ARCHIVE / "chennai" / "raw" / "gcc-finances"
CITY = ROOT / "data" / "cities" / "chennai"
WARDS = CITY / "layers" / "wards.geojson"
OUT_LAYER = CITY / "layers" / "zone_finance.geojson"
OUT_FIN = CITY / "source" / "finance"
UA = {"User-Agent": "sevent4-atlas/1.0 (74th-amendment atlas)"}
VINTAGE = "2012-16 (latest GCC accounts on OpenCity; not current)"
ACTUALS_COL = "2013-14  Actuals"   # last year with ACTUALS (not estimates)

ROMAN = ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV"]


def num(x):
    try: return float(str(x).replace(",", "").strip() or 0)
    except ValueError: return 0.0


def acquire():
    RAW.mkdir(parents=True, exist_ok=True)
    cat = json.load(open(CATALOGUE))
    ds = next((d for d in cat["datasets"] if d.get("title") == "Great Chennai Corporation Finances"), None)
    if not ds: sys.exit("GCC Finances dataset not found in catalogue")
    got = {}
    for r in ds.get("resources", []):
        name = re.sub(r"[^A-Za-z0-9]+", "_", (r.get("name") or "res")).strip("_") + ".csv"
        dst = RAW / name
        if not dst.exists():
            try:
                with urlopen(Request(r["url"], headers=UA), timeout=60) as resp:
                    dst.write_bytes(resp.read())
            except Exception as e:
                print(f"  [warn] {name}: {e}", file=sys.stderr); continue
        got[r.get("name", name)] = dst
    print(f"[acquire] {len(got)} GCC finance CSVs in {RAW}", file=sys.stderr)
    return got


def zone_roman(label: str) -> str | None:
    m = re.match(r"\s*Zone\s+([IVX]+)\b", str(label))
    return m.group(1) if m and m.group(1) in ROMAN else None


def build_zone_capex(files: dict):
    f = next((p for n, p in files.items() if "Zones" in n and "1" in n and "Tools" not in n), None)
    if not f: sys.exit("zone capex CSV not found")
    zones = {}  # roman -> {capex, state_grant, heads:{}}
    with open(f, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            rm = zone_roman(row.get("Zone", ""))
            if not rm: continue
            z = zones.setdefault(rm, {"capex": 0.0, "state_grant": 0.0, "heads": {}})
            v = num(row.get(ACTUALS_COL))
            z["capex"] += v
            head = (row.get("Account Head") or "").strip()
            if re.search(r"GoTN|Specific Grants", head, re.I) or (row.get("Minor Account") or "").strip() == "Specific Grants":
                z["state_grant"] += v
            if head: z["heads"][head] = z["heads"].get(head, 0.0) + v
    return zones


def build_budget_summary(files: dict):
    f = next((p for n, p in files.items() if "summary" in n.lower()), None)
    if not f: return None
    rows = {}
    with open(f, encoding="utf-8", errors="replace") as fh:
        for row in csv.reader(fh):
            if len(row) < 3: continue
            key = (row[1] or "").strip()
            if key and key.upper() != "PARTICULARS":
                rows[key] = num(row[4])  # 2013-14 Actuals column
    return {"vintage": VINTAGE, "unit": "Rs lakh", "year": "2013-14 actuals", "lines": rows}


def main():
    files = acquire()
    zones = build_zone_capex(files)

    import geopandas as gpd
    w = gpd.read_file(WARDS)
    zcol = "zone_no" if "zone_no" in w.columns else None
    if not zcol: sys.exit("wards.geojson lacks zone_no")
    diss = w.dissolve(by=zcol).reset_index()

    feats = []
    for _, r in diss.iterrows():
        rm = str(r[zcol]).strip()
        z = zones.get(rm, {})
        capex = round(z.get("capex", 0.0), 1)
        sg = round(z.get("state_grant", 0.0), 1)
        top = sorted(z.get("heads", {}).items(), key=lambda kv: -kv[1])[:4]
        feats.append({
            "type": "Feature",
            "geometry": json.loads(gpd.GeoSeries([r.geometry]).to_json())["features"][0]["geometry"],
            "properties": {
                "zone_no": rm,
                "zone_name": (w[w[zcol] == rm]["zone_name"].iloc[0] if "zone_name" in w.columns else rm),
                "capex_lakh": capex,
                "capex_cr": round(capex / 100, 2),
                "state_grant_lakh": sg,
                "state_grant_pct": (round(sg / capex * 100) if capex else None),
                "top_heads": [{"head": h, "lakh": round(v, 1)} for h, v in top],
                "vintage": VINTAGE,
            },
        })
    OUT_LAYER.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    tot = sum(f["properties"]["capex_lakh"] for f in feats)
    sg_tot = sum(f["properties"]["state_grant_lakh"] for f in feats)
    print(f"[zone_finance] {len(feats)} zones · capex Rs {tot/100:.0f} cr (2013-14 actuals) · "
          f"state-grant share {sg_tot/tot*100:.0f}%" if tot else "[zone_finance] no capex", file=sys.stderr)

    OUT_FIN.mkdir(parents=True, exist_ok=True)
    bud = build_budget_summary(files)
    if bud:
        (OUT_FIN / "chennai_budget.json").write_text(json.dumps(bud, indent=1))
        print(f"[budget] revenue receipts Rs {bud['lines'].get('Revenue Receipts',0)/100:.0f} cr (2013-14)", file=sys.stderr)

    # provenance
    (OUT_FIN).mkdir(parents=True, exist_ok=True)
    (OUT_FIN / "sources.json").write_text(json.dumps({
        "layer": "zone_finance",
        "publisher": "Greater Chennai Corporation",
        "portal": "data.opencity.in",
        "dataset": "Great Chennai Corporation Finances",
        "dataset_url": "https://data.opencity.in/dataset/great-chennai-corporation-finances",
        "vintage": VINTAGE,
        "grain": "zone (15) — GCC publishes finance by zone, not ward",
        "processing": "sevent4: dissolve 200 wards -> 15 zones; join 2013-14 capex actuals; GoTN-grant share",
        "citation": "Greater Chennai Corporation -> data.opencity.in -> sevent4 (processed)",
    }, indent=1))
    print("[provenance] wrote source/finance/sources.json", file=sys.stderr)


if __name__ == "__main__":
    main()
