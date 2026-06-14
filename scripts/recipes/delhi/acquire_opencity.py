#!/usr/bin/env python3
"""Pull Delhi's structured OpenCity data into the gitignored source archive.

Reads the Delhi shortlist (already inventoried by build_atlas_source_inventory.py)
and downloads every machine-readable resource (CSV/GEOJSON/KML/XLSX/JSON) to
data/cities/delhi/source/opencity/raw/<dataset>/, writing a provenance manifest
with sha256 + sizes. PDFs (budget books, manifestos, master plan) are listed in
the manifest but not auto-downloaded here — they need bespoke parsing.

    python3 scripts/recipes/delhi/acquire_opencity.py            # all structured
    python3 scripts/recipes/delhi/acquire_opencity.py --limit 20 # smoke test
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
SHORTLIST = ROOT / "data/cities/delhi/source/opencity/delhi_opencity_atlas_shortlist.csv"
RAW = ROOT / "data/cities/delhi/source/opencity/_raw"  # _raw/ is gitignored
UA = {"User-Agent": "sevent4-atlas-catalogue/1.0 (open-data harvest)"}
KEEP = {"CSV", "GEOJSON", "KML", "XLSX", "JSON"}


def slugify(s: str, fallback: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", (s or "").strip())[:80].strip("_")
    return s or fallback


def fetch(url: str, dest: Path) -> tuple[int, str]:
    for attempt in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=120)
            r.raise_for_status()
            dest.write_bytes(r.content)
            return len(r.content), hashlib.sha256(r.content).hexdigest()
        except Exception:
            if attempt == 2:
                raise
    return 0, ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="cap resources (0 = all)")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(SHORTLIST)))
    usable = [r for r in rows if r["resource_format"].upper() in KEEP and r["resource_url"]]
    skipped_fmt = sorted({r["resource_format"].upper() for r in rows
                          if r["resource_format"].upper() not in KEEP})
    if args.limit:
        usable = usable[: args.limit]

    RAW.mkdir(parents=True, exist_ok=True)
    manifest, jobs = [], []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, r in enumerate(usable):
            ds = slugify(r["dataset_name"] or r["dataset_title"], f"ds{i}")
            ext = r["resource_format"].lower()
            fname = slugify(r["resource_name"] or r["resource_id"], f"r{i}") + f".{ext}"
            dest = RAW / ds / fname
            dest.parent.mkdir(parents=True, exist_ok=True)
            jobs.append((ex.submit(fetch, r["resource_url"], dest), r, ds, dest))
        for fut, r, ds, dest in [(j[0], j[1], j[2], j[3]) for j in jobs]:
            try:
                size, sha = fut.result()
                status = "ok"
            except Exception as e:
                size, sha, status = 0, "", f"error: {type(e).__name__}"
            manifest.append({
                "dataset": r["dataset_title"], "organization": r["organization"],
                "axis": r["axis_labels"], "format": r["resource_format"],
                "url": r["resource_url"], "local": str(dest.relative_to(ROOT)),
                "bytes": size, "sha256": sha, "status": status,
            })

    ok = [m for m in manifest if m["status"] == "ok"]
    (RAW / "_manifest.json").write_text(json.dumps({
        "downloaded": len(ok), "failed": len(manifest) - len(ok),
        "skipped_formats": skipped_fmt, "total_bytes": sum(m["bytes"] for m in ok),
        "resources": manifest,
    }, indent=2), encoding="utf-8")
    mb = sum(m["bytes"] for m in ok) / 1e6
    print(f"delhi OpenCity: {len(ok)}/{len(manifest)} resources, {mb:.1f} MB -> {RAW}")
    print(f"  formats kept: {sorted(KEEP)}; NOT auto-pulled (need parsing): {skipped_fmt}")
    if len(manifest) - len(ok):
        for m in manifest:
            if m["status"] != "ok":
                print(f"  FAILED: {m['dataset'][:40]} [{m['format']}] {m['status']}")


if __name__ == "__main__":
    main()
