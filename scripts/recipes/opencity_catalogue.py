#!/usr/bin/env python3
"""Catalogue the full data.opencity.in CKAN portal — no downloads.

Enumerates every dataset (package) via the CKAN Action API, captures each
resource (format, size, url, last-modified) plus group + organization
membership, and writes:
  - opencity_catalogue.json   the full machine-readable manifest
  - opencity_catalogue.md     a human-readable index (counts by city/org/format)

CKAN 2.11.4. Action API is public; no key needed. Paginates package_search.

Usage:
  python3 scripts/recipes/opencity_catalogue.py --out data/sources/opencity/_catalogue
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from urllib.request import urlopen, Request

BASE = "https://data.opencity.in"
API = f"{BASE}/api/3/action"
UA = {"User-Agent": "sevent4-atlas-catalogue/1.0 (open-data harvest)"}


def api(action: str, **params) -> dict:
    """Call a CKAN action endpoint, return result, with light retry."""
    from urllib.parse import urlencode
    qs = urlencode(params)
    url = f"{API}/{action}?{qs}" if qs else f"{API}/{action}"
    last_err = None
    for attempt in range(4):
        try:
            req = Request(url, headers=UA)
            with urlopen(req, timeout=60) as r:
                payload = json.load(r)
            if not payload.get("success"):
                raise RuntimeError(f"{action} returned success=false")
            return payload["result"]
        except Exception as e:  # noqa: BLE001 - network resilience
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{action} failed after retries: {last_err}")


def fetch_all_packages(page_size: int = 200) -> list[dict]:
    """Page through package_search and return every package dict."""
    first = api("package_search", rows=0)
    total = first["count"]
    print(f"[catalogue] total datasets reported: {total}", file=sys.stderr)
    pkgs: list[dict] = []
    start = 0
    while start < total:
        res = api("package_search", rows=page_size, start=start)
        batch = res["results"]
        if not batch:
            break
        pkgs.extend(batch)
        start += len(batch)
        print(f"[catalogue]   fetched {len(pkgs)}/{total}", file=sys.stderr)
    return pkgs


def to_int(v) -> int | None:
    try:
        if v in (None, "", "None"):
            return None
        return int(float(v))
    except (TypeError, ValueError):
        return None


def build(pkgs: list[dict]) -> dict:
    datasets = []
    fmt_counter: Counter[str] = Counter
    group_counter: Counter[str] = Counter
    org_counter: Counter[str] = Counter
    bytes_by_group: defaultdict[str, int] = defaultdict(int)
    total_resources = 0
    total_known_bytes = 0

    for p in pkgs:
        groups = [g.get("name") for g in p.get("groups", [])]
        org = (p.get("organization") or {}).get("name")
        resources = []
        for r in p.get("resources", []):
            size = to_int(r.get("size"))
            fmt = (r.get("format") or "").strip.upper or "UNKNOWN"
            fmt_counter[fmt] += 1
            total_resources += 1
            if size:
                total_known_bytes += size
                for g in groups or ["(no-group)"]:
                    bytes_by_group[g] += size
            resources.append({
                "id": r.get("id"),
                "name": r.get("name"),
                "format": fmt,
                "url": r.get("url"),
                "size_bytes": size,
                "last_modified": r.get("last_modified") or r.get("created"),
                "mimetype": r.get("mimetype"),
            })
        for g in groups:
            group_counter[g] += 1
        if org:
            org_counter[org] += 1
        datasets.append({
            "name": p.get("name"),
            "title": p.get("title"),
            "url": f"{BASE}/dataset/{p.get('name')}",
            "organization": org,
            "groups": groups,
            "tags": [t.get("name") for t in p.get("tags", [])],
            "notes": (p.get("notes") or "")[:500],
            "num_resources": len(resources),
            "metadata_modified": p.get("metadata_modified"),
            "resources": resources,
        })

    return {
        "source": BASE,
        "ckan_version": "2.11.4",
        "dataset_count": len(datasets),
        "resource_count": total_resources,
        "known_bytes": total_known_bytes,
        "formats": dict(fmt_counter.most_common),
        "datasets_per_group": dict(group_counter.most_common),
        "datasets_per_org": dict(org_counter.most_common),
        "known_bytes_per_group": {k: v for k, v in sorted(bytes_by_group.items, key=lambda x: -x[1])},
        "datasets": datasets,
    }


def human_bytes(n: int | None) -> str:
    if not n:
        return "?"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def write_markdown(cat: dict, path: str) -> None:
    L = []
    L.append("# data.opencity.in — catalogue\n")
    L.append(f"_CKAN {cat['ckan_version']} · {cat['dataset_count']} datasets · "
             f"{cat['resource_count']} resources · "
             f"{human_bytes(cat['known_bytes'])} of known-size files (many resources report no size)._\n")

    L.append("\n## Datasets per group (city)\n")
    L.append("| group | datasets | known size |")
    L.append("|---|--:|--:|")
    for g, n in cat["datasets_per_group"].items:
        L.append(f"| {g} | {n} | {human_bytes(cat['known_bytes_per_group'].get(g))} |")

    L.append("\n## Datasets per organization (publisher)\n")
    L.append("| org | datasets |")
    L.append("|---|--:|")
    for o, n in cat["datasets_per_org"].items:
        L.append(f"| {o} | {n} |")

    L.append("\n## Resource formats\n")
    L.append("| format | count |")
    L.append("|---|--:|")
    for f, n in cat["formats"].items:
        L.append(f"| {f} | {n} |")

    L.append("\n## Datasets (grouped by org)\n")
    by_org: defaultdict[str, list[dict]] = defaultdict(list)
    for d in cat["datasets"]:
        by_org[d["organization"] or "(no-org)"].append(d)
    for org in sorted(by_org):
        L.append(f"\n### {org}\n")
        for d in sorted(by_org[org], key=lambda x: x["name"] or ""):
            grp = ",".join(d["groups"]) or "-"
            fmts = ",".join(sorted({r["format"] for r in d["resources"]})) or "-"
            L.append(f"- **{d['title']}** (`{d['name']}`) — groups: {grp} · "
                     f"{d['num_resources']} resources [{fmts}] · {d['url']}")

    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


def main -> None:
    ap = argparse.ArgumentParser
    ap.add_argument("--out", required=True, help="output directory for catalogue files")
    ap.add_argument("--page-size", type=int, default=200)
    args = ap.parse_args

    os.makedirs(args.out, exist_ok=True)
    pkgs = fetch_all_packages(page_size=args.page_size)
    cat = build(pkgs)

    json_path = os.path.join(args.out, "opencity_catalogue.json")
    md_path = os.path.join(args.out, "opencity_catalogue.md")
    with open(json_path, "w") as fh:
        json.dump(cat, fh, indent=2, ensure_ascii=False)
    write_markdown(cat, md_path)

    print(f"[catalogue] wrote {json_path}", file=sys.stderr)
    print(f"[catalogue] wrote {md_path}", file=sys.stderr)
    print(f"[catalogue] {cat['dataset_count']} datasets, {cat['resource_count']} resources, "
          f"{human_bytes(cat['known_bytes'])} known size", file=sys.stderr)


if __name__ == "__main__":
    main
