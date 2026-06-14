#!/usr/bin/env python3
"""Spatial analysis of the Delhi Public Library fixed network.

Inputs (all on feat/delhi):
  - data/cities/delhi/derived/geocoding/dpl_geocoded.csv  (22 located fixed libraries:
    5 DPL/official-verified + 17 Nominatim-approx; 13 unlocated)
  - data/cities/delhi/layers/{districts,wards,metro,metro_lines}.geojson

Outputs:
  - data/cities/delhi/layers/dpl_libraries.geojson  (authoritative DPL fixed network
    for the console — distinct from OSM's partial `libraries`)
  - docs/figures/figD3_dpl_walk_access.png  (ward distance-to-nearest-DPL choropleth)
  - docs/figures/figD4_dpl_transit_siting.png (DPL vs Metro network)
  - prints summary stats for the paper

Honest framing: 5 of 22 coordinates are verified, 17 are approximate; the maps show
the FIXED network only (mobile service points are not fixed access). Treat the
numbers as indicative of sparsity, not survey-grade.

Run: .venv/bin/python scripts/recipes/delhi/build_library_spatial.py
"""
from __future__ import annotations
import json
import math
import pathlib

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Point

ROOT = pathlib.Path(__file__).resolve().parents[3]
LAYERS = ROOT / "data/cities/delhi/layers"
GEO = ROOT / "data/cities/delhi/derived/geocoding/dpl_geocoded.csv"
FIG = ROOT / "docs/figures"
FIG.mkdir(parents=True, exist_ok=True)
M = "EPSG:32643"

INK, BLUE, MUTED, RULE, ALERT, GREEN = "#172126", "#1B4E6B", "#66737A", "#D6DEE2", "#B0412B", "#1f9e6b"
mpl.rcParams.update({"font.family": "Helvetica", "font.size": 10.5,
                     "axes.edgecolor": MUTED, "figure.dpi": 150})


def load_dpl() -> gpd.GeoDataFrame:
    df = pd.read_csv(GEO)
    df = df[df["latitude"].notna() & df["longitude"].notna()].copy()
    if "is_fixed" in df.columns:            # analyse the fixed network only
        df = df[df["is_fixed"]].copy()
    df["verified"] = df["geocode_confidence"].isin(
        ["verified", "google_verified", "dpl_maps_pin"])
    g = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])],
                         crs="EPSG:4326")
    return g


