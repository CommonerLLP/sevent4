#!/usr/bin/env python3
"""Build Delhi air-quality layers from the OpenCity hourly/15-min station feeds.

Source (gitignored): data/cities/delhi/source/opencity/_raw/delhi-hourly-air-quality-reports/
  Two vintages per CPCB/DPCC/IMD/IITM station:
    *_AQI_Data_2017-2023.csv        -> wide AQI matrix: per year-block, month rows x
                                       24 hourly cols, day-of-month in col 0. Values
                                       are the station AQI (0-500 CPCB scale).
    *_15_minute_AQI_Data_for_2024-25.csv -> tidy long: Timestamp + pollutant columns,
                                       incl. "PM2.5 (ug/m3)". Station name in col 4.

Station coordinates come from the CPCB CAAQMS published station list
(data/cities/delhi/source/air_quality/station_master.csv), cross-checked against two
independent GitHub mirrors of the CPCB metadata; NOT from Google Maps.

Outputs:
  derived/finance/...                         (n/a here)
  derived/air_quality/station_long_aqi.csv    long AQI 2017-2023 (station/year/month/day/hour)
  derived/air_quality/station_summary.csv     per-station annual + winter means
  derived/air_quality/station_summary.json
  layers/air_quality.geojson                  station points, mean AQI + winter PM2.5
  layers/ward_aqi.geojson                     ward IDW choropleth of winter AQI
  ../../docs/figures/figD_aq_winter_spike.png  monthly AQI seasonality (winter spike)

    .venv/bin/python scripts/recipes/delhi/build_air_quality.py
"""
from __future__ import annotations
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data/cities/delhi/source/opencity/_raw/delhi-hourly-air-quality-reports"
SRC = ROOT / "data/cities/delhi/source/air_quality"
DERIVED = ROOT / "data/cities/delhi/derived/air_quality"
LAYERS = ROOT / "data/cities/delhi/layers"
FIGS = ROOT / "docs/figures"

WINTER_MONTHS = {10, 11, 12, 1}  # Oct-Jan, the Delhi pollution season
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}

# filename stem (minus the _AQI_Data_... suffix) -> canonical station in station_master.csv
FILE_TO_STATION = {
    "Alipur_DPCC": "Alipur",
    "Anand_Vihar_DPCC": "Anand Vihar",
    "Ashok_Vihar_DPCC": "Ashok Vihar",
    "Aya_Nagar_IMD": "Aya Nagar",
    "Bawana_DPCC": "Bawana",
    "Burari_Crossing_IMD": "Burari Crossing",
    "Chandni_Chowk_IITM": "Chandni Chowk",
    "CRRI_Mathura_Road_IMD": "CRRI Mathura Road",
    "Dr._Karni_Singh_Shooting_Range_DPCC": "Dr. Karni Singh Shooting Range",
    "DTU_CPCB": "DTU",
    "Dwarka_Sector_8_DPCC": "Dwarka-Sector 8",
    "Dwarka_Sector_8": "Dwarka-Sector 8",
    "IGI_Airport_T3_IMD": "IGI Airport (T3)",
    "IHBAS_Dilshad_Garden_CPCB": "IHBAS",
    "IHBAS_CPCB": "IHBAS",
    "ITO_CPCB": "ITO",
    "Jahangirpuri_DPCC": "Jahangirpuri",
    "Jawaharlal_Nehru_Stadium_DPCC": "Jawaharlal Nehru Stadium",
    "Lodhi_Road_IITM": "Lodhi Road",
    "Lodhi_Road_IMD": "Lodhi Road IMD",
    "Major_Dhyan_Chand_National_Stadium_DPCC": "Major Dhyan Chand National Stadium",
    "Mandir_Marg_DPCC": "Mandir Marg",
    "Mundka_DPCC": "Mundka",
    "Najafgarh_DPCC": "Najafgarh",
    "Narela_DPCC": "Narela",
    "Nehru_Nagar_DPCC": "Nehru Nagar",
    "North_Campus_DU_IMD": "North Campus",
    "North_Campus_IMD": "North Campus",
    "NSIT_Dwarka_CPCB": "NSIT Dwarka",
    "Okhla_Phase-2_DPCC": "Okhla Phase-2",
    "Okhla_Phase_2": "Okhla Phase-2",
    "Okhla_Phase-2": "Okhla Phase-2",
    "Patparganj_DPCC": "Patparganj",
    "Punjabi_Bagh_DPCC": "Punjabi Bagh",
    "Pusa_DPCC": "Pusa",
    "Pusa_IMD": "Pusa IMD",
    "R_K_Puram_DPCC": "R K Puram",
    "Rohini_DPCC": "Rohini",
    "Shadipur_CPCB": "Shadipur",
    "Sirifort_CPCB": "Sirifort",
    "Sonia_Vihar_DPCC": "Sonia Vihar",
    "Sri_Aurobindo_Marg_DPCC": "Sri Aurobindo Marg",
    "Vivek_Vihar_DPCC": "Vivek Vihar",
    "Wazirpur_DPCC": "Wazirpur",
}

