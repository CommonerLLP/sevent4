"""Application service for Delhi Public Library paper figure generation."""
from __future__ import annotations

from sevent4.domain.delhi_library_paper_figures import decline_stats, finance_stats


def build_delhi_library_paper_figures(store) -> dict:
    rows = store.load_metrics()
    decline = decline_stats(rows)
    finance = finance_stats(rows)
    store.render_decline(rows, decline)
    store.render_finance(rows, finance)
    return {"decline": decline, "finance": finance}
