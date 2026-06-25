"""Deterministic validation for the Chennai OpenCity water/flood layers.

Enforces the acquisition discipline from docsx/ready-city-geo-layer-queue.md for
every promoted layer: file exists, nonzero features, WGS84 coordinates inside the
Chennai bounding box, required attribute present, and a provenance record in
source/opencity/sources.json carrying explicit confidence + absence semantics.

The layer GeoJSON and the provenance file live under gitignored data/ paths, so
the suite skips when the build has not been run locally.
"""

import json
import unittest
from pathlib import Path

CHENNAI = Path("data/cities/chennai")
LAYERS = CHENNAI / "layers"
SOURCES = CHENNAI / "source" / "opencity" / "sources.json"

# Chennai NCT-ish bounding box (lon, lat)
LON_MIN, LON_MAX = 79.9, 80.5
LAT_MIN, LAT_MAX = 12.7, 13.4

# layer id -> an attribute that must survive the build (the analytic payload)
LAYERS_REQUIRED_ATTR = {
    "flood_hazard": "CATEGORY",
    "flood_inundation": "DEPTH",
    "flood_2015": "ZONE",
    "stormwater_drains": "DRAIN_TYPE",
    "cmwssb_depots": "depot",
    "sewer_command_area": "name_of_the_sps",
    "water_overhead_tanks": "capacity_of_oht_ml",
}

_built = all((LAYERS / f"{lid}.geojson").exists() for lid in LAYERS_REQUIRED_ATTR)


def _coords(geom):
    """Yield (lon, lat) pairs from any GeoJSON geometry."""
    def walk(c):
        if c and isinstance(c[0], (int, float)):
            yield c[0], c[1]
        else:
            for sub in c:
                yield from walk(sub)
    if geom and geom.get("coordinates") is not None:
        yield from walk(geom["coordinates"])


@unittest.skipUnless(_built, "Chennai water/flood layers not built (run build_opencity_water_layers.py)")
class ChennaiWaterFloodLayersTest(unittest.TestCase):
    def _load(self, lid):
        return json.loads((LAYERS / f"{lid}.geojson").read_text())

    def test_layers_nonempty_with_required_attr(self):
        for lid, attr in LAYERS_REQUIRED_ATTR.items():
            fc = self._load(lid)
            feats = fc.get("features", [])
            self.assertGreater(len(feats), 0, f"{lid}: zero features")
            self.assertIn(attr, feats[0].get("properties", {}),
                          f"{lid}: missing required attribute {attr}")
            self.assertIn("source", feats[0]["properties"], f"{lid}: no source tag")

    def test_coordinates_are_wgs84_in_chennai(self):
        for lid in LAYERS_REQUIRED_ATTR:
            fc = self._load(lid)
            # sample the first 50 features for speed
            for ft in fc.get("features", [])[:50]:
                for lon, lat in _coords(ft.get("geometry") or {}):
                    self.assertTrue(LON_MIN <= lon <= LON_MAX,
                                    f"{lid}: lon {lon} out of Chennai range")
                    self.assertTrue(LAT_MIN <= lat <= LAT_MAX,
                                    f"{lid}: lat {lat} out of Chennai range")

    def test_provenance_complete(self):
        self.assertTrue(SOURCES.exists(), "missing opencity sources.json")
        meta = json.loads(SOURCES.read_text())
        # every public-domain dataset must name a publisher + license
        for slug, ds in meta["datasets"].items():
            self.assertTrue(ds.get("publisher"), f"{slug}: no publisher")
            self.assertTrue(ds.get("license"), f"{slug}: no license")
        # every promoted layer needs confidence + absence semantics
        for lid in LAYERS_REQUIRED_ATTR:
            rec = meta["layers"].get(lid)
            self.assertIsNotNone(rec, f"{lid}: no provenance record")
            self.assertTrue(rec.get("confidence"), f"{lid}: no confidence stated")
            self.assertTrue(rec.get("absence_means"), f"{lid}: no absence semantics")


if __name__ == "__main__":
    unittest.main()