HOUR_COLS = list(range(1, 25))  # cols 1..24 hold the 24 hourly readings


def _stem(path: Path, suffix: str) -> str:
    return path.name[: -len(suffix)] if path.name.endswith(suffix) else path.stem


def parse_wide_aqi(path: Path, station: str) -> pd.DataFrame:
    """2017-2023 wide AQI -> long rows (station, year, month, day, hour, aqi)."""
    rows = []
    year = None
    month = None
    with open(path, newline="") as fh:
        for raw in fh:
            cells = [c.strip().strip('"') for c in raw.rstrip("\n").split(",")]
            if not cells or cells[0] == "":
                continue
            first = cells[0]
            if first == "Year":
                year = int(cells[1]) if len(cells) > 1 and cells[1].isdigit() else None
                continue
            m = re.match(r"^([A-Za-z]+)-(\d{4})$", first)
            if m:                       # month header row (cols are hour labels)
                month = MONTHS.get(m.group(1))
                if m.group(2).isdigit():
                    year = int(m.group(2))
                continue
            if first.isdigit() and month is not None and year is not None:
                day = int(first)
                if not (1 <= day <= 31):
                    continue
                for h in range(24):
                    idx = 1 + h
                    if idx < len(cells) and cells[idx] not in ("", "nan", "NA"):
                        try:
                            val = float(cells[idx])
                        except ValueError:
                            continue
                        if 0 < val <= 1000:
                            rows.append((station, year, month, day, h, val))
    return pd.DataFrame(rows, columns=["station", "year", "month", "day", "hour", "aqi"])


def parse_15min_pm25(path: Path, station: str) -> pd.DataFrame:
    """2024-25 15-min tidy -> daily-mean PM2.5 rows (station, date, month, pm25)."""
    try:
        df = pd.read_csv(path, usecols=lambda c: c in ("Timestamp", "PM2.5 (µg/m³)"))
    except Exception:
        df = pd.read_csv(path)
        cols = {c: c for c in df.columns}
        pm = [c for c in df.columns if c.startswith("PM2.5")]
        if not pm or "Timestamp" not in df.columns:
            return pd.DataFrame(columns=["station", "date", "month", "pm25"])
        df = df[["Timestamp", pm[0]]].rename(columns={pm[0]: "PM2.5 (µg/m³)"})
    pmcol = [c for c in df.columns if c.startswith("PM2.5")]
    if not pmcol:
        return pd.DataFrame(columns=["station", "date", "month", "pm25"])
    df = df.rename(columns={pmcol[0]: "pm25"})
    df["ts"] = pd.to_datetime(df["Timestamp"], errors="coerce", utc=True)
    df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")
    df = df.dropna(subset=["ts", "pm25"])
    df = df[(df["pm25"] > 0) & (df["pm25"] <= 1200)]
    df["date"] = df["ts"].dt.date
    daily = df.groupby("date", as_index=False)["pm25"].mean()
    daily["month"] = pd.to_datetime(daily["date"]).dt.month
    daily["station"] = station
    return daily[["station", "date", "month", "pm25"]]


