from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CKAN_API = "https://data.opencity.in/api/3/action"
CKAN_UA = {"User-Agent": "sevent4-atlas-catalogue/1.0 (open-data harvest)"}
RAIL_ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
RAIL_UA = {"User-Agent": "sevent4-atlas/1.0 (74th-amendment atlas)"}


def ckan_api(action: str, **params) -> dict:
    qs = urlencode(params)
    url = f"{CKAN_API}/{action}?{qs}" if qs else f"{CKAN_API}/{action}"
    last_err = None
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers=CKAN_UA), timeout=60) as r:
                payload = json.load(r)
            if not payload.get("success"):
                raise RuntimeError(f"{action} returned success=false")
            return payload["result"]
        except Exception as e:  # noqa: BLE001 - network resilience
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{action} failed after retries: {last_err}")


def fetch_all_packages(page_size: int = 200) -> list[dict]:
    first = ckan_api("package_search", rows=0)
    total = first["count"]
    print(f"[catalogue] total datasets reported: {total}", file=sys.stderr)
    pkgs: list[dict] = []
    start = 0
    while start < total:
        res = ckan_api("package_search", rows=page_size, start=start)
        batch = res["results"]
        if not batch:
            break
        pkgs.extend(batch)
        start += len(batch)
        print(f"[catalogue]   fetched {len(pkgs)}/{total}", file=sys.stderr)
    return pkgs


def overpass_rail(query: str) -> dict:
    last = None
    for ep in RAIL_ENDPOINTS:
        try:
            data = urlencode({"data": query}).encode()
            with urlopen(Request(ep, data=data, headers=RAIL_UA), timeout=300) as r:
                j = json.loads(r.read())
            rk = j.get("remark", "")
            if "error" in rk.lower() or "timed out" in rk.lower():
                last = rk
                print(f"  [overpass remark] {rk[:120]}", file=sys.stderr)
                time.sleep(3)
                continue
            return j
        except Exception as e:  # noqa: BLE001 - endpoint fallback
            last = e
            print(f"  [warn] {ep}: {e}", file=sys.stderr)
            time.sleep(3)
    raise RuntimeError(f"Overpass failed: {last}")


def write_json(obj, path, indent=None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=indent), encoding="utf-8")


def write_text(text: str, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
