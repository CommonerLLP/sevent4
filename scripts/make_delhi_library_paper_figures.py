#!/usr/bin/env python3
"""Figures for the Delhi Public Library paper."""
from __future__ import annotations

import sevent4.adapters.delhi_library_paper_figures_matplotlib as figure_store
from sevent4.application.delhi_library_paper_figures import build_delhi_library_paper_figures
from sevent4.domain.delhi_library_paper_figures import decline_stats, finance_stats


def fig_decline() -> dict:
    rows = figure_store.load_metrics()
    stats = decline_stats(rows)
    return figure_store.render_decline(rows, stats)


def fig_finance() -> dict:
    rows = figure_store.load_metrics()
    stats = finance_stats(rows)
    return figure_store.render_finance(rows, stats)


def main() -> None:
    build_delhi_library_paper_figures(figure_store)
    print("Delhi figures written to", figure_store.FIG)


if __name__ == "__main__":
    main()
