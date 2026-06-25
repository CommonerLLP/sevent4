"""Build Delhi air-quality outputs: parse the wide 2017-2023 AQI feeds and the
2024-25 15-minute PM2.5 feeds, summarise per station, and emit the long table,
summaries, station-point and ward-IDW layers, and the winter-spike figure.
File/geospatial IO is injected via the store; this layer owns the dispatch order.
"""
from __future__ import annotations

import pandas as pd

from sevent4.domain.delhi_air_quality import (
    FILE_TO_STATION,
    WINTER_MONTHS,
    clean_15min_pm25,
    file_stem,
    parse_wide_aqi_lines,
    summarise,
)

_WIDE_SUFFIX = "_AQI_Data_2017-2023.csv"
_PM_SUFFIX = "_15_minute_AQI_Data_for_2024-25.csv"


def build_air_quality(store) -> dict:
    master = store.read_master()

    long_parts, pm_parts = [], []
    parsed_wide, parsed_pm, unmapped = [], [], []
    for path, name in store.iter_raw_csvs():
        if name.endswith(_WIDE_SUFFIX):
            station = FILE_TO_STATION.get(file_stem(name, _WIDE_SUFFIX))
            if station is None:
                unmapped.append(name); continue
            d = parse_wide_aqi_lines(store.read_lines(path), station)
            if not d.empty:
                long_parts.append(d); parsed_wide.append(station)
        elif "15_minute_AQI_Data_for_2024-25" in name:
            station = FILE_TO_STATION.get(file_stem(name, _PM_SUFFIX))
            if station is None:
                unmapped.append(name); continue
            d = clean_15min_pm25(store.read_15min_csv(path), station)
            if not d.empty:
                pm_parts.append(d); parsed_pm.append(station)

    long_aqi = pd.concat(long_parts, ignore_index=True) if long_parts else pd.DataFrame()
    pm = pd.concat(pm_parts, ignore_index=True) if pm_parts else pd.DataFrame()

    if not long_aqi.empty:
        store.write_long_aqi(long_aqi)

    summary = summarise(long_aqi, pm).merge(master, on="station", how="left")
    store.write_summary(summary)

    gpts = store.write_station_points(summary)
    out = store.write_ward_choropleth(gpts)
    store.render_figure(long_aqi)

    winter = nonwinter = None
    if not long_aqi.empty:
        winter = long_aqi[long_aqi["month"].isin(WINTER_MONTHS)]["aqi"].mean()
        nonwinter = long_aqi[~long_aqi["month"].isin(WINTER_MONTHS)]["aqi"].mean()
    return {
        "master": len(master),
        "parsed_wide": len(set(parsed_wide)), "long_rows": len(long_aqi),
        "parsed_pm": len(set(parsed_pm)), "pm_rows": len(pm),
        "unmapped": unmapped, "stations": len(gpts), "wards": len(out),
        "ward_cols": [c for c in ("aqi_winter", "aqi_annual", "pm25_winter") if c in out.columns],
        "winter_aqi": winter, "nonwinter_aqi": nonwinter,
    }
