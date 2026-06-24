from __future__ import annotations

from dataclasses import dataclass

from sevent4.domain.kanpur_wards import KanpurAnalysis, enrich_wards, summary_lines


@dataclass
class KanpurResult:
    wards: dict
    analysis: KanpurAnalysis
    summary_lines: list[str]


def analyze_kanpur_wards(wards: dict, heat: dict) -> KanpurResult:
    """Enrich the partial Kanpur ward layer (area/density/heat/coverage +
    heat-vulnerability) and build the partial-only summary. Mutates `wards`."""
    analysis = enrich_wards(wards, heat)
    return KanpurResult(wards=wards, analysis=analysis, summary_lines=summary_lines(analysis))
