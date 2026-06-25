#!/usr/bin/env python3
"""Build Ahmedabad library figures for the public-libraries paper."""
from __future__ import annotations

import sevent4.adapters.ahmedabad_library_paper_figures_geospatial as figure_store
from sevent4.application.ahmedabad_library_paper_figures import build_ahmedabad_library_paper_figures
from sevent4.domain.ahmedabad_library_paper_figures import assemble_figure_stats


_read_layers = figure_store.read_layers
fig_access_proxy = figure_store.render_access_proxy
fig_transit_context = figure_store.render_transit_context
fig_exclusion_cross = figure_store.render_exclusion_cross


def main() -> None:
    result = build_ahmedabad_library_paper_figures(figure_store)
    print("Ahmedabad figure stats:")
    print(result["access"])
    print(result["transit"])
    print(result["exclusion"])
    print("Figures written to", figure_store.FIG)


if __name__ == "__main__":
    main()
