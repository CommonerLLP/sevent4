"""Pure result shaping for Ahmedabad library-paper figures."""
from __future__ import annotations


def assemble_figure_stats(access: dict, transit: dict, exclusion: dict) -> dict:
    return {"access": access, "transit": transit, "exclusion": exclusion}
