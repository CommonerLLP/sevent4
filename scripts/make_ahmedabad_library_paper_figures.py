#!/usr/bin/env python3
"""Build Ahmedabad library figures for the public-libraries paper.

The figures use the 83-row normalized Ahmedabad library inventory rather than
the older 62-point AMC GIS library layer, because the paper's service count is
based on the normalized inventory.

Run:
  MPLCONFIGDIR=/private/tmp/matplotlib-cache python3 scripts/make_ahmedabad_library_paper_figures.py
"""
from __future__ import annotations

import os
import pathlib

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib-cache")

import geopandas as gpd
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.ops import unary_union


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG = ROOT / "docs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

DATA = ROOT / "data" / "cities" / "ahmedabad"
LIBRARY_CSV = DATA / "source" / "libraries" / "ahmedabad_library_locations.csv"
WARD_GEOJSON = DATA / "layers" / "wards.geojson"
STOPS_GEOJSON = DATA / "layers" / "stops.geojson"
METRO_STATIONS_GEOJSON = DATA / "layers" / "metro.geojson"
METRO_LINES_GEOJSON = DATA / "layers" / "metro_lines.geojson"
AMTS_LINES_GEOJSON = DATA / "layers" / "corr_amts.geojson"
BRTS_LINES_GEOJSON = DATA / "layers" / "corr_brts.geojson"
SCHOOLS_GEOJSON = DATA / "layers" / "schools.geojson"
UNIVERSITIES_GEOJSON = DATA / "layers" / "universities.geojson"

WGS84 = "EPSG:4326"
METRIC = "EPSG:32643"

INK = "#172126"
MUTED = "#66737A"
RULE = "#C7D0D5"
WARD_FILL = "#F4F7F8"
BLUE = "#1B4E6B"
GREEN = "#1F8F6B"
AMBER = "#C87920"
RED = "#B0412B"
PURPLE = "#6A4C93"
TEAL = "#2E8C9A"
SCHOOL = "#8A8F93"
PAPER = "#FFFFFF"

mpl.rcParams.update(
    {
        "font.family": "Helvetica",
        "font.size": 10,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "figure.facecolor": PAPER,
        "axes.facecolor": PAPER,
        "savefig.facecolor": PAPER,
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
    }
)


def _clean_axis(ax):
    ax.set_axis_off()
    ax.set_aspect("equal")


def _read_layers():
    wards = gpd.read_file(WARD_GEOJSON).to_crs(METRIC)
    raw = pd.read_csv(LIBRARY_CSV)
    libraries = gpd.GeoDataFrame(
        raw,
        geometry=gpd.points_from_xy(raw["longitude"], raw["latitude"]),
        crs=WGS84,
    ).to_crs(METRIC)
    stops = gpd.read_file(STOPS_GEOJSON).to_crs(METRIC)
    metro_stations = gpd.read_file(METRO_STATIONS_GEOJSON).to_crs(METRIC)
    metro_lines = gpd.read_file(METRO_LINES_GEOJSON).to_crs(METRIC)
    amts_lines = gpd.read_file(AMTS_LINES_GEOJSON).to_crs(METRIC)
    brts_lines = gpd.read_file(BRTS_LINES_GEOJSON).to_crs(METRIC)
    schools = gpd.read_file(SCHOOLS_GEOJSON).to_crs(METRIC)
    universities = gpd.read_file(UNIVERSITIES_GEOJSON).to_crs(METRIC)
    return wards, libraries, stops, metro_stations, metro_lines, amts_lines, brts_lines, schools, universities


def _nearest_distance_m(points: gpd.GeoSeries, targets: gpd.GeoSeries) -> pd.Series:
    target_union = unary_union(list(targets))
    return points.distance(target_union)


def _set_extent(ax, wards):
    xmin, ymin, xmax, ymax = wards.total_bounds
    pad_x = (xmax - xmin) * 0.05
    pad_y = (ymax - ymin) * 0.05
    ax.set_xlim(xmin - pad_x, xmax + pad_x)
    ax.set_ylim(ymin - pad_y, ymax + pad_y)


