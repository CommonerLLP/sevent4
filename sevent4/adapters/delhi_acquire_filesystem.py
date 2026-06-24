from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import time
import zipfile
from pathlib import Path

from sevent4.domain.delhi_acquire import AC_BASE, PC_URL, WARDS_URL

UA = {"User-Agent": "sevent4-atlas/1.0 (74th-amendment atlas)"}
OVERPASS = "https://overpass-api.de/api/interpreter"
OTD_STATIC_URL = "https://otd.delhi.gov.in/data/static/"


# ---- HTTP ----
def download(url: str, dest: Path) -> Path:
    import requests

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, headers=UA, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def fetch_with_sha(url: str, dest: Path) -> tuple[int, str]:
    import requests

    for attempt in range(3):
        try:
            r = requests.get(url, headers={"User-Agent": "sevent4-atlas-catalogue/1.0 (open-data harvest)"}, timeout=120)
            r.raise_for_status()
            Path(dest).write_bytes(r.content)
            return len(r.content), hashlib.sha256(r.content).hexdigest()
        except Exception:
            if attempt == 2:
                raise
    return 0, ""


def overpass_post(query: str) -> dict:
    import requests

    for attempt in range(3):
        try:
            r = requests.post(OVERPASS, data={"data": query}, headers=UA, timeout=120)
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(8)
    return {"elements": []}


def download_otd_static(dest: Path, verify: bool = True) -> Path:
    import requests

    s = requests.Session()
    s.headers["User-Agent"] = UA["User-Agent"]
    g = s.get(OTD_STATIC_URL, timeout=60, verify=verify)
    g.raise_for_status()
    token = ""
    for line in g.text.splitlines():
        if "csrfmiddlewaretoken" in line and "value=" in line:
            token = line.split("value=")[1].strip().strip("'\"").split(">")[0].strip("'\" ")
            break
    email = os.environ.get("OTD_EMAIL", "research@example.org")
    r = s.post(
        OTD_STATIC_URL,
        data={"csrfmiddlewaretoken": token, "dataDownloaded": "routes", "name": "research",
              "email": email, "purpose": "academic municipalities atlas"},
        headers={"Referer": OTD_STATIC_URL}, timeout=180, verify=verify,
    )
    r.raise_for_status()
    if "zip" not in r.headers.get("Content-Type", ""):
        raise RuntimeError(f"OTD did not return a zip (got {r.headers.get('Content-Type')})")
    dest.write_bytes(r.content)
    print(f"  downloaded {len(r.content)} bytes, sha256={hashlib.sha256(r.content).hexdigest()}")
    return dest


# ---- boundaries (geopandas) ----
class DelhiBoundarySource:
    def __init__(self, tmp: Path) -> None:
        self.tmp = Path(tmp)

    def acs(self):
        import geopandas as gpd

        for ext in ("shp", "dbf", "shx", "prj"):
            download(f"{AC_BASE}.{ext}", self.tmp / f"India_AC.{ext}")
        g = gpd.read_file(self.tmp / "India_AC.shp")
        g = g[g["ST_NAME"].astype(str).str.strip().str.upper().eq("DELHI")].copy().to_crs(4326)
        g["ac_name"] = g["AC_NAME"].astype(str).str.strip()
        g["ac_no"] = g["AC_NO"]
        g["dist_name"] = g["DIST_NAME"].astype(str).str.strip()
        g["pc_name"] = g["PC_NAME"].astype(str).str.strip()
        g["office"] = "MLA"
        return g[["ac_name", "ac_no", "dist_name", "pc_name", "office", "geometry"]]

    def pcs(self):
        import geopandas as gpd

        download(PC_URL, self.tmp / "india_pc.geojson")
        g = gpd.read_file(self.tmp / "india_pc.geojson")
        g = g[g["st_name"].astype(str).str.strip().str.upper().eq("DELHI")].copy().to_crs(4326)
        g["pc_name"] = g["pc_name"].astype(str).str.strip()
        g["office"] = "MP"
        return g[["pc_name", "pc_no", "office", "geometry"]]

    def wards(self):
        import geopandas as gpd

        download(WARDS_URL, self.tmp / "Delhi_Wards.geojson")
        g = gpd.read_file(self.tmp / "Delhi_Wards.geojson").to_crs(4326)
        g["ward_name"] = g["Ward_Name"].astype(str).str.title().str.strip()
        g["ward_no"] = g["Ward_No"].astype(str).str.strip()
        g["Name"] = g["ward_name"]
        g["ward_vintage"] = "pre-2022 (interim; not the 2022 unified-MCD 250-ward set)"
        return g[["Name", "ward_name", "ward_no", "ward_vintage", "geometry"]]

    def districts(self, acs):
        valid = acs["dist_name"].notna() & acs["dist_name"].astype(str).str.strip().ne("")
        if not valid.any():
            return None
        d = acs[valid].dissolve(by="dist_name", as_index=False)[["dist_name", "geometry"]]
        d["district"] = d["dist_name"]
        return d[["district", "geometry"]]


def write_geodataframe(gdf, path: Path) -> None:
    gdf.to_file(Path(path), driver="GeoJSON")


# ---- GTFS feed (pandas) ----
def load_gtfs_feed(zip_path: str | None, dir_path: str | None) -> dict:
    import pandas as pd

    def _read(buf):
        return pd.read_csv(buf, dtype=str, keep_default_na=False)

    want = ("routes", "trips", "stops", "stop_times", "shapes", "agency")
    tables: dict = {}
    if dir_path:
        d = Path(dir_path)
        for name in want:
            f = d / f"{name}.txt"
            if f.exists():
                tables[name] = _read(f)
    elif zip_path:
        with zipfile.ZipFile(zip_path) as zf:
            names = {Path(n).name: n for n in zf.namelist()}
            for name in want:
                if f"{name}.txt" in names:
                    with zf.open(names[f"{name}.txt"]) as fh:
                        tables[name] = _read(io.TextIOWrapper(fh, "utf-8"))
    else:
        raise ValueError("need --zip or --dir")
    return tables


# ---- generic file IO ----
def read_csv_rows(path: Path) -> list[dict]:
    with Path(path).open() as fh:
        return list(csv.DictReader(fh))


def write_json(document, path: Path, indent=None) -> None:
    Path(path).write_text(json.dumps(document, ensure_ascii=False, indent=indent), encoding="utf-8")


def write_text(text: str, path: Path) -> None:
    Path(path).write_text(text, encoding="utf-8")


def write_geojson(fc: dict, path: Path) -> int:
    Path(path).write_text(json.dumps(fc), encoding="utf-8")
    return len(fc["features"])


def load_layer_manifest(path: Path) -> dict:
    return json.loads(Path(path).read_text())
