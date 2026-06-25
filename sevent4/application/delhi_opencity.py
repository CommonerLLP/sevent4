"""Build Delhi's OpenCity atlas layers: villages, dissolved districts, and water
bodies, then register them in the layer manifest. Geospatial/filesystem IO is
injected via the layers port; this layer owns only the build order and merge.
"""
from __future__ import annotations

from sevent4.domain.delhi_opencity import layer_specs, merge_layers


def build_opencity_layers(layers) -> dict[str, int]:
    villages = layers.build_villages()
    districts = layers.build_districts(villages)
    water = layers.build_water()

    layers.write_layer(villages, "villages.geojson")
    layers.write_layer(districts, "districts.geojson")
    layers.write_layer(water, "water.geojson")

    manifest = merge_layers(layers.read_manifest(), layer_specs())
    layers.write_manifest(manifest)

    return {"villages": len(villages), "districts": len(districts), "water": len(water)}