def fig_access_proxy(wards, libraries):
    """Map the 83-location inventory and first-pass 1.2 km access proxy."""
    lib_union = unary_union(list(libraries.geometry))
    wards = wards.copy()
    wards["nearest_library_km"] = wards.geometry.centroid.distance(lib_union) / 1000

    buffer_1200 = unary_union(list(libraries.geometry.buffer(1200)))
    ward_area = wards.geometry.area.sum()
    covered_area = wards.geometry.intersection(buffer_1200).area.sum()
    covered_share = covered_area / ward_area * 100
    covered_wards = int((wards["nearest_library_km"] <= 1.2).sum())
    median_km = float(wards["nearest_library_km"].median())

    priority_names = ["46 LAMBHA", "48 RAMOL HATHIJAN", "41 VASTRAL"]
    priority = wards[wards["Name"].isin(priority_names)]

    fig, ax = plt.subplots(figsize=(8.4, 8.2))
    wards.plot(
        ax=ax,
        column="nearest_library_km",
        cmap="YlGnBu_r",
        legend=True,
        edgecolor="#FFFFFF",
        linewidth=0.65,
        legend_kwds={
            "label": "Nearest listed library from ward centroid (km)",
            "shrink": 0.62,
            "pad": 0.02,
        },
        zorder=1,
    )
    gpd.GeoSeries([buffer_1200], crs=METRIC).plot(
        ax=ax,
        color=GREEN,
        alpha=0.12,
        edgecolor=GREEN,
        linewidth=0.4,
        zorder=2,
    )
    wards.boundary.plot(ax=ax, color="#FFFFFF", linewidth=0.45, zorder=3)
    priority.boundary.plot(ax=ax, color=RED, linewidth=2.0, zorder=4)
    libraries.plot(
        ax=ax,
        markersize=20,
        color=BLUE,
        edgecolor="white",
        linewidth=0.35,
        zorder=5,
    )

    for row in priority.to_crs(METRIC).itertuples():
        p = row.geometry.representative_point()
        label = str(row.Name).split(" ", 1)[1].title()
        ax.annotate(
            label,
            (p.x, p.y),
            xytext=(3, 3),
            textcoords="offset points",
            fontsize=8.2,
            color=RED,
            fontweight="bold",
            zorder=6,
        )

    ax.set_title(
        "Ahmedabad: 83 library locations, first-pass 1.2 km access proxy",
        loc="left",
        fontweight="bold",
        fontsize=13.2,
        pad=8,
    )
    subtitle = (
        f"{covered_wards} of {len(wards)} wards have centroids within 1.2 km; "
        f"{covered_share:.0f}% of mapped ward area falls inside a 1.2 km straight-line buffer; "
        f"median ward-centroid distance is {median_km:.2f} km."
    )
    ax.text(0, 0.992, subtitle, transform=ax.transAxes, ha="left", va="top", fontsize=8.7, color=MUTED)
    ax.text(
        0,
        -0.02,
        "Sources: AMC ward layer and normalized Ahmedabad library inventory. Distances are straight-line proxies, not street-network travel times.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.6,
        color=MUTED,
    )
    _set_extent(ax, wards)
    _clean_axis(ax)
    fig.savefig(FIG / "figA1_ahmedabad_walk_access_proxy.png")
    plt.close(fig)
    print(
        "wrote figA1_ahmedabad_walk_access_proxy.png "
        f"({covered_wards}/{len(wards)} ward centroids <=1.2km; {covered_share:.1f}% area; median {median_km:.2f}km)"
    )
    return {
        "ward_centroids_within_1200m": covered_wards,
        "ward_count": len(wards),
        "area_within_1200m_pct": covered_share,
        "median_ward_centroid_km": median_km,
    }


