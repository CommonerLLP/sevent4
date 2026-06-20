#!/usr/bin/env python3
"""Generic city build: turn acquired source/ data into the layers/ + manifest +
city.yaml the console renders. Normalises field names across cities, merges the
councillor roster onto wards, and writes a city-level governance.json (council
status + Municipal Commissioner) for the power-map popup.

Proven on Chennai; parameterised by --city so it scales to the rest.

    python3 scripts/recipes/build_city.py --city chennai
"""
from __future__ import annotations
import argparse, csv, json, math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def wardkey(v):
    d = re.sub(r"\D", "", str(v or ""))
    return str(int(d)) if d else ""

# Per-city metadata the source data doesn't carry. Council status is from the
# corporation-data agents (notes/council-status-extra.md + CORPORATION.md files).
CITY_META = {
    "chennai": {"name": "Chennai", "state": "Tamil Nadu", "district": "Chennai",
        "council": {"status": "elected", "since": "2022-02",
            "note": "Elected GCC council since Feb 2022 (DMK-led, ~178/200). Mayor R. Priya (DMK) — Chennai's first Dalit woman mayor."}},
    "mumbai": {"name": "Mumbai", "state": "Maharashtra", "district": "Mumbai",
        "council": {"status": "elected", "since": "2026-01",
            "note": "Elected BMC council since Jan 2026 (BJP-led Maha Yuti, Mayor Ritu Tawde) — ending ~4 years of state-appointed administrator rule (Mar 2022-Jan 2026)."}},
    "bengaluru": {"name": "Bengaluru", "state": "Karnataka", "district": "Bengaluru Urban",
        "council": {"status": "administrator", "since": "2020-09",
            "note": "NO elected council since 2020. BBMP dissolved into the Greater Bengaluru Authority (5 corps, 369 wards) under IAS Chief Commissioner M. Maheshwar Rao; first elections only by Aug 2026 — an 11-year democratic gap."}},
    "kolkata": {"name": "Kolkata", "state": "West Bengal", "district": "Kolkata",
        "council": {"status": "elected", "since": "2021-12",
            "note": "Elected KMC council since Dec 2021 (TMC, 134/144). Mayoralty currently vacant — Firhad Hakim resigned June 2026."}},
    "hyderabad": {"name": "Hyderabad", "state": "Telangana", "district": "Hyderabad",
        "council": {"status": "administrator", "since": "2026-02",
            "note": "NO sitting council — the 2020 GHMC term expired Feb 2026 and GHMC was trifurcated; run by IAS Special Officer Jayesh Ranjan. Fresh polls pending."}},
    "visakhapatnam": {"name": "Visakhapatnam", "state": "Andhra Pradesh", "district": "Visakhapatnam",
        "council": {"status": "elected", "since": "2021-03",
            "note": "Elected GVMC council since 2021; mayoralty flipped to TDP/NDA (Peela Srinivasa Rao) via a no-confidence motion in Apr 2025."}},
    "bhubaneswar": {"name": "Bhubaneswar", "state": "Odisha", "district": "Khordha",
        "council": {"status": "elected", "since": "2022-03",
            "note": "Elected BMC council since Mar 2022 (BJD, 48/67). Mayor Sulochana Das — Bhubaneswar's first woman mayor."}},
    "kochi": {"name": "Kochi", "state": "Kerala", "district": "Ernakulam",
        "council": {"status": "elected", "since": "2025-12",
            "note": "Elected Kochi Corporation council since Dec 2025 (UDF, Mayor V.K. Minimol, INC) — Kerala holds local elections on time every 5 years; no administrator gap, ever."}},
    "pune": {"name": "Pune", "state": "Maharashtra", "district": "Pune",
        "council": {"status": "elected", "since": "2026-01",
            "note": "Elected PMC council since Jan 2026 (BJP, Mayor Manjusha Nagpure) — ending ~4 years of administrator rule (Maharashtra delimitation case)."}},
    "kanpur": {"name": "Kanpur", "state": "Uttar Pradesh", "district": "Kanpur Nagar",
        "council": {"status": "elected", "since": "2023-05",
            "note": "Elected Kanpur Nagar Nigam council since May 2023 (BJP, Mayor Pramila Pandey). Note: only legacy 58-ward geometry is openly available; current count is 110."}},
    "jaipur": {"name": "Jaipur", "state": "Rajasthan", "district": "Jaipur",
        "council": {"status": "administrator", "since": "2025-04",
            "note": "Administrator-run — the Heritage & Greater corporations' terms expired and the state is merging them; elections delayed on the Rajasthan OBC-report question."}},
    "delhi": {"name": "Delhi", "state": "Delhi (NCT)", "district": "Delhi",
        "council": {"status": "elected", "since": "2022-12",
            "note": "Elected MCD council since Dec 2022 — the trifurcated North/South/East corporations were re-unified into a single 250-ward Municipal Corporation of Delhi. AAP won the 2022 poll (~134/250); the mayoralty passed to the BJP (Mayor Raja Iqbal Singh, Apr 2025) after the BJP's Feb 2025 NCT assembly win. NCT special case: the MCD is only one of three civic bodies — the New Delhi Municipal Council (NDMC) and the Delhi Cantonment Board run their own areas, and most city functions sit with the GNCTD / Lieutenant-Governor, not the municipality."}},
}

