"""Geospatial + matplotlib + filesystem adapter for the Delhi DPL fixed-network
spatial analysis: load geocoded libraries and base layers, compute the
walk-access / transit-siting / dispersion metrics, render the two figures, and
write the DPL layer, manifest entry, and stats JSON.
"""
from __future__ import annotations

import json
import math
import textwrap
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from mpl_toolkits.axes_grid1 import make_axes_locatable
from shapely.geometry import Point

from sevent4.domain.delhi_library_spatial import compass_label

M = "EPSG:32643"
MIN_PER_KM = 12.5   # walk-minutes per km (1.2 km ≈ 15-min walk); unifies the scale with the Ahmedabad map
WALK_VMAX = 80      # shared colour scale ceiling, walk-minutes, both cities
INK, BLUE, MUTED, RULE, ALERT, GREEN = "#172126", "#1B4E6B", "#66737A", "#D6DEE2", "#B0412B", "#1f9e6b"
mpl.rcParams.update({"font.family": "Helvetica", "font.size": 10.5,
                     "axes.edgecolor": MUTED, "figure.dpi": 150})

_VERIFIED = ["verified", "google_verified", "dpl_maps_pin"]


@dataclass
class SpatialAnalysis:
    dpl: gpd.GeoDataFrame
    wards: gpd.GeoDataFrame
    districts: gpd.GeoDataFrame
    metro: gpd.GeoDataFrame
    metro_lines: gpd.GeoDataFrame
    libc: object
    cityc: object
    bus_path: Path
    metrics: dict


