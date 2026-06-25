"""Application service for Ahmedabad library-paper figure generation."""
from __future__ import annotations

from sevent4.domain.ahmedabad_library_paper_figures import assemble_figure_stats


def build_ahmedabad_library_paper_figures(store) -> dict:
    layers = store.read_layers()
    wards, libraries = layers[0], layers[1]
    access = store.render_access_proxy(wards, libraries)
    transit = store.render_transit_context(*layers)
    exclusion = store.render_exclusion_cross(wards, libraries)
    return assemble_figure_stats(access, transit, exclusion)
