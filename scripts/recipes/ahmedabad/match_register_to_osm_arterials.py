#!/usr/bin/env python3
"""Match the AMC resurfacing register's road descriptions to NAMED OSM
arterials (the only redistributable road geometry — ODbL), and emit a GeoJSON
of those arterials weighted by how often the register repaves them.

This is the LEGITIMATE, partial "see the roads" layer: it draws the major named
roads that recur in the registers. The bulk of register rows are local
society-to-society lanes that name no mappable road — those stay ward-level
(see resurfacing_by_ward.geojson). Honest coverage is reported at the end.

Inputs:
  resurfaced_registers/roads_resurfaced_rows.csv   (1,683 work-orders)
  ../roads/osm_named_roads.json                    (Overpass: named ways + geom)
Output:
  arterials_recurrence.geojson
"""

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[3] / "data/cities/ahmedabad/source/budget/roads"
ROWS = BASE / "resurfaced_registers/roads_resurfaced_rows.csv"
OSM = BASE.parent.parent / "roads/osm_named_roads.json"   # data/.../source/roads/
OUT = BASE / "arterials_recurrence.geojson"

# Gazetteer: canonical arterial -> (OSM-name regex, register-text regex across
# the three encodings: legacy-font / unicode-Gujarati / latin+numerals).
ARTERIALS = {
    "SP / Sardar Patel Ring Road": (
        r"sardar patel ring|s p ring",
        r"yum\.?ve\.?\s*hekd|એસ\.?પી\.?\s*રӄग|એસપી\s*રӄग|સરદાર\s*પટ°લ\s*રӄग|s\.?p\.?\s*ring",
    ),
    "132 Ft Ring Road": (
        r"132",
        r"132\s*(?:Vwx|ફ|ft|feet)|૧૩૨|132\s*ft",
    ),
    "SG Highway (Sarkhej-Gandhinagar)": (
        r"sg highway|sarkhej-gandhinagar",
        r"yum\.?S\.?\s*ntRJu|એસ\.?ĥ\.?\s*હાઈ|એસĥ\s*હાઈ|sg\s*high|mhFus.{0,6}dtk^eldh",
    ),
    "Ashram Road": (
        r"ashram road|asharam ashram",
        r"yt©b\s*htuz|આĖમ\s*રોડ|ashram\s*r",
    ),
    "120 Ft Ring Road": (
        r"120 feet ring",
        r"120\s*(?:Vwx|ફ|ft|feet)|૧૨૦",
    ),
    "Naroda Road / Nava Naroda Road": (
        r"naroda road|nava naroda",
        r"lhtuzt\s*htuz|નરોડા\s*રોડ|નવા\s*નરોડા",
    ),
    "Naroda-Dehgam Road": (
        r"naroda-dehgam|dehgam road",
        r"œnudtb\s*htuz|દહેગામ\s*રોડ",
    ),
}


def main():
    rows = list(csv.DictReader(open(ROWS)))
    osm = json.load(open(OSM))["elements"]

    # count register references per arterial (and which contractors/years)
    refs = defaultdict(lambda: {"count": 0, "years": set(), "contractors": Counter()})
    matched_rows = 0
    for r in rows:
        d = r["road_desc_raw"]
        hit = False
        for art, (_, regpat) in ARTERIALS.items():
            if re.search(regpat, d, re.I):
                refs[art]["count"] += 1
                refs[art]["years"].add(r["register_year"])
                if r["contractor"]:
                    refs[art]["contractors"][r["contractor"]] += 1
                hit = True
        if hit:
            matched_rows += 1

    # attach geometry: every OSM named way whose name matches an arterial's
    # OSM-name regex inherits that arterial's register weight
    features = []
    osm_matched = 0
    for el in osm:
        name = el.get("tags", {}).get("name", "")
        geom = el.get("geometry")
        if not geom:
            continue
        for art, (osmpat, _) in ARTERIALS.items():
            if re.search(osmpat, name, re.I) and refs[art]["count"] > 0:
                osm_matched += 1
                info = refs[art]
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString",
                                 "coordinates": [[p["lon"], p["lat"]] for p in geom]},
                    "properties": {
                        "arterial": art,
                        "osm_name": name,
                        "register_references": info["count"],
                        "years_repaved": len(info["years"]),
                        "top_contractor": (info["contractors"].most_common(1)[0][0]
                                           if info["contractors"] else ""),
                    },
                })
                break

    fc = {"type": "FeatureCollection", "features": features,
          "_meta": {
              "what": "AMC resurfacing-register road descriptions matched to NAMED OSM arterials (ODbL). Partial by design: only register rows that cite a named arterial. Society-lane stretches are not drawable from open data — see resurfacing_by_ward.geojson.",
              "register_rows_total": len(rows),
              "register_rows_matched_to_an_arterial": matched_rows,
              "osm_arterial_segments_drawn": osm_matched,
          }}
    OUT.write_text(json.dumps(fc))
    print(f"register rows citing a named arterial: {matched_rows}/{len(rows)} "
          f"({100*matched_rows//len(rows)}%)")
    print(f"OSM arterial line-segments drawn: {osm_matched}")
    print("per-arterial register references:")
    for art, info in sorted(refs.items(), key=lambda kv: -kv[1]["count"]):
        if info["count"]:
            print(f"  {info['count']:4d}  ({len(info['years'])} yrs)  {art}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
