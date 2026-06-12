#!/usr/bin/env python3
"""Driver: build the Landsat heat layer for all SevenT4 cities."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
RECIPE = REPO / "scripts" / "recipes" / "ahmedabad" / "build_heat_layer.py"
AGG = REPO / "scripts" / "recipes" / "ahmedabad" / "aggregate_ward_heat.py"
PATCH = REPO / "scripts" / "recipes" / "ahmedabad" / "patch_heat_manifest.py"
PY = str(REPO / ".venv" / "bin" / "python")

CITIES = sys.argv[1:] or [
    "chennai", "mumbai", "bengaluru", "hyderabad", "kolkata",
    "visakhapatnam", "bhubaneswar", "kochi", "pune", "kanpur", "jaipur",
]


def run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def main() -> None:
    results = {}
    for city in CITIES:
        cfg = yaml.safe_load((REPO / "data" / "cities" / city / "city.yaml").read_text())
        bbox = [str(x) for x in cfg["bbox"]]
        print(f"\n===== {city}  bbox={bbox} =====", flush=True)

        rc, out, err = run([
            PY, str(RECIPE), "--city", city, "--bbox", *bbox,
            "--datetime", "2023-04-01/2025-06-30", "--cloud-cover", "30",
        ])
        # tail of stderr for scene log
        sys.stderr.write(err[-1500:])
        if rc != 0 or not (REPO / "data" / "cities" / city / "layers" / "heat30m.tif").exists():
            results[city] = {"status": "MISSING", "reason": (err.strip().splitlines() or ["unknown"])[-1]}
            print(f"{city}: HEAT MISSING -> {results[city]['reason']}", flush=True)
            continue
        try:
            scene_stats = json.loads(out[out.rfind("{"):])
        except Exception:
            scene_stats = {}

        rc2, out2, err2 = run([PY, str(AGG), "--city", city])
        if rc2 != 0:
            results[city] = {"status": "RASTER_ONLY", "reason": err2.strip()[-200:], "scene_stats": scene_stats}
            print(f"{city}: ward agg failed -> {err2.strip()[-200:]}", flush=True)
            continue
        agg = json.loads(out2.strip().splitlines()[-1])

        rc3, out3, err3 = run([PY, str(PATCH), "--city", city])
        results[city] = {
            "status": "OK",
            "scenes": scene_stats.get("scenes"),
            "scene_min_c": scene_stats.get("min_c"),
            "scene_max_c": scene_stats.get("max_c"),
            "ward_mean_lst_min": agg.get("mean_lst_min"),
            "ward_mean_lst_max": agg.get("mean_lst_max"),
            "wards_with_lst": agg.get("wards_with_lst"),
            "wards": agg.get("wards"),
            "manifest": out3.strip() or err3.strip(),
        }
        print(f"{city}: OK  {agg.get('mean_lst_min')}-{agg.get('mean_lst_max')}C  "
              f"{agg.get('wards_with_lst')}/{agg.get('wards')} wards", flush=True)

    (REPO / "scripts" / "recipes" / "ahmedabad" / "_heat_run_summary.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    print("\n===== SUMMARY =====")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
