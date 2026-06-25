"""Network + filesystem adapter for Delhi-DPL geocoding: Google Maps Geocoding
API, goo.gl/maps shortlink resolution, Nominatim fallback, and source/output CSV.
Each network method sleeps after its call so callers need no timing logic.
"""
from __future__ import annotations

import csv
import time
from pathlib import Path

import requests

from sevent4.domain.dpl_geocode import extract_pin_coords

UA = "r2r-atlas-research/1.0"


class DplGeocoder:
    def __init__(self, api_key: str = "") -> None:
        self.api_key = (api_key or "").strip()

    @property
    def has_google(self) -> bool:
        return bool(self.api_key)

    def resolve_maps_url(self, url: str):
        """Resolve a DPL goo.gl/maps shortlink to its place-pin coordinates.
        Returns (lat, lon, resolved_url) or (None, None, None)."""
        lat = lon = label = None
        try:
            response = requests.get(url, allow_redirects=True, timeout=20,
                                    headers={"User-Agent": "Mozilla/5.0"})
            lat, lon = extract_pin_coords(response.url)
            if lat is not None:
                label = response.url
        except Exception as error:
            print("  maps-url err", error)
        time.sleep(0.2)
        return lat, lon, label

    def geocode_google(self, query: str):
        """Return (lat, lon, formatted, precision) via Google, or Nones."""
        try:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": query, "key": self.api_key, "region": "in",
                        "bounds": "28.40,76.83|28.89,77.36"}, timeout=20,
            )
            payload = response.json()
            if payload.get("status") == "OK" and payload.get("results"):
                top = payload["results"][0]
                location = top["geometry"]["location"]
                time.sleep(0.1)
                return (location["lat"], location["lng"],
                        top.get("formatted_address", ""),
                        top["geometry"].get("location_type", ""))
        except Exception as error:
            print("  google err", error)
        time.sleep(0.1)
        return None, None, None, None

    def geocode_nominatim(self, query: str):
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1, "countrycodes": "in"},
                headers={"User-Agent": UA}, timeout=20,
            )
            if response.status_code == 200 and response.json():
                hit = response.json()[0]
                time.sleep(1.1)
                return float(hit["lat"]), float(hit["lon"]), hit.get("display_name", "")
        except Exception as error:
            print("  err", error)
        time.sleep(1.1)
        return None, None, None


def read_source_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_geocoded(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