def summarise(long_aqi: pd.DataFrame, pm: pd.DataFrame) -> pd.DataFrame:
    out = {}
    # AQI annual + winter mean from hourly 2017-2023
    if not long_aqi.empty:
        g = long_aqi.groupby("station")
        ann = g["aqi"].mean()
        wint = long_aqi[long_aqi["month"].isin(WINTER_MONTHS)].groupby("station")["aqi"].mean()
        n = g["aqi"].size()
        for s in ann.index:
            out.setdefault(s, {})
            out[s]["aqi_annual_mean"] = round(float(ann[s]), 1)
            out[s]["aqi_winter_mean"] = round(float(wint.get(s, np.nan)), 1) if s in wint else None
            out[s]["aqi_hours"] = int(n[s])
            out[s]["aqi_years"] = "2017-2023"
    # PM2.5 annual + winter mean from 2024-25 daily means
    if not pm.empty:
        g = pm.groupby("station")
        ann = g["pm25"].mean()
        wint = pm[pm["month"].isin(WINTER_MONTHS)].groupby("station")["pm25"].mean()
        nd = g["pm25"].size()
        for s in ann.index:
            out.setdefault(s, {})
            out[s]["pm25_annual_mean"] = round(float(ann[s]), 1)
            out[s]["pm25_winter_mean"] = round(float(wint.get(s, np.nan)), 1) if s in wint else None
            out[s]["pm25_days"] = int(nd[s])
            out[s]["pm25_years"] = "2024-2025"
    rec = pd.DataFrame.from_dict(out, orient="index").reset_index(names="station")
    return rec


def idw(stations: gpd.GeoDataFrame, targets: gpd.GeoDataFrame, col: str,
        k: int = 6, power: float = 2.0) -> np.ndarray:
    """Inverse-distance weighting of `col` from station points to target centroids."""
    src = stations.dropna(subset=[col])
    sxy = np.c_[src.geometry.x.values, src.geometry.y.values]
    svals = src[col].astype(float).values
    txy = np.c_[targets.geometry.x.values, targets.geometry.y.values]
    tree = cKDTree(sxy)
    kk = min(k, len(src))
    dist, idx = tree.query(txy, k=kk)
    if kk == 1:
        dist = dist[:, None]; idx = idx[:, None]
    dist = np.maximum(dist, 1e-9)
    w = 1.0 / dist**power
    return (w * svals[idx]).sum(axis=1) / w.sum(axis=1)


