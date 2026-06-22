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
from pathlib import Path

from sevent4.adapters.filesystem import FilePollutionBoardCapacityRepository, JsonFilePublicSurfaceWriter
from sevent4.application.why_air import publish_pollution_board_table

CITIES_DIR = Path("data/cities")
OUT = Path("public/why/air/boards.json")


def build(cities_dir=CITIES_DIR, out=OUT, verbose=True):
    out = Path(out)
    document = publish_pollution_board_table(
        FilePollutionBoardCapacityRepository(cities_dir),
        JsonFilePublicSurfaceWriter(out),
    )
    boards = document["boards"]
    if verbose:
        live = sum(b["status"] == "live" for b in boards)
        print(f"wrote {out} — {len(boards)} cities ({live} with data, {len(boards)-live} pending)")
        for b in boards:
            pct = f'{b["vacancy_pct"]}%' if b["vacancy_pct"] is not None else "pending"
            print(f'  {b["name"]:<12} {b["board"]:<7} {pct:>8}  [{b["tier"]}]')
    return document


if __name__ == "__main__":
    build()
