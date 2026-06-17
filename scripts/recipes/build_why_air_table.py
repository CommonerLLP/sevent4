#!/usr/bin/env python3
"""Publish the WHY/air board-capacity league table.

Reads each ready city's gitignored capacity layer
(`data/cities/<city>/source/pollution/capacity.json`) and emits a small,
public, sanitised roster (`public/why/air/boards.json`) that the chapter page
renders into a ranked, scalable grid. Adding/acquiring a city = re-run this; no
HTML is hand-edited. Status-honest: a city with no acquired count is published
as `pending`, never a fabricated number.

Run: .venv/bin/python scripts/recipes/build_why_air_table.py
"""
import json
from pathlib import Path

CITIES_DIR = Path("data/cities")
OUT = Path("public/why/air/boards.json")

# pretty names + the worked-example deep-dives that have bespoke narrative
DISPLAY = {
    "ahmedabad": "Ahmedabad", "bengaluru": "Bengaluru", "chennai": "Chennai",
    "delhi": "Delhi", "kolkata": "Kolkata",
}
FEATURED = {"delhi", "kolkata"}  # cities with a hand-built deep-dive on the page


def _latest(facts, metric):
    """Most recent non-null fact for a metric, preferring status=found."""
    rows = [f for f in facts if f.get("metric") == metric and f.get("value") is not None]
    if not rows:
        return None
    rows.sort(key=lambda f: (f.get("status") == "found", str(f.get("year", ""))), reverse=True)
    return rows[0]


def build():
    boards = []
    for cap_path in sorted(CITIES_DIR.glob("*/source/pollution/capacity.json")):
        city = cap_path.parts[2]
        data = json.loads(cap_path.read_text(encoding="utf-8"))
        facts = data.get("facts", [])
        board = data.get("board", "")

        sanc = _latest(facts, "posts_sanctioned")
        vac = _latest(facts, "posts_vacant")
        pct_fact = _latest(facts, "vacancy_pct")

        sanctioned = sanc["value"] if sanc else None
        vacant = vac["value"] if vac else None
        pct = None
        if pct_fact and isinstance(pct_fact["value"], (int, float)):
            pct = round(pct_fact["value"])
        elif isinstance(sanctioned, (int, float)) and isinstance(vacant, (int, float)) and sanctioned:
            pct = round(vacant / sanctioned * 100)

        if pct is None:
            status, tier = "pending", "pending"
        else:
            # confidence of the underlying staffing fact -> primary vs reported
            conf = (sanc or vac or pct_fact or {}).get("confidence", "low")
            tier = "primary" if conf == "high" else "reported"
            status = "live"

        boards.append({
            "city": city,
            "name": DISPLAY.get(city, city.title()),
            "board": board,
            "sanctioned": sanctioned,
            "vacant": vacant,
            "vacancy_pct": pct,
            "status": status,
            "tier": tier,
            "featured": city in FEATURED,
            "console": f"../../cities/{city}/index.html",
        })

    # ranked worst-empty first; pending cities fall to the bottom
    boards.sort(key=lambda b: (b["vacancy_pct"] is None, -(b["vacancy_pct"] or 0)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"boards": boards}, indent=2) + "\n", encoding="utf-8")
    live = sum(b["status"] == "live" for b in boards)
    print(f"wrote {OUT} — {len(boards)} cities ({live} with data, {len(boards)-live} pending)")
    for b in boards:
        pct = f'{b["vacancy_pct"]}%' if b["vacancy_pct"] is not None else "pending"
        print(f'  {b["name"]:<12} {b["board"]:<7} {pct:>8}  [{b["tier"]}]')


if __name__ == "__main__":
    build()
