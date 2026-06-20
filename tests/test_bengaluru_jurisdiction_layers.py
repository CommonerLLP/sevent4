"""Deterministic validation for the Bengaluru OpenCity authority-jurisdiction layers.

Each authority (GBA, BDA, BWSSB, traffic police) cuts Bengaluru on a different
boundary than BBMP wards. These checks enforce the queue discipline: file exists,
nonzero features, WGS84 coordinates inside the Bengaluru box, required attribute
present, and provenance with confidence + absence semantics.

Layer GeoJSON + provenance live under gitignored data/ paths, so the suite skips
when the build has not been run locally.
"""

import json
import unittest
from pathlib import Path

BLR = Path("data/cities/bengaluru")
LAYERS = BLR / "layers"
SOURCES = BLR / "source" / "opencity" / "sources.json"

LON_MIN, LON_MAX = 77.2, 77.9
LAT_MIN, LAT_MAX = 12.7, 13.3

LAYERS_REQUIRED_ATTR = {
    "gba_corporations": "corporatio",
    "gba_zones": "Zone",
    "bda_zones": "AEE name",
    "bwssb_divisions": "DivisionName",
    "traffic_police_jurisdiction": "PS_BOUNDName",
    "bbmp_dry_waste_centres": "DWCCName",
    "bbmp_landfills": "Land_FillsName",
}

_built = all((LAYERS / f"{lid}.geojson").exists() for lid in LAYERS_REQUIRED_ATTR)


def _coords(geom):
    def walk(c):
        if c and isinstance(c[0], (int, float)):
            yield c[0], c[1]
        else:
            for sub in c:
                yield from walk(sub)
    if geom and geom.get("coordinates") is not None:
        yield from walk(geom["coordinates"])


@unittest.skipUnless(_built, "Bengaluru jurisdiction layers not built (run build_opencity_jurisdiction_layers.py)")
class BengaluruJurisdictionLayersTest(unittest.TestCase):
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

    def test_gba_has_five_corporations(self):
        fc = self._load("gba_corporations")
        self.assertEqual(len(fc["features"]), 5,
                         "GBA 2025 delimitation should carve five corporations")

    def test_coordinates_are_wgs84_in_bengaluru(self):
        for lid in LAYERS_REQUIRED_ATTR:
            for ft in self._load(lid).get("features", [])[:50]:
                for lon, lat in _coords(ft.get("geometry") or {}):
                    self.assertTrue(LON_MIN <= lon <= LON_MAX, f"{lid}: lon {lon} out of range")
                    self.assertTrue(LAT_MIN <= lat <= LAT_MAX, f"{lid}: lat {lat} out of range")

    def test_provenance_complete(self):
        self.assertTrue(SOURCES.exists(), "missing opencity sources.json")
        meta = json.loads(SOURCES.read_text())
        for lid in LAYERS_REQUIRED_ATTR:
            rec = meta["layers"].get(lid)
            self.assertIsNotNone(rec, f"{lid}: no provenance record")
            self.assertTrue(rec.get("publisher"), f"{lid}: no publisher")
            self.assertTrue(rec.get("confidence"), f"{lid}: no confidence")
            self.assertTrue(rec.get("absence_means"), f"{lid}: no absence semantics")


if __name__ == "__main__":
    unittest.main()
