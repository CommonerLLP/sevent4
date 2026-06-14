#!/usr/bin/env python3
"""Pass-1 boundary spine for Bengaluru — acquire + convert the three representative cuts.

Downloads the city-specific KMLs from data.opencity.in, converts to GeoJSON, normalises
field names to the build_city.py source contract, and writes provenance. Lands everything
in the in-repo gitignored data/cities/bengaluru/source/boundaries/.

Outputs:
  wards.geojson          GBA 369-ward Dec-2025 (current unelected-GBA — DEFAULT display layer)
  wards_bbmp198.geojson  BBMP 2023 final wards (198 — historical join layer for work-orders)
  acs.geojson            Bengaluru assembly constituencies (ECI/KSEC)
  pcs.geojson            Bengaluru Urban parliamentary constituencies (ECI)
  sources.json           machine-readable provenance per layer
  CREDITS.md             human-readable credit (publisher -> OpenCity -> sevent4)

Run:  .venv/bin/python scripts/recipes/bengaluru/acquire_boundaries.py
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen, Request

import geopandas as gpd

ROOT = Path(__file__).resolve.parents[3]
OUT = ROOT / "data" / "cities" / "bengaluru" / "source" / "boundaries"
RAW = OUT / "_raw"
UA = {"User-Agent": "sevent4-atlas/1.0 (74th-amendment atlas)"}

# layer_id -> (target geojson, source dataset page, direct resource URL, publisher, label)
SPINE = {
    "wards": {
        "target": "wards.geojson",
        "dataset": "https://data.opencity.in/dataset/gba-wards-delimitation-2025",
        "resource": "https://data.opencity.in/dataset/863209cb-4ced-4f51-b5c5-156939c50922/resource/9013d656-8051-4e2d-9648-46efd0d86d3d/download/gba-369-wards-december-2025.kml",
        "publisher": "Greater Bengaluru Authority (GBA)",
        "label": "GBA Final Wards (369) — December 2025",
    },
    "wards_bbmp198": {
        "target": "wards_bbmp198.geojson",
        "dataset": "https://data.opencity.in/dataset/bbmp-wards-delimitation-2023",
        "resource": "https://data.opencity.in/dataset/7b492849-a5cb-439b-89e9-e03522055e6a/resource/7857d752-dda4-4e5e-b9e6-53146372f86b/download/b272c5b2-3e66-4b0f-a59f-35ec7b4caa1e.kml",
        "publisher": "Bruhat Bengaluru Mahanagara Palike (BBMP)",
        "label": "BBMP Final Wards Map 2023 (198) — historical join layer",
    },
    "acs": {
        "target": "acs.geojson",
        "dataset": "https://data.opencity.in/dataset/karnataka-and-bengaluru-assembly-constituency-maps",
        "resource": "https://data.opencity.in/dataset/f80a1ff2-a1f2-442a-aff0-f332acd14ae6/resource/c1c04138-0eeb-4e5f-b1ef-6932dbcd23c0/download/28add4af-0ee5-4f13-9c64-0e5b3927c321.kml",
        "publisher": "Karnataka State Election Commission / ECI",
        "label": "Bengaluru Assembly Constituencies Map",
    },
    "pcs": {
        "target": "pcs.geojson",
        "dataset": "https://data.opencity.in/dataset/karnataka-and-bengaluru-parliamentary-constituency-maps",
        "resource": "https://data.opencity.in/dataset/f4eea943-d4ef-484a-a636-8de9ca0b7497/resource/4ae8e478-8cbc-45ca-be75-e7e32938d11a/download/fb4523e8-985d-4f0a-815e-025504c3b9a9.kml",
        "publisher": "Election Commission of India (ECI)",
        "label": "Bengaluru Urban Parliamentary Constituencies Map",
    },
}


def fetch(url: str, dest: Path) -> int:
    req = Request(url, headers=UA)
    with urlopen(req, timeout=120) as r:
        data = r.read
    dest.write_bytes(data)
    return len(data)


def main -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    provenance = []

    for lid, spec in SPINE.items:
        kml = RAW / f"{lid}.kml"
        n = fetch(spec["resource"], kml)
        gdf = gpd.read_file(kml)
        # KML always EPSG:4326; ensure it
        if gdf.crs is None:
            gdf.set_crs(4326, inplace=True)
        gdf = gdf.to_crs(4326)
        # normalise the field the builder keys on
        if lid == "acs":
            if "ac_name" not in gdf.columns:
                gdf["ac_name"] = gdf.get("Name", "")
            gdf["office"] = "MLA"
        elif lid == "pcs":
            if "pc_name" not in gdf.columns:
                gdf["pc_name"] = gdf.get("Name", "")
            gdf["office"] = "MP"
        out = OUT / spec["target"]
        gdf.to_file(out, driver="GeoJSON")
        feats = len(gdf)
        cols = [c for c in gdf.columns if c != "geometry"]
        print(f"[{lid}] {feats} features -> {spec['target']}  ({n/1024:.0f} KB KML)  cols={cols}")
        provenance.append({
            "layer": lid,
            "file": spec["target"],
            "features": feats,
            "publisher_org": spec["publisher"],
            "opencity_dataset": spec["dataset"],
            "resource_url": spec["resource"],
            "format_source": "KML",
            "processor": "sevent4 (scripts/recipes/bengaluru/acquire_boundaries.py)",
            "retrieved": "2026-06-11",
        })

    (OUT / "sources.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False))

    # human-readable credit
    lines = ["# Bengaluru boundary spine — sources & credit\n",
             "_Acquired from data.opencity.in. Cite: **publisher → OpenCity → sevent4 (processed)**._\n"]
    for p in provenance:
        lines.append(f"- **{p['layer']}** (`{p['file']}`, {p['features']} features) — "
                     f"{p['publisher_org']} · published on OpenCity · {p['opencity_dataset']}")
    (OUT / "CREDITS.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote sources.json + CREDITS.md to {OUT}")


if __name__ == "__main__":
    main
