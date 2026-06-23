import json
import tempfile
import unittest
from pathlib import Path

from sevent4.build_city_console import (
    CITY_READINESS,
    READY_CITIES,
    _feature_options,
    _css,
    _governance_for_city,
    _governance_js,
    _js,
    _layer_json,
    _macro_links,
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
        if not crosswalk_cities:
            self.skipTest("jurisdiction crosswalks live under gitignored data/ and are absent on this checkout")

        self.assertLessEqual(READY_CITIES, crosswalk_cities)

    def test_ready_cities_are_the_approved_selectable_set(self) -> None:
        # Selectable = every console graded in CITY_READINESS (a tracked in-repo constant,
        # not a scan of the gitignored data/ tree). A thin-but-navigable console is still
        # selectable; the grades carry quality separately.
        self.assertEqual(
            READY_CITIES,
            {
                "ahmedabad", "bengaluru", "bhubaneswar", "chennai", "delhi", "hyderabad",
                "jaipur", "kanpur", "kochi", "kolkata", "lucknow", "mumbai", "pune",
                "visakhapatnam",
            },
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

    def test_toggles_render_year_transport_for_timeline_layers(self) -> None:
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

        # transport control replaces the old <select>: step + play/pause buttons,
        # the full year list for the animation loop, and a current-year readout
        self.assertIn("data-year-layer='ward_workorders_yearly'", html)
        self.assertIn("data-years='2013,2014'", html)
        self.assertIn("data-yact='play'", html)
        self.assertIn("data-yact='back'", html)
        self.assertIn("data-yact='fwd'", html)
        self.assertIn("data-year-label='ward_workorders_yearly'", html)
        self.assertNotIn("<option", html)

    def test_toggles_swatch_shape_follows_geometry_kind(self) -> None:
        # the legend swatch is geometry-shaped and consistent across cities:
        # fill -> chip, line -> bar, circle -> dot
        def spec(kind, color):
            return LayerSpec(id=f"x_{kind}", label=kind, file="x.geojson", kind=kind,
                             default=False, group="G", popup=(),
                             paint={f"{kind}-color": color})
        html = _toggles({"G": [spec("fill", "#111"), spec("line", "#222"), spec("circle", "#333")]})
        self.assertIn("sw sw-fill", html)
        self.assertIn("sw sw-line", html)
        self.assertIn("sw sw-dot", html)
        self.assertIn("aria-label='Toggle fill layer'", html)
        self.assertIn("aria-label='Toggle line layer'", html)
        self.assertIn("aria-label='Toggle circle layer'", html)
        # collapsible group wrapper, not a flat list
        self.assertIn("class='layerGroup'", html)
        self.assertIn("class='lgh'", html)

    def test_governance_card_states_water_control_per_city(self) -> None:
        # the atlas thesis made interactive: the same water layer is a parastatal
        # in Bengaluru but the elected corporation's own in Ahmedabad.
        blr = _governance_for_city("bengaluru")
        amd = _governance_for_city("ahmedabad")

        self.assertEqual(blr["water"]["control"], "parastatal")
        self.assertIn("BWSSB", blr["water"]["line"])
        self.assertIn("No councillor you elect", blr["water"]["verdict"])

        self.assertEqual(amd["water"]["control"], "city")
        self.assertIn("AMC Water Supply", amd["water"]["line"])
        self.assertIn("Your vote reaches it", amd["water"]["verdict"])

    def test_governance_card_marks_ahmedabad_libraries_by_grace(self) -> None:
        # right2read crux: Ahmedabad libraries are AMC-funded by discretion, not duty —
        # neither "State runs it" nor "you elect them". The override carries that nuance.
        amd = _governance_for_city("ahmedabad")
        self.assertEqual(amd["libraries"]["control"], "grace")
        self.assertEqual(amd["libraries"]["chipClass"], "gc-grace")
        self.assertIn("96%", amd["libraries"]["line"])
        self.assertIn("AMC", amd["libraries"]["line"])
        self.assertIn("no law requires them", amd["libraries"]["verdict"])

    def test_governance_libraries_stay_state_subject_without_override(self) -> None:
        # the national default is unchanged for cities with no override.
        blr = _governance_for_city("bengaluru")
        self.assertEqual(blr["libraries"]["control"], "state")

    def test_governance_splits_stormwater_from_clean_sanitation(self) -> None:
        # a card that admits floods "fall between" AMC and State irrigation can't be a
        # clean elected-city green; toilets (a genuine municipal duty) stays city.
        amd = _governance_for_city("ahmedabad")
        self.assertEqual(amd["stormwater_drains"]["control"], "shared")
        self.assertEqual(amd["flood_hazard"]["control"], "shared")
        self.assertEqual(amd["toilets"]["control"], "city")
        self.assertIn("falls between", amd["stormwater_drains"]["line"])

    def test_governance_applies_special_case_overrides(self) -> None:
        self.assertEqual(_governance_for_city("delhi")["police"]["control"], "union")
        self.assertEqual(_governance_for_city("kolkata")["metro"]["control"], "union")

    def test_governance_links_corp_money_layers_to_finance_page(self) -> None:
        # with a finance page, the corporation's own money-axis layers point to it;
        # state/parastatal layers (and the no-finance case) do not.
        with_fin = _governance_for_city("ahmedabad", "finance/")
        self.assertEqual(with_fin["wards"]["finance"], "finance/")
        self.assertNotIn("finance", with_fin["libraries"])  # state subject, not corp money
        self.assertNotIn("finance", with_fin["water"])      # AMC water, but not the budget axis

        without = _governance_for_city("ahmedabad")
        self.assertNotIn("finance", without["wards"])

    def test_governance_js_exposes_toggle_hook_and_card_renders(self) -> None:
        script = _governance_js()
        self.assertIn("window.__govShow", script)
        self.assertIn("govcard", script)
        self.assertIn("govchip", script)

    def test_generated_script_keeps_maplibre_qa_hooks_valid(self) -> None:
        script = _js()

        self.assertIn("window.__atlasMap = map;", script)
        self.assertLess(
            script.index("DefaultViewControl.prototype.onAdd"),
            script.index("map.addControl(new DefaultViewControl()"),
        )
        self.assertNotIn('"line-color": "var(--ink)"', script)

    def test_city_console_renders_static_macro_links(self) -> None:
        html = _macro_links("../../")

        self.assertIn('href="../../index.html"', html)
        self.assertIn('href="../../cities/index.html"', html)
        self.assertIn('href="../../why/index.html"', html)
        self.assertIn('href="../../findings/index.html"', html)
        self.assertIn('href="../../about/index.html"', html)

    def test_city_console_css_has_visible_keyboard_focus(self) -> None:
        css = _css()

        self.assertIn(":focus-visible", css)
        self.assertIn("outline:3px solid var(--gold)", css)

    def test_city_console_css_uses_touch_sized_controls(self) -> None:
        css = _css()

        self.assertIn(".lgh{", css)
        self.assertIn("min-height:44px", css)
        self.assertIn(".jurisdictionbar select", css)
        self.assertIn("height:44px;padding:0 8px;width:100%", css)
        self.assertIn(".search,.fsel{width:100%;min-height:44px", css)
        self.assertIn(".tog{align-items:center;display:flex;min-height:44px", css)
        self.assertIn("grid-template-columns:minmax(160px,1fr) minmax(150px,1fr) minmax(150px,1fr) auto 44px", css)
        self.assertIn(".filterbar .fsel,.filterbar .fbtn2,.filterbar .tbtn{height:44px", css)
        self.assertIn(".tbtn{", css)
        self.assertIn("width:44px", css)
        self.assertIn(".ybtn{", css)
        self.assertIn("height:44px;min-width:44px", css)
        self.assertIn(".maplibregl-ctrl-group button{height:44px;width:44px}", css)


if __name__ == "__main__":
    unittest.main()