# source OSM filename -> (layer id, display label, geometry kind, group, default)
OSM_LAYERS = {
    "roads": ("roads", "Roads", "line", "Mobility", False),
    "metro_lines": ("metro_lines", "Metro lines", "line", "Transit", True),
    "metro_stations": ("metro", "Metro stations", "circle", "Transit", True),
    "bus_stops": ("stops", "Bus stops", "circle", "Transit", False),
    "hospitals": ("health", "Health facilities", "circle", "Public services", False),
    "schools": ("schools", "Schools", "circle", "Public services", False),
    "libraries": ("libraries", "Libraries", "circle", "Public services", True),
    "toilets": ("toilets", "Public toilets", "circle", "Public services", False),
    "police": ("police", "Police", "circle", "Public services", False),
    "fire_stations": ("fire", "Fire & emergency", "circle", "Public services", False),
}
CIRCLE_COLOR = {
    "metro": "#5c8af2", "stops": "#9ca3ad", "health": "#49a35f", "schools": "#1e9f8f",
    "libraries": "#e0b84d", "toilets": "#46c1b4", "police": "#4d76c7", "fire": "#db4c45",
}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(obj, path):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def bbox_of(features):
    xs, ys = [], []
    def walk(c):
        if c and isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1])
        else:
            for x in c: walk(x)
    for f in features:
        walk(f["geometry"]["coordinates"])
    return [min(xs), min(ys), max(xs), max(ys)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True)
    args = ap.parse_args()
    slug = args.city
    meta = CITY_META.get(slug)
    if not meta:
        raise SystemExit(f"add {slug} to CITY_META first")
    city = ROOT / "data" / "cities" / slug
    src = city / "source"
    bnd = src / "boundaries"
    layers = city / "layers"
    layers.mkdir(parents=True, exist_ok=True)

    # ── wards: normalise + merge councillors ──────────────────────────────
    wards = load(bnd / "wards.geojson")
    roster = {}
    rpath = src / "corporation" / "councillors.csv"
    if rpath.exists():
        with rpath.open(encoding="utf-8") as fh:
            rd = csv.DictReader(fh)
            cols = {c.lower().strip(): c for c in (rd.fieldnames or [])}
            def pick(*names):
                for n in names:
                    if n in cols:
                        return cols[n]
                return None
            wcol = pick("ward_no", "ward", "ward_number", "wardno", "ward_id", "division")
            ncol = pick("councillor_name", "corporator_name", "name", "member_name", "councillor")
            pcol = pick("party")
            phcol = pick("phone", "contact", "mobile", "phone_number")
            for row in rd:
                k = wardkey(row.get(wcol, "")) if wcol else ""
                if not k:
                    continue
                roster[k] = {
                    "name": (row.get(ncol) or "").strip() if ncol else "",
                    "party": (row.get(pcol) or "").strip() if pcol else "",
                    "phone": (row.get(phcol) or "").strip() if phcol else "",
                }
    WK = ("ward_no", "WARD_NO", "Ward_No", "ward", "WARD", "no", "NO", "wardno", "Name", "name")
    for ft in wards["features"]:
        p = ft["properties"]
        wn = str(next((p[k] for k in WK if str(p.get(k) or "").strip()), "")).strip()
        zone = p.get("zone_name") or p.get("ZONE") or p.get("zone") or p.get("CIRCLE") or ""
        if "Name" not in p:
            p["Name"] = f"Ward {wn}" + (f" · {zone}" if zone else "")
        r = roster.get(wardkey(wn))
        if r and r["name"]:
            p["councillor_count"] = 1
            p["councillors"] = r["name"]
            p["councillor_parties"] = r["party"]
            p["councillor_phones"] = r["phone"]
    dump(wards, layers / "wards.geojson")

    # ── ACs / PCs: normalise field names, keep MLA/MP ─────────────────────
    acs = load(bnd / "acs.geojson")
    for ft in acs["features"]:
        p = ft["properties"]
        p.setdefault("ac_name", p.get("AC_NAME") or p.get("ac_name") or "")
        p.setdefault("office", "MLA")
    dump(acs, layers / "acs.geojson")

    pcs = load(bnd / "pcs.geojson")
    for ft in pcs["features"]:
        p = ft["properties"]
        p.setdefault("pc_name", p.get("PC_NAME") or p.get("pc_name") or "")
        p.setdefault("office", "MP")
    dump(pcs, layers / "pcs.geojson")

    if (bnd / "districts.geojson").exists():
        dist = load(bnd / "districts.geojson")
        for ft in dist["features"]:
            ft["properties"].setdefault("district", ft["properties"].get("DISTRICT", ""))
        dump(dist, layers / "districts.geojson")

    # ── OSM layers: copy through ──────────────────────────────────────────
    present_osm = []
    for fname, spec in OSM_LAYERS.items():
        srcf = src / "osm" / f"{fname}.geojson"
        if srcf.exists():
            data = load(srcf)
            if data.get("features"):
                dump(data, layers / f"{spec[0]}.geojson")
                present_osm.append(spec)

    # ── city.yaml ─────────────────────────────────────────────────────────
    b = bbox_of(wards["features"])
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    utm = 32600 + int((cx + 180) / 6) + 1
    (city / "city.yaml").write_text(
        f"id: {slug}\nname: {meta['name']}\ncountry: India\nstate: {meta['state']}\n"
        f"center: [{cx:.4f}, {cy:.4f}]\nbbox: [{b[0]:.4f}, {b[1]:.4f}, {b[2]:.4f}, {b[3]:.4f}]\n"
        f"crs_metric: EPSG:{utm}\nlayers_dir: data/cities/{slug}/layers\n"
        f"source_dir: data/cities/{slug}/source\noutputs_dir: public/cities/{slug}\n",
        encoding="utf-8",
    )

    # ── governance.json (city-level, for the power-map popup) ─────────────
    officers = load(src / "officers.json") if (src / "officers.json").exists() else []
    def officer(role):
        for o in officers:
            if role.lower() in (o.get("role") or "").lower():
                return o
        return {}
    mc = officer("municipal commissioner") or officer("commissioner")
    cp = officer("police")
    dump({
        "city": meta["name"], "council": meta["council"],
        "municipal_commissioner": mc.get("name", ""), "mc_service": mc.get("service", ""),
        "police_commissioner": cp.get("name", ""), "pc_service": cp.get("service", ""),
    }, layers / "governance.json")

    # ── layer_manifest.json ───────────────────────────────────────────────
    manifest = {"layers": []}
    manifest["layers"].append({
        "id": "wards", "label": "Wards", "file": "wards.geojson", "kind": "fill",
        "group": "Civic baseline", "default": True, "outline": True,
        "popup": ["Name", "councillors", "councillor_parties", "councillor_phones",
                   "population_2020", "pop_density_km2", "ward_coverage"],
        "paint": {"fill-color": "#1f6f8b", "fill-opacity": 0.18},
    })
    if (layers / "districts.geojson").exists():  # only manifest districts when the layer was produced
        manifest["layers"].append({
            "id": "districts", "label": "District boundary", "file": "districts.geojson",
            "kind": "line", "group": "Civic baseline", "default": True, "popup": ["district"],
            "paint": {"line-color": "#c9c2b3", "line-width": 1.3, "line-opacity": 0.55},
        })
    manifest["layers"].append({
        "id": "pcs", "label": "Parliament constituencies", "file": "pcs.geojson",
        "kind": "line", "group": "Public jurisdictions", "default": True,
        "popup": ["pc_name", "office", "representative", "party"],
        "paint": {"line-color": "#d6a946", "line-width": 2.0, "line-opacity": 0.78},
    })
    manifest["layers"].append({
        "id": "acs", "label": "Assembly constituencies", "file": "acs.geojson",
        "kind": "line", "group": "Public jurisdictions", "default": True,
        "popup": ["ac_name", "office", "representative", "party"],
        "paint": {"line-color": "#5c8af2", "line-width": 1.6, "line-opacity": 0.82},
    })
    for lid, label, kind, group, default in present_osm:
        if kind == "line":
            paint = {"line-color": "#dc4c4c" if lid == "metro_lines" else "#58606d",
                     "line-width": 2.4 if lid == "metro_lines" else 0.5,
                     "line-opacity": 0.9 if lid == "metro_lines" else 0.4}
        else:
            paint = {"circle-color": CIRCLE_COLOR.get(lid, "#9ca3ad"), "circle-radius": 3.2,
                     "circle-stroke-color": "#101318", "circle-stroke-width": 0.6, "circle-opacity": 0.85}
        manifest["layers"].append({
            "id": lid, "label": label, "file": f"{lid}.geojson", "kind": kind,
            "group": group, "default": default, "popup": ["name"], "paint": paint,
        })
    dump(manifest, layers / "layer_manifest.json")

    n_council = sum(1 for f in wards["features"] if f["properties"].get("councillors"))
    print(f"{slug}: {len(wards['features'])} wards ({n_council} with councillor), "
          f"{len(acs['features'])} ACs, {len(pcs['features'])} PCs, {len(present_osm)} OSM layers")
    print(f"  city.yaml + layer_manifest.json + governance.json written to {layers}")
    print(f"  commissioner: {mc.get('name','?')} | council: {meta['council']['status']} since {meta['council']['since']}")


if __name__ == "__main__":
    main()
