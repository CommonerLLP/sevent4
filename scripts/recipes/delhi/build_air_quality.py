#!/usr/bin/env python3
"""Build Delhi air-quality layers from the OpenCity hourly/15-min station feeds
(thin CLI wrapper).

Source (gitignored): data/cities/delhi/source/opencity/_raw/delhi-hourly-air-quality-reports/
  Two vintages per CPCB/DPCC/IMD/IITM station:
    *_AQI_Data_2017-2023.csv             -> wide AQI matrix (month rows x 24 hourly cols)
    *_15_minute_AQI_Data_for_2024-25.csv -> tidy long Timestamp + PM2.5 columns

Station coordinates come from the CPCB CAAQMS published station list
(data/cities/delhi/source/air_quality/station_master.csv); NOT from Google Maps.

Parsing, summarisation, and IDW live in sevent4.domain.delhi_air_quality; the
dispatch order in sevent4.application.delhi_air_quality; all file/geospatial/
matplotlib IO in sevent4.adapters.delhi_air_quality_filesystem.

Outputs:
  derived/air_quality/station_long_aqi.csv.gz  long AQI 2017-2023
  derived/air_quality/station_summary.csv      per-station annual + winter means
  derived/air_quality/station_summary.json
  layers/air_quality.geojson                   station points, mean AQI + winter PM2.5
  layers/ward_aqi.geojson                       ward IDW choropleth of winter AQI
  docs/figures/figD_aq_winter_spike.png         monthly AQI seasonality (winter spike)

    .venv/bin/python scripts/recipes/delhi/build_air_quality.py
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.delhi_air_quality_filesystem import DelhiAirQualityStore
from sevent4.application.delhi_air_quality import build_air_quality

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data/cities/delhi/source/opencity/_raw/delhi-hourly-air-quality-reports"
SRC = ROOT / "data/cities/delhi/source/air_quality"
DERIVED = ROOT / "data/cities/delhi/derived/air_quality"
LAYERS = ROOT / "data/cities/delhi/layers"
FIGS = ROOT / "docs/figures"


def main() -> None:
    store = DelhiAirQualityStore(RAW, SRC, DERIVED, LAYERS, FIGS)
    r = build_air_quality(store)
    print(f"stations in master:        {r['master']}")
    print(f"parsed wide AQI (2017-23): {r['parsed_wide']} stations, {r['long_rows']:,} hourly readings")
    print(f"parsed 15-min PM2.5 (24-25): {r['parsed_pm']} stations, {r['pm_rows']:,} station-days")
    if r["unmapped"]:
        print(f"UNMAPPED files: {r['unmapped']}")
    print(f"station points: {r['stations']} -> layers/air_quality.geojson")
    print(f"ward choropleth: {r['wards']} wards -> layers/ward_aqi.geojson (cols: {r['ward_cols']})")
    if r["winter_aqi"] is not None:
        print(f"city-wide winter AQI mean {r['winter_aqi']:.0f} vs non-winter {r['nonwinter_aqi']:.0f}")


if __name__ == "__main__":
    main()
