"""Validation for the AMC 2024 wards cross-check layer (OpenCity).

Ingested as a coded cross-check only; the enriched wards.geojson is unchanged.
Skips when the layer has not been built locally (gitignored data/).
"""
import json, unittest
from pathlib import Path

AMD = Path("data/cities/ahmedabad")
LAYER = AMD / "layers" / "wards_2024.geojson"
SOURCES = AMD / "source" / "opencity" / "sources.json"


@unittest.skipUnless(LAYER.exists(), "wards_2024 not built")
class AhmedabadWards2024Test(unittest.TestCase):
    def test_48_wards_with_lgd_codes(self):
        fc = json.loads(LAYER.read_text())
        feats = fc["features"]
        self.assertEqual(len(feats), 48, "AMC has 48 wards")
        p = feats[0]["properties"]
        for attr in ("ward_name", "ward_no", "ward_lgd_code"):
            self.assertIn(attr, p, f"missing {attr}")

    def test_does_not_overwrite_enriched_wards(self):
        # the canonical enriched layer must still exist and carry its derived metrics
        wards = json.loads((AMD / "layers" / "wards.geojson").read_text())
        self.assertIn("deprivation", wards["features"][0]["properties"])

    def test_provenance_marks_crosscheck(self):
        meta = json.loads(SOURCES.read_text())
        rec = meta["layers"]["wards_2024"]
        self.assertTrue(rec.get("confidence"))
        self.assertIn("cross-check", rec.get("absence_means", "").lower())
