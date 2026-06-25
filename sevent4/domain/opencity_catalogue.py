"""Pure shaping for the data.opencity.in CKAN catalogue: package -> manifest dict,
size coercion, human-readable bytes, and the markdown index. No network/IO here
(the adapter calls the CKAN API and writes files).

NOTE: the original recipe was corrupted (method calls missing their parentheses,
e.g. `Counter`, `.strip.upper`, `.most_common`, `.items`); those are repaired here
as part of the fix-and-refactor.
"""
from __future__ import annotations

from collections import Counter, defaultdict

BASE = "https://data.opencity.in"


def to_int(v) -> int | None:
    try:
        if v in (None, "", "None"):
            return None
        return int(float(v))
    except (TypeError, ValueError):
        return None


def human_bytes(n: int | None) -> str:
    if not n:
        return "?"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def build_catalogue(pkgs: list[dict]) -> dict:
    datasets = []
    fmt_counter: Counter[str] = Counter()
    group_counter: Counter[str] = Counter()
    org_counter: Counter[str] = Counter()
    bytes_by_group: defaultdict[str, int] = defaultdict(int)
    total_resources = 0
    total_known_bytes = 0

    for p in pkgs:
        groups = [g.get("name") for g in p.get("groups", [])]
        org = (p.get("organization") or {}).get("name")
        resources = []
        for r in p.get("resources", []):
            size = to_int(r.get("size"))
            fmt = (r.get("format") or "").strip().upper() or "UNKNOWN"
            fmt_counter[fmt] += 1
            total_resources += 1
            if size:
                total_known_bytes += size
                for g in groups or ["(no-group)"]:
                    bytes_by_group[g] += size
            resources.append({
                "id": r.get("id"), "name": r.get("name"), "format": fmt,
                "url": r.get("url"), "size_bytes": size,
                "last_modified": r.get("last_modified") or r.get("created"),
                "mimetype": r.get("mimetype"),
            })
        for g in groups:
            group_counter[g] += 1
        if org:
            org_counter[org] += 1
        datasets.append({
            "name": p.get("name"), "title": p.get("title"),
            "url": f"{BASE}/dataset/{p.get('name')}", "organization": org, "groups": groups,
            "tags": [t.get("name") for t in p.get("tags", [])],
            "notes": (p.get("notes") or "")[:500], "num_resources": len(resources),
            "metadata_modified": p.get("metadata_modified"), "resources": resources,
        })

    return {
        "source": BASE, "ckan_version": "2.11.4",
        "dataset_count": len(datasets), "resource_count": total_resources,
        "known_bytes": total_known_bytes,
        "formats": dict(fmt_counter.most_common()),
        "datasets_per_group": dict(group_counter.most_common()),
        "datasets_per_org": dict(org_counter.most_common()),
        "known_bytes_per_group": {k: v for k, v in sorted(bytes_by_group.items(), key=lambda x: -x[1])},
        "datasets": datasets,
    }


def catalogue_markdown(cat: dict) -> str:
    L = ["# data.opencity.in — catalogue\n"]
    L.append(f"_CKAN {cat['ckan_version']} · {cat['dataset_count']} datasets · "
             f"{cat['resource_count']} resources · "
             f"{human_bytes(cat['known_bytes'])} of known-size files (many resources report no size)._\n")

    L.append("\n## Datasets per group (city)\n")
    L.append("| group | datasets | known size |")
    L.append("|---|--:|--:|")
    for g, n in cat["datasets_per_group"].items():
        L.append(f"| {g} | {n} | {human_bytes(cat['known_bytes_per_group'].get(g))} |")

    L.append("\n## Datasets per organization (publisher)\n")
    L.append("| org | datasets |")
    L.append("|---|--:|")
    for o, n in cat["datasets_per_org"].items():
        L.append(f"| {o} | {n} |")

    L.append("\n## Resource formats\n")
    L.append("| format | count |")
    L.append("|---|--:|")
    for f, n in cat["formats"].items():
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
    return "\n".join(L) + "\n"
