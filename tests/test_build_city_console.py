import json
import tempfile
import unittest
from pathlib import Path

from sevent4.build_city_console import (
    CITY_READINESS,
    READY_CITIES,
    _feature_options,
    _js,
    _layer_json,
    _toggles,
)
from sevent4.city_dataset import CityDataset
from sevent4.layer_manifest import LayerSpec


class FeatureOptionsTest(unittest.TestCase):
    def test_feature_options_can_be_limited_to_allowed_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pcs.geojson"
            path.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "properties": {"pc_name": "Crosswalk PC"},
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
                                    ],
                                },
                            },
                            {
                                "type": "Feature",
                                "properties": {"pc_name": "Outside PC"},
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]
                                    ],
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            html = _feature_options(path, "pc_name", allowed={"Crosswalk PC"})

        self.assertIn("Crosswalk PC", html)
        self.assertNotIn("Outside PC", html)

    def test_every_city_with_a_crosswalk_is_ready(self) -> None:
        crosswalk_cities = {
            path.parent.parent.name
            for path in Path("data/cities").glob("*/layers/jurisdiction_crosswalk.json")
        }

        self.assertLessEqual(READY_CITIES, crosswalk_cities)

    def test_ready_cities_are_the_approved_selectable_set(self) -> None:
        self.assertEqual(
            READY_CITIES,
            {"ahmedabad", "bengaluru", "chennai", "delhi", "kolkata"},
        )

    def test_finance_grades_use_standard_keywords(self) -> None:
        standard_grades = {"strong", "partial", "research_only", "missing", "special_case_partial"}

        self.assertLessEqual(
            {grades["finance_grade"] for grades in CITY_READINESS.values()},
            standard_grades,
        )
        for grades in CITY_READINESS.values():
            self.assertNotIn("ahmedabad", grades["finance_grade"])

        self.assertEqual(CITY_READINESS["ahmedabad"]["finance_grade"], "strong")
        self.assertEqual(CITY_READINESS["delhi"]["finance_grade"], "special_case_partial")
        self.assertEqual(CITY_READINESS["kolkata"]["finance_grade"], "research_only")

    def test_layer_json_carries_year_control_metadata(self) -> None:
        city = CityDataset(
            id="test",
            name="Test City",
            country="India",
            state="State",
            center=(0.0, 0.0),
            bbox=(0.0, 0.0, 1.0, 1.0),
            crs_metric="EPSG:3857",
            layers_dir=Path("."),
            source_dir=Path("."),
            outputs_dir=Path("."),
            config_path=Path("city.yaml"),
            repo_root=Path("."),
        )
        layer = LayerSpec(
            id="ward_workorders_yearly",
            label="BBMP works spend by ward, by year",
            file="ward_workorders_yearly.geojson",
            kind="fill",
            default=False,
            group="Who pays",
            popup=("Ward", "year", "works_spend_cr"),
            paint={"fill-color": "#1f6f8b", "fill-opacity": 0.6},
            outline=True,
            year_field="year",
            year_values=(2013, 2014),
            default_year=2014,
        )

        data = _layer_json(layer, city)

        self.assertEqual(data["yearField"], "year")
        self.assertEqual(data["yearValues"], [2013, 2014])
        self.assertEqual(data["defaultYear"], 2014)

    def test_toggles_render_compact_year_selector_for_timeline_layers(self) -> None:
        layer = LayerSpec(
            id="ward_workorders_yearly",
            label="BBMP works spend by ward, by year",
            file="ward_workorders_yearly.geojson",
            kind="fill",
            default=False,
            group="Who pays",
            popup=("Ward", "year", "works_spend_cr"),
            paint={"fill-color": "#1f6f8b", "fill-opacity": 0.6},
            outline=True,
            year_field="year",
            year_values=(2013, 2014),
            default_year=2014,
        )

        html = _toggles({"Who pays": [layer]})

        self.assertIn("data-year-layer='ward_workorders_yearly'", html)
        self.assertIn("<option value='2014' selected>2014</option>", html)

    def test_generated_script_keeps_maplibre_qa_hooks_valid(self) -> None:
        script = _js()

        self.assertIn("window.__sevent4Map = map;", script)
        self.assertLess(
            script.index("DefaultViewControl.prototype.onAdd"),
            script.index("map.addControl(new DefaultViewControl()"),
        )
        self.assertNotIn('"line-color": "var(--ink)"', script)


if __name__ == "__main__":
    unittest.main()
