"""Spatial analysis of the Delhi Public Library fixed network: register the
authoritative DPL layer, then compute walk-access, transit-siting, and dispersion
metrics and render the figures. Geospatial/matplotlib IO is injected via the
spatial port; this layer owns only the order and the stats shaping.
"""
from __future__ import annotations

from sevent4.domain.delhi_library_spatial import (
    assemble_stats,
    confidence_note,
    libraries_layer_spec,
    merge_layers,
)


def build_library_spatial(spatial) -> dict:
    dpl = spatial.load_dpl()
    base = spatial.load_base_layers()

    # ---- authoritative DPL layer for the console ----
    spatial.write_dpl_layer(dpl)
    spatial.write_manifest(merge_layers(spatial.read_manifest(), [libraries_layer_spec()]))

    analysis = spatial.analyse(dpl, base)
    m = analysis.metrics
    note = confidence_note(m["hi"], m["pins"], m["approx"])
    spatial.render_walk_access(analysis, note)
    spatial.render_transit_siting(analysis)

    stats = assemble_stats(m)
    spatial.write_stats(stats)
    return stats