def fig_transit_context(wards, libraries, stops, metro_stations, metro_lines, amts_lines, brts_lines, schools, universities):
    """Show libraries against transit and education-service context."""
    libraries = libraries.copy()
    libraries["bus_stop_m"] = _nearest_distance_m(libraries.geometry, stops.geometry)
    libraries["metro_station_m"] = _nearest_distance_m(libraries.geometry, metro_stations.geometry)
    libraries["brts_corridor_m"] = _nearest_distance_m(libraries.geometry, brts_lines.geometry)

    def classify(row):
        if row.metro_station_m <= 800:
            return "Metro within 800 m"
        if row.brts_corridor_m <= 400:
            return "BRTS corridor within 400 m"
        if row.bus_stop_m <= 400:
            return "Bus stop within 400 m"
        return "Off mapped transit"

    libraries["transit_class"] = libraries.apply(classify, axis=1)
    palette = {
        "Metro within 800 m": GREEN,
        "BRTS corridor within 400 m": AMBER,
        "Bus stop within 400 m": BLUE,
        "Off mapped transit": RED,
    }
    counts = libraries["transit_class"].value_counts().to_dict()

    fig, ax = plt.subplots(figsize=(8.4, 8.2))
    wards.plot(ax=ax, color=WARD_FILL, edgecolor="#FFFFFF", linewidth=0.55, zorder=1)
    amts_lines.plot(ax=ax, color="#B9C2C7", linewidth=0.35, alpha=0.28, zorder=2)
    brts_lines.plot(ax=ax, color=AMBER, linewidth=1.2, alpha=0.8, zorder=3)
    metro_lines.plot(ax=ax, color=PURPLE, linewidth=1.5, alpha=0.9, zorder=4)
    schools.plot(ax=ax, markersize=8, color=SCHOOL, alpha=0.36, zorder=5)
    universities.plot(ax=ax, markersize=18, color="#30383D", marker="^", alpha=0.52, zorder=6)
    for cls, color in palette.items():
        g = libraries[libraries["transit_class"] == cls]
        if len(g):
            g.plot(ax=ax, markersize=28, color=color, edgecolor="white", linewidth=0.35, zorder=7)

    ax.set_title(
        "Ahmedabad: library siting against transit and education anchors",
        loc="left",
        fontweight="bold",
        fontsize=13.2,
        pad=8,
    )
    subtitle = (
        f"{int((libraries['bus_stop_m'] <= 400).sum())} of {len(libraries)} listed libraries are within 400 m of a mapped bus stop; "
        f"{int((libraries['metro_station_m'] <= 800).sum())} are within 800 m of a Metro station; "
        f"{int((libraries['brts_corridor_m'] <= 400).sum())} are within 400 m of a BRTS corridor."
    )
    ax.text(0, 0.992, subtitle, transform=ax.transAxes, ha="left", va="top", fontsize=8.7, color=MUTED)
    ax.text(
        0,
        -0.02,
        "Sources: Ahmedabad library inventory, AMC ward layer, AMTS/BRTS/Metro layers, and school/college POIs. This is a siting map, not a commute-time model.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.6,
        color=MUTED,
    )

    handles = [
        Line2D([0], [0], color="#B9C2C7", lw=1.2, label="AMTS corridors"),
        Line2D([0], [0], color=AMBER, lw=1.8, label="BRTS corridors"),
        Line2D([0], [0], color=PURPLE, lw=1.8, label="Metro"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=SCHOOL, markeredgecolor=SCHOOL, markersize=5, alpha=0.55, label="Schools"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#30383D", markeredgecolor="#30383D", markersize=6, alpha=0.7, label="Colleges/universities"),
    ]
    handles.extend(
        Patch(facecolor=color, edgecolor="white", label=f"{cls} ({counts.get(cls, 0)})")
        for cls, color in palette.items()
    )
    ax.legend(handles=handles, loc="lower left", frameon=True, framealpha=0.94, fontsize=7.8)

    _set_extent(ax, wards)
    _clean_axis(ax)
    fig.savefig(FIG / "figA2_ahmedabad_transit_education_context.png")
    plt.close(fig)
    print(
        "wrote figA2_ahmedabad_transit_education_context.png "
        f"(bus400={int((libraries['bus_stop_m'] <= 400).sum())}; "
        f"metro800={int((libraries['metro_station_m'] <= 800).sum())}; "
        f"brts400={int((libraries['brts_corridor_m'] <= 400).sum())})"
    )
    return {
        "bus_stop_400m": int((libraries["bus_stop_m"] <= 400).sum()),
        "metro_station_800m": int((libraries["metro_station_m"] <= 800).sum()),
        "brts_corridor_400m": int((libraries["brts_corridor_m"] <= 400).sum()),
        "transit_class_counts": counts,
    }


def fig_exclusion_cross(wards, libraries):
    """Cross ward deprivation against spatially computed library access.

    The headline is the double-locked quadrant: wards above the median on BOTH
    deprivation and nearest-library distance. Bubble area is ward population, so
    the eye reads how many people sit in each quadrant, not just how many wards.
    Access is measured directly here because the ward layer's precomputed
    library-desert flag is unusable (it reads true for all 48 wards).
    """
    lib_union = unary_union(list(libraries.geometry))
    w = wards.copy()
    w["nearest_library_km"] = w.geometry.centroid.distance(lib_union) / 1000
    w["dep"] = pd.to_numeric(w["deprivation"], errors="coerce")
    w["pop"] = pd.to_numeric(w["population_2020"], errors="coerce")
    w = w.dropna(subset=["dep", "pop"]).copy()

    med_dep = float(w["dep"].median())
    med_km = float(w["nearest_library_km"].median())
    w["double_locked"] = (w["dep"] >= med_dep) & (w["nearest_library_km"] >= med_km)
    locked = w[w["double_locked"]]
    people_locked = int(locked["pop"].sum())
    pop_total = int(w["pop"].sum())
    pop_max = float(w["pop"].max())

    def _sizes(frame):
        return (frame["pop"] / pop_max) * 880 + 28

    fig, ax = plt.subplots(figsize=(8.4, 8.0))
    xmax = 1.0
    ymax = float(w["nearest_library_km"].max()) * 1.08
    # shade the double-locked quadrant (high deprivation AND far from a library)
    ax.add_patch(
        plt.Rectangle(
            (med_dep, med_km),
            xmax - med_dep,
            ymax - med_km,
            facecolor=RED,
            alpha=0.05,
            edgecolor="none",
            zorder=1,
        )
    )
    ax.axvline(med_dep, color=MUTED, lw=0.8, ls="--", zorder=2)
    ax.axhline(med_km, color=MUTED, lw=0.8, ls="--", zorder=2)

    served = w[~w["double_locked"]]
    ax.scatter(
        served["dep"], served["nearest_library_km"], s=_sizes(served),
        c=MUTED, alpha=0.5, edgecolor="white", linewidth=0.5, zorder=3,
    )
    ax.scatter(
        locked["dep"], locked["nearest_library_km"], s=_sizes(locked),
        c=RED, alpha=0.82, edgecolor="white", linewidth=0.6, zorder=4,
    )
    for row in locked.itertuples():
        label = str(row.Name).split(" ", 1)[1].title()
        ax.annotate(
            label,
            (row.dep, row.nearest_library_km),
            xytext=(4, 3),
            textcoords="offset points",
            fontsize=7.4,
            color=RED,
            fontweight="bold",
            zorder=5,
        )

    ax.text(med_dep + 0.004, ymax * 0.985, "Double-locked", color=RED, fontsize=8.6,
            fontweight="bold", ha="left", va="top", zorder=6)
    ax.set_xlim(min(0.0, float(w["dep"].min()) - 0.03), xmax + 0.01)
    ax.set_ylim(0, ymax)
    ax.set_xlabel("Ward deprivation index (0–1)")
    ax.set_ylabel("Distance from ward centroid to nearest listed library (km)")
    ax.set_aspect("auto")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    ax.set_title(
        "Ahmedabad: who is shut out — deprivation against library access",
        loc="left",
        fontweight="bold",
        fontsize=13.2,
        pad=10,
    )
    subtitle = (
        f"{len(locked)} of {len(w)} wards sit in the double-locked quadrant: deprivation ≥ {med_dep:.2f}\n"
        f"and ≥ {med_km:.2f} km from a library. They hold {people_locked:,} residents —\n"
        f"{people_locked / pop_total * 100:.0f}% of mapped ward population. Bubble area is ward population."
    )
    ax.text(0.012, 0.985, subtitle, transform=ax.transAxes, ha="left", va="top",
            fontsize=8.6, color=MUTED, linespacing=1.45)
    ax.text(
        0,
        -0.085,
        "Sources: AMC ward layer (deprivation, 2020 population) and the normalized 83-location library inventory. "
        "Distance is a straight-line centroid proxy, not a street-network travel time.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.6,
        color=MUTED,
    )
    fig.savefig(FIG / "figA3_ahmedabad_library_exclusion_cross.png")
    plt.close(fig)
    print(
        "wrote figA3_ahmedabad_library_exclusion_cross.png "
        f"({len(locked)}/{len(w)} double-locked wards; {people_locked:,} residents)"
    )
    return {
        "double_locked_wards": int(len(locked)),
        "ward_count": int(len(w)),
        "people_in_double_locked": people_locked,
        "median_deprivation": round(med_dep, 3),
        "median_nearest_library_km": round(med_km, 3),
    }


def main():
    layers = _read_layers()
    wards, libraries = layers[0], layers[1]
    access_stats = fig_access_proxy(wards, libraries)
    transit_stats = fig_transit_context(*layers)
    exclusion_stats = fig_exclusion_cross(wards, libraries)
    print("Ahmedabad figure stats:")
    print(access_stats)
    print(transit_stats)
    print(exclusion_stats)
    print("Figures written to", FIG)


if __name__ == "__main__":
    main()
