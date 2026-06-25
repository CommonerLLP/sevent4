"""Pure Delhi air-quality logic: the CPCB station file→name map, the wide
2017–2023 AQI line parser, the 2024–25 15-minute PM2.5 cleaner, per-station
summarisation, and inverse-distance weighting. No filesystem IO (callers pass
already-read lines / DataFrames / GeoDataFrames).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

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


def file_stem(name: str, suffix: str) -> str:
    return name[: -len(suffix)] if name.endswith(suffix) else name.rsplit(".", 1)[0]


def parse_wide_aqi_lines(lines, station: str) -> pd.DataFrame:
    """2017-2023 wide AQI text lines -> long rows (station, year, month, day, hour, aqi)."""
    rows = []
    year = None
    month = None
    for raw in lines:
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


def clean_15min_pm25(df: pd.DataFrame, station: str) -> pd.DataFrame:
    """2024-25 15-min frame (Timestamp + PM2.5 col) -> daily-mean PM2.5 rows."""
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


def idw(stations, targets, col: str, k: int = 6, power: float = 2.0) -> np.ndarray:
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