class DelhiLibrarySpatial:
    def __init__(self, geo_csv: Path, layers_dir: Path, fig_dir: Path) -> None:
        self.geo_csv = Path(geo_csv)
        self.layers = Path(layers_dir)
        self.fig = Path(fig_dir)
        self.fig.mkdir(parents=True, exist_ok=True)

    def load_dpl(self) -> gpd.GeoDataFrame:
        df = pd.read_csv(self.geo_csv)
        df = df[df["latitude"].notna() & df["longitude"].notna()].copy()
        if "is_fixed" in df.columns:            # analyse the fixed network only
            df = df[df["is_fixed"]].copy()
        df["verified"] = df["geocode_confidence"].isin(_VERIFIED)
        return gpd.GeoDataFrame(
            df, geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])],
            crs="EPSG:4326")

    def load_base_layers(self) -> dict:
        return {
            "districts": gpd.read_file(self.layers / "districts.geojson").to_crs(4326),
            "wards": gpd.read_file(self.layers / "wards.geojson").to_crs(4326),
            "metro": gpd.read_file(self.layers / "metro.geojson").to_crs(4326),
            "metro_lines": gpd.read_file(self.layers / "metro_lines.geojson").to_crs(4326),
        }

    def write_dpl_layer(self, dpl: gpd.GeoDataFrame) -> None:
        keep = ["name", "location_type", "zone", "geocode_confidence"]
        out = dpl[[c for c in keep if c in dpl.columns] + ["geometry"]].copy()
        out["Name"] = out["name"]
        out.to_file(self.layers / "dpl_libraries.geojson", driver="GeoJSON")

    def read_manifest(self) -> dict:
        return json.loads((self.layers / "layer_manifest.json").read_text())

    def write_manifest(self, manifest: dict) -> None:
        (self.layers / "layer_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def analyse(self, dpl: gpd.GeoDataFrame, base: dict) -> SpatialAnalysis:
        districts, wards = base["districts"], base["wards"]
        metro, metro_lines = base["metro"], base["metro_lines"]

        hi = int(dpl["geocode_confidence"].isin(_VERIFIED).sum())
        approx = len(dpl) - hi
        pins = int(dpl["geocode_confidence"].eq("dpl_maps_pin").sum())

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
        bus_stats: dict = {}
        dpl["bus_m"] = float("inf")
        bus_f = self.layers / "bus_stops.geojson"
        if bus_f.exists():
            bus_m = gpd.read_file(bus_f).to_crs(M)
            dpl["bus_m"] = dpl_m.geometry.apply(lambda p: bus_m.distance(p).min()).values
            bus_stats = {"dpl_within_400m_bus": int((dpl["bus_m"] <= 400).sum()),
                         "dpl_within_200m_bus": int((dpl["bus_m"] <= 200).sum()),
                         "bus_stops_total": len(bus_m)}
        any_transit_400 = int(((dpl["metro_m"] <= 400) | (dpl["bus_m"] <= 400)).sum())

        centres = gpd.GeoSeries([Point(cx, cy), nct_c], crs=M).to_crs(4326)
        libc, cityc = centres.iloc[0], centres.iloc[1]

        metrics = {
            "located": len(dpl), "hi": hi, "approx": approx, "pins": pins,
            "source_verified": int(dpl["verified"].sum()),
            "n_wards": n_wards, "within_1200": within_1200,
            "median_ward_km": round(float(wards_m["dpl_km"].median()), 2),
            "reach": reach, "area_cov_1200": area_cov_1200,
            "centroid_offset_km": centroid_offset_km, "bearing": bearing, "std_dist_km": std_dist_km,
            "within800": within800, "within400": within400, "any_transit_400": any_transit_400,
            "bus_stats": bus_stats, "per_district": per_district.to_dict(),
            "compass": compass_label(bearing),
        }
        return SpatialAnalysis(dpl=dpl, wards=wards, districts=districts, metro=metro,
                               metro_lines=metro_lines, libc=libc, cityc=cityc,
                               bus_path=bus_f, metrics=metrics)

    def render_walk_access(self, a: SpatialAnalysis, conf_note: str) -> None:
        m = a.metrics
        fig, ax = plt.subplots(figsize=(7.4, 7.0))
        _div = make_axes_locatable(ax)
        cax = _div.append_axes("right", size="3.5%", pad=0.2)
        _sp = _div.append_axes("left", size="3.5%", pad=0.2)   # balances the colorbar so the map centres
        _sp.set_xticks([]); _sp.set_yticks([])
        for _s in _sp.spines.values():
            _s.set_visible(False)
        a.wards.assign(walk_min=a.wards["dpl_km"] * MIN_PER_KM).to_crs(4326).plot(
                                  ax=ax, column="walk_min", cmap="YlOrRd", vmin=0, vmax=WALK_VMAX,
                                  edgecolor="#ffffff", linewidth=0.15, legend=True, cax=cax,
                                  legend_kwds={"label": "Walk minutes to nearest library (ward centroid)"})
        a.districts.boundary.plot(ax=ax, color=INK, linewidth=0.6)
        a.dpl.plot(ax=ax, color="#11304a", markersize=22, marker="o", edgecolor="white", linewidth=0.6, zorder=5)
        # the lopsided network: library mean-centre (star) vs city centroid (plus), with
        # the skew line — visualises the ~7 km ENE pull into the old core.
        ax.plot([a.cityc.x, a.libc.x], [a.cityc.y, a.libc.y], color="#11304a", lw=1.1, ls=(0, (4, 3)), zorder=6)
        ax.scatter([a.cityc.x], [a.cityc.y], s=90, marker="P", color=MUTED, edgecolor="white", linewidth=0.8, zorder=7)
        ax.scatter([a.libc.x], [a.libc.y], s=150, marker="*", color="#edc233", edgecolor="#1a1a1a", linewidth=0.7, zorder=8)
        ax.set_title("Delhi: how far is the nearest fixed public library?", color=INK, fontsize=12, loc="left")
        ax.annotate(textwrap.fill(
                        f"{m['within_1200']} of {m['n_wards']} wards lie within a 1.2 km (≈15-min) walk of one of the "
                        f"{m['located']} located fixed DPL branches — barely {m['area_cov_1200']:.0f}% of the city's land. "
                        f"The network's mean centre (★) sits ~{m['centroid_offset_km']:.0f} km {m['compass']} of the city "
                        f"centre (✚), pulled into the old core.", 64) + f"\n{textwrap.fill(conf_note, 64)}",
                    xy=(0.0, -0.07), xycoords="axes fraction", fontsize=7.4, color=MUTED, va="top")
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(self.fig / "figD3_dpl_walk_access.png", bbox_inches="tight")
        plt.close(fig)

    def render_transit_siting(self, a: SpatialAnalysis) -> None:
        m = a.metrics
        fig, ax = plt.subplots(figsize=(7.4, 7.0))
        _div = make_axes_locatable(ax)
        cax = _div.append_axes("right", size="3.5%", pad=0.2)
        _sp = _div.append_axes("left", size="3.5%", pad=0.2)   # balances the colorbar so the map centres
        _sp.set_xticks([]); _sp.set_yticks([])
        for _s in _sp.spines.values():
            _s.set_visible(False)
        # same walk-minutes heat surface as the access map, so the two Delhi maps match
        a.wards.assign(walk_min=a.wards["dpl_km"] * MIN_PER_KM).to_crs(4326).plot(
                                  ax=ax, column="walk_min", cmap="YlOrRd", vmin=0, vmax=WALK_VMAX,
                                  edgecolor="#ffffff", linewidth=0.15, legend=True, cax=cax,
                                  legend_kwds={"label": "Walk minutes to nearest library (ward centroid)"},
                                  zorder=0)
        a.districts.boundary.plot(ax=ax, color=INK, linewidth=0.6, zorder=1)
        # faint bus-stop density shows the DTC/cluster web the libraries mostly sit within
        if a.bus_path.exists():
            gpd.read_file(a.bus_path).to_crs(4326).plot(ax=ax, color="#3f3a2f", markersize=0.5, alpha=0.28, zorder=2)
        # Metro in contrasting purple so it reads over the red heat (as BRTS/Metro do on the Ahmedabad map)
        a.metro_lines.to_crs(4326).plot(ax=ax, color="#5b2a86", linewidth=1.4, alpha=0.95, zorder=4, label="Metro line")
        a.metro.plot(ax=ax, color="#5b2a86", markersize=4, alpha=0.6, zorder=4)
        metro_ok = a.dpl[a.dpl["metro_m"] <= 800]
        bus_only = a.dpl[(a.dpl["metro_m"] > 800) & (a.dpl["bus_m"] <= 400)]
        isolated = a.dpl[(a.dpl["metro_m"] > 800) & (a.dpl["bus_m"] > 400)]
        metro_ok.plot(ax=ax, color=GREEN, markersize=36, marker="o", edgecolor="white", linewidth=0.6, zorder=6, label=f"≤800 m from Metro ({len(metro_ok)})")
        bus_only.plot(ax=ax, color="#e0a93a", markersize=36, marker="o", edgecolor="white", linewidth=0.6, zorder=6, label=f"Bus only — ≤400 m bus, no Metro ({len(bus_only)})")
        isolated.plot(ax=ax, color=ALERT, markersize=36, marker="o", edgecolor="white", linewidth=0.6, zorder=7, label=f">400 m from any transit ({len(isolated)})")
        b = a.districts.total_bounds  # clamp to Delhi — the GTFS bus net spills into the NCR
        ax.set_xlim(b[0] - 0.02, b[2] + 0.02)
        ax.set_ylim(b[1] - 0.02, b[3] + 0.02)
        ax.legend(loc="lower left", fontsize=7.6, frameon=False)
        ax.set_title("Delhi: are the libraries on the transit network?", color=INK, fontsize=12, loc="left")
        ax.annotate(textwrap.fill(
                        f"Only {m['within800']} of {m['located']} branches are within 800 m of a Metro station "
                        f"({m['within400']} within 400 m) — half are off the rapid-transit grid. But "
                        f"{m['bus_stats'].get('dpl_within_400m_bus', 0)} of {m['located']} sit within 400 m of a bus stop "
                        f"(of {m['bus_stats'].get('bus_stops_total', 0):,} DTC/cluster stops): the bus reaches them, "
                        f"the faster Metro doesn't.", 64),
                    xy=(0.0, -0.07), xycoords="axes fraction", fontsize=7.4, color=MUTED, va="top")
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(self.fig / "figD4_dpl_transit_siting.png", bbox_inches="tight")
        plt.close(fig)

    def write_stats(self, stats: dict) -> None:
        (self.layers / "_dpl_spatial_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
