#!/usr/bin/env python3
"""Scope (do NOT download) the OpenCity catalogue against the 74th-Amendment atlas frame.

Reads the catalogue JSON produced by opencity_catalogue.py and, for a set of cities,
classifies every dataset against the atlas's analytical axes:

  decides   — who governs: parastatals, development authorities, devolution, council,
              elections, wards (the elected vs unelected city)
  profits   — land, planning, FSI/TDR, property, real estate, rent capture
  pays      — budgets, municipal finance, property tax, revenue, fees, audit (CAG)
  labours   — sanitation/conservancy workers, contract labour, SHGs, welfare
  function  — the 18 Twelfth-Schedule functions (water, sewerage, solid waste, roads,
              transport, health, education, parks, fire, streetlight, slums, poverty…)
  base      — enabling geography (ward/admin boundaries) the atlas needs to join anything

Multi-label: a dataset can serve several axes. Output is a markdown scoping note —
title, URL, publisher org, formats, resource count — grouped by axis, per city, with a
high-value shortlist. No files are fetched.

Usage:
  python3 scripts/recipes/scope_opencity_for_atlas.py \
    --catalogue data/sources/opencity/_catalogue/opencity_catalogue.json \
    --cities bengaluru chennai kolkata mumbai \
    --out docs/opencity-atlas-scope.md
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict

# Axis -> keyword patterns (matched against title + tags + notes + org, lowercased).
# Ordered roughly by the four-axis machine, then the 18 functions, then base geography.
AXES: dict[str, list[str]] = {
    "decides": [
        r"\bward", r"councillor", r"corporator", r"election", r"electoral", r"voter",
        r"delimitation", r"development authority", r"\bda\b", r"metropolitan", r"parastatal",
        r"governance", r"council", r"municipal council", r"mayor", r"standing committee",
        r"smart city", r"\bspv\b", r"jurisdiction", r"zone", r"administ",
    ],
    "profits": [
        r"land use", r"land-use", r"\blanduse\b", r"\bland\b", r"master plan", r"\bcdp\b",
        r"\btdr\b", r"\bfsi\b", r"floor space", r"premium", r"betterment", r"real estate",
        r"property\b(?!.*tax)", r"plot", r"building perm/?", r"layout", r"redevelopment",
        r"\bdcr\b", r"planning", r"survey number", r"khata",
    ],
    "pays": [
        r"budget", r"finance", r"financial", r"revenue", r"expenditure", r"property tax",
        r"\btax\b", r"\bcess\b", r"user fee", r"tariff", r"grant", r"\bcag\b", r"audit",
        r"receipts", r"income", r"collection", r"arrear", r"fund", r"borrow", r"bond",
    ],
    "labours": [
        r"sanitation worker", r"conservancy", r"safai", r"pourakarmika", r"contract labour",
        r"contract worker", r"\bshg\b", r"self help", r"\bnulm\b", r"welfare", r"pension",
        r"manual scaveng", r"sewer death", r"powrakarmika", r"labour",
    ],
    "function": [
        r"water", r"sewer", r"sewage", r"drainage", r"solid waste", r"\bswm\b", r"garbage",
        r"\broad", r"transport", r"\bbus\b", r"metro", r"traffic", r"mobility", r"\bbrts?\b",
        r"health", r"hospital", r"phc", r"clinic", r"\bschool", r"education", r"\bpark",
        r"\bfire\b", r"street ?light", r"slum", r"poverty", r"toilet", r"public toilet",
        r"\bswd\b", r"storm water", r"lake", r"tree", r"environment", r"pollution", r"air quality",
        r"birth", r"death", r"\bcrematori", r"market", r"library", r"playground",
    ],
    "base": [
        r"ward boundar", r"ward map", r"administrative boundar", r"admin boundar",
        r"\bboundary", r"\bgis\b", r"basemap", r"base map", r"shapefile", r"village boundar",
    ],
}

AXIS_LABEL = {
    "decides": "WHO DECIDES — governance / parastatals / elections / wards",
    "profits": "WHO PROFITS — land / planning / property / rent",
    "pays": "WHO PAYS — budgets / finance / tax / audit",
    "labours": "WHO LABOURS — sanitation / contract / welfare",
    "function": "THE 18 FUNCTIONS — services delivered (or not)",
    "base": "BASE GEOGRAPHY — boundaries / GIS the atlas joins on",
}

COMPILED = {ax: [re.compile(p) for p in pats] for ax, pats in AXES.items()}

# The three representative cuts the atlas must be able to slice any geo by.
# A dataset only counts as a usable CUT if it carries boundary GEOMETRY
# (polygon formats), not merely results tabulated by AC/PC.
CUT_PATTERNS: dict[str, list[str]] = {
    "ward": [r"\bward", r"ward boundar", r"ward map", r"ward delimit"],
    "assembly": [r"assembly constituenc", r"\bac boundar", r"vidhan sabha",
                 r"legislative assembly", r"\bassembly\b", r"\bvidhansabha"],
    "parliament": [r"parliament", r"lok sabha", r"parliamentary constituenc",
                   r"\bpc boundar", r"loksabha"],
}
CUT_COMPILED = {c: [re.compile(p) for p in pats] for c, pats in CUT_PATTERNS.items()}
GEOM_FORMATS = {"KML", "KMZ", "GEOJSON", "JSON", "SHP", "ZIP"}  # ZIP often = shapefile bundle
CUT_LABEL = {"ward": "ward", "assembly": "assembly (AC)", "parliament": "parliament (PC)"}


def cut_hits(d: dict) -> dict[str, bool]:
    """For each of the 3 cuts, does this dataset name it AND carry geometry?"""
    hay = " ".join([(d.get("title") or ""), " ".join(d.get("tags") or []),
                    (d.get("name") or ""), (d.get("notes") or "")]).lower()
    has_geom = any(r["format"] in GEOM_FORMATS for r in d.get("resources", []))
    out = {}
    for cut, regs in CUT_COMPILED.items():
        named = any(r.search(hay) for r in regs)
        out[cut] = bool(named and has_geom)
    return out


def classify(d: dict) -> set[str]:
    hay = " ".join([
        (d.get("title") or ""),
        " ".join(d.get("tags") or []),
        (d.get("notes") or ""),
        (d.get("organization") or ""),
        (d.get("name") or ""),
    ]).lower()
    hits = set()
    for ax, regs in COMPILED.items():
        if any(r.search(hay) for r in regs):
            hits.add(ax)
    return hits


def fmts_of(d: dict) -> str:
    return ",".join(sorted({r["format"] for r in d.get("resources", [])})) or "-"


def has_structured(d: dict) -> bool:
    struct = {"CSV", "GEOJSON", "KML", "KMZ", "XLSX", "XLS", "JSON"}
    return any(r["format"] in struct for r in d.get("resources", []))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", required=True)
    ap.add_argument("--cities", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cat = json.load(open(args.catalogue))
    datasets = cat["datasets"]

    L: list[str] = []
    L.append("# OpenCity → sevent4 atlas — scoping map (74th Amendment)\n")
    L.append("_What in `data.opencity.in` can improve the atlas. Scoping only — nothing downloaded. "
             "Generated by `scripts/recipes/scope_opencity_for_atlas.py`. "
             "Each dataset is multi-labelled against the four-axis machine + the 18 functions; "
             "a dataset can appear under several axes._\n")
    L.append("\n**Credit line for anything ingested:** every dataset below is published on "
             "OpenCity (`data.opencity.in`) by the listed publisher org; on ingestion we cite "
             "_publisher → OpenCity → sevent4 (processed)_ and link the dataset URL.\n")

    grand_axis_counts: dict[str, int] = defaultdict(int)

    for city in args.cities:
        ds = [d for d in datasets if city in (d.get("groups") or [])]
        # classify
        by_axis: dict[str, list[dict]] = defaultdict(list)
        atlas_relevant = 0
        for d in ds:
            hits = classify(d)
            if hits:
                atlas_relevant += 1
            for ax in hits:
                by_axis[ax].append(d)
                grand_axis_counts[ax] += 1

        L.append(f"\n---\n\n## {city.title()}  ·  {len(ds)} datasets  ·  "
                 f"{atlas_relevant} atlas-relevant\n")
        # axis summary line
        summary = "  ".join(f"{ax}:{len(by_axis[ax])}" for ax in AXES if by_axis[ax])
        L.append(f"_axis coverage:_ {summary}\n")

        # --- CUT GEOMETRY: can we slice this city by ward / AC / PC? ---
        cut_sets: dict[str, list[dict]] = {c: [] for c in CUT_PATTERNS}
        for d in ds:
            for cut, ok in cut_hits(d).items():
                if ok:
                    cut_sets[cut].append(d)
        verdict = "  ".join(
            f"{CUT_LABEL[c]}: {'✅ '+str(len(cut_sets[c])) if cut_sets[c] else '❌ none'}"
            for c in CUT_PATTERNS
        )
        L.append(f"\n### ⬛ CUT GEOMETRY (slice-by) — {verdict}\n")
        for c in CUT_PATTERNS:
            if cut_sets[c]:
                for d in cut_sets[c]:
                    L.append(f"- _{CUT_LABEL[c]}_: **{d['title']}** — {d['organization'] or '-'} · "
                             f"[{fmts_of(d)}] · {d['url']}")
            else:
                L.append(f"- _{CUT_LABEL[c]}_: **no boundary geometry on OpenCity** — "
                         f"source elsewhere (ECI maps / DataMeet / Census / state SEC).")

        for ax in AXES:
            items = by_axis.get(ax) or []
            if not items:
                continue
            L.append(f"\n### {AXIS_LABEL[ax]}  ({len(items)})\n")
            # sort: structured-first, then by resource count desc
            items.sort(key=lambda x: (not has_structured(x), -x["num_resources"]))
            for d in items:
                star = "★" if has_structured(d) else " "
                L.append(f"- {star} **{d['title']}** — {d['organization'] or '-'} · "
                         f"{d['num_resources']} res [{fmts_of(d)}] · {d['url']}")

        # datasets matching nothing — surface so the frame's blind spots are visible
        unmatched = [d for d in ds if not classify(d)]
        if unmatched:
            L.append(f"\n### (unclassified — {len(unmatched)}; frame may be missing a keyword)\n")
            for d in unmatched[:40]:
                L.append(f"-   {d['title']} — {d['organization'] or '-'} · {fmts_of(d)} · {d['url']}")
            if len(unmatched) > 40:
                L.append(f"- _…and {len(unmatched)-40} more_")

    # legend
    L.insert(4, "\n_★ = has at least one structured (CSV/GeoJSON/KML/XLSX/JSON) resource — "
                "directly atlas-feedable; unstarred = PDF/scan only._\n")

    with open(args.out, "w") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"wrote {args.out}")
    print("axis totals across cities:", dict(grand_axis_counts))


if __name__ == "__main__":
    main()