def main() -> None:
    dpl = load_dpl()
    hi = int(dpl["geocode_confidence"].isin(["verified", "google_verified", "dpl_maps_pin"]).sum())
    approx = len(dpl) - hi
    pins = int(dpl["geocode_confidence"].eq("dpl_maps_pin").sum())
    conf_note = (f"Coordinates: {hi} verified/rooftop ({pins} from DPL's own map links), "
                 f"{approx} approximate. Mobile service points excluded.")
    districts = gpd.read_file(LAYERS / "districts.geojson").to_crs(4326)
    wards = gpd.read_file(LAYERS / "wards.geojson").to_crs(4326)
    metro = gpd.read_file(LAYERS / "metro.geojson").to_crs(4326)
    metro_lines = gpd.read_file(LAYERS / "metro_lines.geojson").to_crs(4326)

    # ---- authoritative DPL layer for the console ----
    keep = ["name", "location_type", "zone", "geocode_confidence"]
    out = dpl[[c for c in keep if c in dpl.columns] + ["geometry"]].copy()
    out["Name"] = out["name"]
    out.to_file(LAYERS / "dpl_libraries.geojson", driver="GeoJSON")
    _register_dpl_layer()

    # ---- metric projections ----
    dpl_m = dpl.to_crs(M)
    metro_m = metro.to_crs(M)
    wards_m = wards.to_crs(M)

    # ---- transit siting: distance to nearest Metro station ----
    nearest = dpl_m.geometry.apply(lambda p: metro_m.distance(p).min())
    dpl["metro_m"] = nearest.values
    within800 = int((nearest <= 800).sum())
    within400 = int((nearest <= 400).sum())

    # ---- walk access: each ward rep-point distance to nearest fixed DPL ----
    wpt = wards_m.copy()
    wpt["geometry"] = wpt.representative_point()
    wd = wpt.geometry.apply(lambda p: dpl_m.distance(p).min())
    wards_m["dpl_km"] = (wd / 1000.0).values
    wards["dpl_km"] = wards_m["dpl_km"].values
    within_1200 = int((wards_m["dpl_km"] <= 1.2).sum())
    n_wards = len(wards_m)

    # ---- per-district counts ----
    dpl4326 = dpl.to_crs(4326)
    joined = gpd.sjoin(dpl4326, districts[["district", "geometry"]], how="left", predicate="within")
    per_district = joined.groupby("district").size().sort_values(ascending=False)

    # ---- multi-radius reach + city-area coverage ----
    reach = {f"wards_within_{int(r*1000)}m": int((wards_m["dpl_km"] <= r).sum())
             for r in (0.8, 1.2, 2.0, 3.0)}
    nct_poly = wards_m.union_all()
    area_cov_1200 = round(100 * dpl_m.geometry.buffer(1200).union_all()
                          .intersection(nct_poly).area / nct_poly.area, 1)

    # ---- centroid / dispersion (how core-clustered is the network?) ----
    cx, cy = float(dpl_m.geometry.x.mean()), float(dpl_m.geometry.y.mean())
    nct_c = nct_poly.centroid
    centroid_offset_km = round(math.hypot(cx - nct_c.x, cy - nct_c.y) / 1000.0, 2)
    bearing = round((math.degrees(math.atan2(cx - nct_c.x, cy - nct_c.y)) + 360) % 360)
    std_dist_km = round(math.sqrt((((dpl_m.geometry.x - cx) ** 2 +
                                    (dpl_m.geometry.y - cy) ** 2).mean())) / 1000.0, 2)

    # ---- bus (GTFS) proximity — uses the 10k+ DTC/cluster stops if present ----
    bus_stats = {}
    bus_f = LAYERS / "bus_stops.geojson"
    if bus_f.exists():
        bus_m = gpd.read_file(bus_f).to_crs(M)
        bnear = dpl_m.geometry.apply(lambda p: bus_m.distance(p).min())
        bus_stats = {"dpl_within_400m_bus": int((bnear <= 400).sum()),
                     "dpl_within_200m_bus": int((bnear <= 200).sum()),
                     "bus_stops_total": len(bus_m)}
    # any-transit reach: within 400m of a metro station OR a bus stop
    any_transit_400 = int(((dpl["metro_m"] <= 400) |
                           (bnear.values <= 400 if bus_stats else False)).sum())

    # ---- figD3: ward walk-access choropleth ----
    fig, ax = plt.subplots(figsize=(7.4, 7.0))
    wards.to_crs(4326).plot(ax=ax, column="dpl_km", cmap="YlOrRd", vmin=0, vmax=12,
                            edgecolor="#ffffff", linewidth=0.15, legend=True,
                            legend_kwds={"label": "Distance to nearest fixed DPL (km)", "shrink": 0.6})
    districts.boundary.plot(ax=ax, color=INK, linewidth=0.6)
    dpl.plot(ax=ax, color="#11304a", markersize=22, marker="o", edgecolor="white", linewidth=0.6, zorder=5)
    ax.set_title("Delhi: how far is the nearest fixed public library?", color=INK, fontsize=12, loc="left")
    ax.annotate(f"{within_1200} of {n_wards} wards lie within a 1.2 km (≈15-min) walk of one of the "
                f"{len(dpl)} located fixed DPL branches.\n{conf_note}",
                xy=(0.0, -0.06), xycoords="axes fraction", fontsize=7.6, color=MUTED, va="top")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(FIG / "figD3_dpl_walk_access.png", bbox_inches="tight")
    plt.close(fig)

    # ---- figD4: DPL vs Metro network ----
    fig, ax = plt.subplots(figsize=(7.4, 7.0))
    districts.boundary.plot(ax=ax, color=RULE, linewidth=0.8)
    metro_lines.to_crs(4326).plot(ax=ax, color="#c9603a", linewidth=0.7, alpha=0.7, zorder=2)
    metro.plot(ax=ax, color=MUTED, markersize=4, alpha=0.5, zorder=3)
    near = dpl[dpl["metro_m"] <= 800]
    far = dpl[dpl["metro_m"] > 800]
    far.plot(ax=ax, color=ALERT, markersize=34, marker="o", edgecolor="white", linewidth=0.6, zorder=5, label=">800 m from Metro")
    near.plot(ax=ax, color=GREEN, markersize=34, marker="o", edgecolor="white", linewidth=0.6, zorder=6, label="≤800 m from Metro")
    ax.legend(loc="lower left", fontsize=8, frameon=False)
    ax.set_title("Delhi: are the libraries on the Metro network?", color=INK, fontsize=12, loc="left")
    ax.annotate(f"{within800} of {len(dpl)} fixed DPL branches are within 800 m of a Metro station "
                f"({within400} within 400 m). Metro: {len(metro)} stations, {len(metro_lines)} OSM track segments.",
                xy=(0.0, -0.06), xycoords="axes fraction", fontsize=7.6, color=MUTED, va="top")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(FIG / "figD4_dpl_transit_siting.png", bbox_inches="tight")
    plt.close(fig)

    stats = {
        "located_fixed_dpl": len(dpl), "high_confidence": hi, "approximate": approx,
        "source_verified": int(dpl["verified"].sum()),
        "wards_total": n_wards, "wards_within_1200m": within_1200,
        "wards_within_1200m_pct": round(100 * within_1200 / n_wards, 1),
        "median_ward_km_to_dpl": round(float(wards_m["dpl_km"].median()), 2),
        "reach_by_radius": reach, "city_area_pct_within_1200m": area_cov_1200,
        "centroid_offset_from_city_km": centroid_offset_km, "centroid_bearing_deg": bearing,
        "network_std_distance_km": std_dist_km,
        "dpl_within_800m_metro": within800, "dpl_within_400m_metro": within400,
        "dpl_within_400m_any_transit": any_transit_400, **bus_stats,
        "per_district": per_district.to_dict(),
    }
    print(json.dumps(stats, indent=2))
    (LAYERS / "_dpl_spatial_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")


def _register_dpl_layer() -> None:
    mp = LAYERS / "layer_manifest.json"
    m = json.loads(mp.read_text())
    # the authoritative DPL fixed network IS Delhi's libraries layer — present it
    # like every other city: id "libraries", label "Libraries", standard yellow circle.
    entry = {"id": "libraries", "label": "Libraries", "file": "dpl_libraries.geojson",
             "kind": "circle", "group": "Public services", "default": True,
             "popup": ["Name", "location_type", "zone", "geocode_confidence"],
             "paint": {"circle-color": "#e0b84d", "circle-radius": 3.2, "circle-stroke-color": "#101318",
                       "circle-stroke-width": 0.6, "circle-opacity": 0.85}}
    ids = {l["id"] for l in m["layers"]}
    m["layers"] = [entry if l["id"] == "libraries" else l for l in m["layers"]] if "libraries" in ids \
        else m["layers"] + [entry]
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
