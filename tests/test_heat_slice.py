import ast
import unittest
from pathlib import Path

import numpy as np

from sevent4.application.heat import (
    HeatGrid,
    aggregate_ward_heat,
    build_city_heat,
    patch_heat_manifest,
)
from sevent4.domain.heat import (
    HEAT30M_LAYER,
    WARD_HEAT_LAYER,
    celsius_from_landsat_st,
    heat_rgba,
    patched_manifest_layers,
    qa_mask,
    ward_lst_stats,
)

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "scripts" / "recipes" / "ahmedabad"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class HeatRecipeArchitectureTest(unittest.TestCase):
    def test_heat_recipes_do_not_own_io_and_route_through_ports(self) -> None:
        for name in (
            "build_heat_layer.py",
            "aggregate_ward_heat.py",
            "patch_heat_manifest.py",
            "_run_all_heat.py",
        ):
            imports = _imports(RECIPES / name)
            for forbidden in ("json", "csv", "numpy", "rasterio", "subprocess", "yaml"):
                self.assertNotIn(forbidden, imports, f"{name} should not own {forbidden} IO")
            self.assertTrue(
                any(module.startswith("sevent4.adapters.heat") for module in imports),
                f"{name} should route through a heat adapter",
            )
            self.assertIn("sevent4.application.heat", imports, f"{name} should use the heat application")


class HeatDomainTest(unittest.TestCase):
    def test_qa_mask_rejects_fill_and_flagged_bits(self) -> None:
        # 0=fill, 8=cloud(bit3), 2=dilated-cloud(bit1) are bad; 1(bit0) and 32(bit5) are usable.
        qa = np.array([[0, 8, 2], [1, 32, 16]], dtype="uint16")
        mask = qa_mask(qa)
        self.assertFalse(mask[0, 0])  # fill value 0
        self.assertFalse(mask[0, 1])  # cloud bit 3
        self.assertFalse(mask[0, 2])  # dilated-cloud bit 1
        self.assertTrue(mask[1, 0])   # bit 0 not masked
        self.assertTrue(mask[1, 1])   # bit 5 not masked
        self.assertFalse(mask[1, 2])  # cloud-shadow bit 4

    def test_celsius_conversion_masks_bad_and_out_of_range(self) -> None:
        st = np.array([[44000, 0]], dtype="float32")
        good = np.array([[True, True]])
        celsius = celsius_from_landsat_st(st, good)
        self.assertTrue(np.isfinite(celsius[0, 0]))
        self.assertTrue(np.isnan(celsius[0, 1]))  # fill 0 -> NaN

    def test_heat_rgba_makes_nan_transparent(self) -> None:
        data = np.array([[36.0, np.nan]], dtype="float32")
        rgba = heat_rgba(data)
        self.assertEqual(rgba[0, 0, 3], 220)
        self.assertEqual(rgba[0, 1, 3], 0)

    def test_ward_lst_stats_filters_range_and_nodata(self) -> None:
        values = np.array([35.0, 40.0, np.nan, 999.0, -999.0])
        mean_c, max_c, count = ward_lst_stats(values, nodata=None)
        self.assertEqual(count, 2)
        self.assertEqual(max_c, 40.0)
        self.assertEqual(mean_c, 37.5)
        self.assertEqual(ward_lst_stats(None, None), (None, None, 0))

    def test_patched_manifest_layers_is_idempotent(self) -> None:
        base = [{"id": "wards"}, dict(WARD_HEAT_LAYER)]
        once = patched_manifest_layers(base, (WARD_HEAT_LAYER, HEAT30M_LAYER))
        twice = patched_manifest_layers(once, (WARD_HEAT_LAYER, HEAT30M_LAYER))
        self.assertEqual([layer["id"] for layer in once], ["wards", "ward_heat", "heat30m"])
        self.assertEqual(once, twice)


class HeatApplicationTest(unittest.TestCase):
    def test_aggregate_ward_heat_uses_sampler_and_summarises(self) -> None:
        wards = {
            "features": [
                {"properties": {"Name": "A"}, "geometry": {"type": "Polygon", "coordinates": []}},
                {"properties": {"Name": "B"}, "geometry": {"type": "Polygon", "coordinates": []}},
                {"properties": {"Name": "C"}, "geometry": None},
            ]
        }
        samples = {0: np.array([35.0, 37.0]), 1: np.array([np.nan])}
        calls = {"n": 0}

        def sample(_geometry):
            index = calls["n"]
            calls["n"] += 1
            return samples.get(index)

        document, summary = aggregate_ward_heat(wards, sample, nodata=None)
        self.assertEqual(summary["wards"], 3)
        self.assertEqual(summary["wards_with_lst"], 1)
        self.assertEqual(document["features"][0]["properties"]["mean_lst_c"], 36.0)
        self.assertEqual(document["features"][2]["properties"]["lst_px_count"], 0)
        self.assertEqual(document["name"], "ward_heat")

    def test_build_city_heat_summarises_grid(self) -> None:
        data = np.array([[35.0, 40.0], [np.nan, 38.0]], dtype="float32")
        grid = HeatGrid(
            data=data,
            lon=np.array([72.0, 72.1]),
            lat=np.array([23.1, 23.0]),
            bounds=[72.0, 23.0, 72.1, 23.1],
            scene_log=[{"id": "x"}, {"id": "y"}],
        )
        artifacts = build_city_heat("ahmedabad", grid)
        self.assertEqual(artifacts.summary["scenes"], 2)
        self.assertEqual(artifacts.summary["max_c"], 40.0)
        self.assertEqual(artifacts.bounds_doc["bbox"], [72.0, 23.0, 72.1, 23.1])
        self.assertEqual(artifacts.rgba.shape, (2, 2, 4))

    def test_patch_heat_manifest_adds_climate_layers(self) -> None:
        manifest = {"layers": [{"id": "wards"}]}
        patched = patch_heat_manifest(manifest)
        self.assertEqual([layer["id"] for layer in patched["layers"]], ["wards", "ward_heat", "heat30m"])
        self.assertEqual(manifest["layers"], [{"id": "wards"}])  # input untouched


if __name__ == "__main__":
    unittest.main()
