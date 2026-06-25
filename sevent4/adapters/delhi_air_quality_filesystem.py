"""Filesystem + geospatial + matplotlib adapter for Delhi air quality: read the
station master and the raw OpenCity AQI/PM2.5 feeds, persist the long table and
summaries, build the station-point and ward-IDW GeoJSON layers, and render the
winter-spike figure.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from sevent4.domain.delhi_air_quality import idw

_WIDE_SUFFIX = "_AQI_Data_2017-2023.csv"
_PM_TARGET = "PM2.5 (µg/m³)"  # "PM2.5 (µg/m³)"


class DelhiAirQualityStore:
    def __init__(self, raw_dir: Path, src_dir: Path, derived_dir: Path,
                 layers_dir: Path, figs_dir: Path) -> None:
        self.raw = Path(raw_dir)
        self.src = Path(src_dir)
        self.derived = Path(derived_dir)
        self.layers = Path(layers_dir)
        self.figs = Path(figs_dir)
        self.derived.mkdir(parents=True, exist_ok=True)
        self.figs.mkdir(parents=True, exist_ok=True)

    def read_master(self) -> pd.DataFrame:
        return pd.read_csv(self.src / "station_master.csv")

    def iter_raw_csvs(self):
        return [(path, path.name) for path in sorted(self.raw.glob("*.csv"))]

    def read_lines(self, path: Path) -> list[str]:
        with open(path, newline="") as handle:
            return handle.readlines()

    def read_15min_csv(self, path: Path) -> pd.DataFrame:
        try:
            return pd.read_csv(path, usecols=lambda c: c in ("Timestamp", _PM_TARGET))
        except Exception:
            df = pd.read_csv(path)
            pm = [c for c in df.columns if c.startswith("PM2.5")]
            if not pm or "Timestamp" not in df.columns:
                return pd.DataFrame(columns=["Timestamp", _PM_TARGET])
            return df[["Timestamp", pm[0]]].rename(columns={pm[0]: _PM_TARGET})

    def write_long_aqi(self, long_aqi: pd.DataFrame) -> None:
        # compressed; it's large
        long_aqi.to_csv(self.derived / "station_long_aqi.csv.gz", index=False, compression="gzip")

    def write_summary(self, summary: pd.DataFrame) -> None:
        summary.to_csv(self.derived / "station_summary.csv", index=False)
        summary.to_json(self.derived / "station_summary.json", orient="records", indent=2)

    def write_station_points(self, summary: pd.DataFrame) -> gpd.GeoDataFrame:
        geom = gpd.points_from_xy(summary["longitude"], summary["latitude"])
        gpts = gpd.GeoDataFrame(summary, geometry=geom, crs="EPSG:4326")
        keep = ["station", "agency", "aqi_annual_mean", "aqi_winter_mean",
                "pm25_annual_mean", "pm25_winter_mean", "geometry"]
        keep = [c for c in keep if c in gpts.columns or c == "geometry"]
        gpts[keep].to_file(self.layers / "air_quality.geojson", driver="GeoJSON")
        return gpts

    def write_ward_choropleth(self, gpts: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        wards = gpd.read_file(self.layers / "wards.geojson").to_crs(4326)
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
        out[cols].to_file(self.layers / "ward_aqi.geojson", driver="GeoJSON")
        return out

    def render_figure(self, long_aqi: pd.DataFrame) -> None:
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
        colors = ["#9f2d2d" if m in {10, 11, 12, 1} else "#5c7a8a" for m in order]

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
        fig.savefig(self.figs / "figD_aq_winter_spike.png", dpi=150)
        plt.close(fig)