def main() -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(SRC / "station_master.csv")
    master_idx = master.set_index("station")

    long_parts, pm_parts = [], []
    parsed_wide, parsed_pm, unmapped = [], [], []
    for path in sorted(RAW.glob("*.csv")):
        if path.name.endswith("_AQI_Data_2017-2023.csv"):
            stem = _stem(path, "_AQI_Data_2017-2023.csv")
            station = FILE_TO_STATION.get(stem)
            if station is None:
                unmapped.append(path.name); continue
            d = parse_wide_aqi(path, station)
            if not d.empty:
                long_parts.append(d); parsed_wide.append(station)
        elif "15_minute_AQI_Data_for_2024-25" in path.name:
            stem = _stem(path, "_15_minute_AQI_Data_for_2024-25.csv")
            station = FILE_TO_STATION.get(stem)
            if station is None:
                unmapped.append(path.name); continue
            d = parse_15min_pm25(path, station)
            if not d.empty:
                pm_parts.append(d); parsed_pm.append(station)

    long_aqi = pd.concat(long_parts, ignore_index=True) if long_parts else pd.DataFrame()
    pm = pd.concat(pm_parts, ignore_index=True) if pm_parts else pd.DataFrame()

    # Persist the long AQI table (compressed; it's large)
    if not long_aqi.empty:
        long_aqi.to_csv(DERIVED / "station_long_aqi.csv.gz", index=False, compression="gzip")

    summary = summarise(long_aqi, pm)
    summary = summary.merge(master, on="station", how="left")
    summary.to_csv(DERIVED / "station_summary.csv", index=False)
    summary.to_json(DERIVED / "station_summary.json", orient="records", indent=2)

    # ---- station points layer ----
    geom = gpd.points_from_xy(summary["longitude"], summary["latitude"])
    gpts = gpd.GeoDataFrame(summary, geometry=geom, crs="EPSG:4326")
    keep = ["station", "agency", "aqi_annual_mean", "aqi_winter_mean",
            "pm25_annual_mean", "pm25_winter_mean", "geometry"]
    keep = [c for c in keep if c in gpts.columns or c == "geometry"]
    gpts[keep].to_file(LAYERS / "air_quality.geojson", driver="GeoJSON")

    # ---- ward IDW choropleth (winter AQI) ----
    wards = gpd.read_file(LAYERS / "wards.geojson").to_crs(4326)
    # project to metric for distance-correct IDW
    sm = gpts.to_crs(32643)
    wm = wards.to_crs(32643).copy()
    wm["cx"] = wm.geometry.centroid
    cent = gpd.GeoDataFrame(wm.drop(columns="geometry"), geometry=wm["cx"], crs=32643)
    for src_col, out_col in [("aqi_winter_mean", "aqi_winter"),
                             ("aqi_annual_mean", "aqi_annual"),
                             ("pm25_winter_mean", "pm25_winter")]:
        if src_col in sm.columns and sm[src_col].notna().sum() >= 3:
            wm[out_col] = np.round(idw(sm, cent, src_col), 1)
    out = wards.copy()
    for c in ("aqi_winter", "aqi_annual", "pm25_winter"):
        if c in wm.columns:
            out[c] = wm[c].values
    cols = ["Name", "ward_name", "ward_no", "aqi_winter", "aqi_annual", "pm25_winter", "geometry"]
    cols = [c for c in cols if c in out.columns]
    out[cols].to_file(LAYERS / "ward_aqi.geojson", driver="GeoJSON")

    # ---- winter-spike figure ----
    make_figure(long_aqi)

    # ---- report ----
    print(f"stations in master:        {len(master)}")
    print(f"parsed wide AQI (2017-23): {len(set(parsed_wide))} stations, "
          f"{len(long_aqi):,} hourly readings")
    print(f"parsed 15-min PM2.5 (24-25): {len(set(parsed_pm))} stations, "
          f"{len(pm):,} station-days")
    if unmapped:
        print(f"UNMAPPED files: {unmapped}")
    print(f"station points: {len(gpts)} -> layers/air_quality.geojson")
    print(f"ward choropleth: {len(out)} wards -> layers/ward_aqi.geojson "
          f"(cols: {[c for c in ('aqi_winter','aqi_annual','pm25_winter') if c in out.columns]})")
    nat_w = long_aqi[long_aqi['month'].isin(WINTER_MONTHS)]['aqi'].mean()
    nat_s = long_aqi[~long_aqi['month'].isin(WINTER_MONTHS)]['aqi'].mean()
    print(f"city-wide winter AQI mean {nat_w:.0f} vs non-winter {nat_s:.0f}")


def make_figure(long_aqi: pd.DataFrame) -> None:
    if long_aqi.empty:
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    by_m = long_aqi.groupby("month")["aqi"].mean().reindex(range(1, 13))
    order = [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]  # start the year at the season
    labels = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr",
              "May", "Jun", "Jul", "Aug", "Sep"]
    vals = [by_m[m] for m in order]
    colors = ["#9f2d2d" if m in WINTER_MONTHS else "#5c7a8a" for m in order]

    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.bar(range(12), vals, color=colors, width=0.78)
    for band, lo, hi, c in [("Moderate", 100, 200, "#f0e3b0"),
                            ("Poor", 200, 300, "#f0cf9e"),
                            ("Very poor", 300, 400, "#e8b3a0"),
                            ("Severe", 400, 500, "#d8a0a0")]:
        ax.axhspan(lo, hi, color=c, alpha=0.18, zorder=0)
    ax.set_xticks(range(12)); ax.set_xticklabels(labels)
    ax.set_ylabel("Mean AQI (CPCB)")
    ax.set_title("Delhi's winter spike: mean monthly AQI across 39 stations, 2017–2023",
                 fontsize=12, loc="left")
    ax.axhline(by_m.mean(), color="#333", lw=0.8, ls="--")
    ax.text(11.4, by_m.mean() + 4, f"annual mean {by_m.mean():.0f}",
            ha="right", fontsize=8, color="#333")
    ax.margins(x=0.01)
    ax.set_ylim(0, max(vals) * 1.12)
    fig.text(0.01, 0.01, "Source: CPCB/DPCC/IMD hourly AQI via OpenCity. "
             "Red = Oct–Jan pollution season.", fontsize=7, color="#666")
    fig.tight_layout()
    fig.savefig(FIGS / "figD_aq_winter_spike.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
