import unittest

from sevent4.application.city_build import CityBuildInput, build_city_artifacts


def _feature(properties, coordinates=None):
    return {
        "type": "Feature",
        "properties": dict(properties),
        "geometry": {
            "type": "Polygon",
            "coordinates": coordinates
            or [[
                [72.0, 23.0],
                [72.1, 23.0],
                [72.1, 23.1],
                [72.0, 23.1],
                [72.0, 23.0],
            ]],
        },
    }


class CityBuildPortsTest(unittest.TestCase):
    def test_application_builds_city_artifacts_without_filesystem(self) -> None:
        input_data = CityBuildInput(
            slug="chennai",
            boundaries={
                "wards": {"type": "FeatureCollection", "features": [_feature({"ward_no": "001", "zone": "North"})]},
                "acs": {"type": "FeatureCollection", "features": [_feature({"AC_NAME": "Assembly One"})]},
                "pcs": {"type": "FeatureCollection", "features": [_feature({"PC_NAME": "Parliament One"})]},
                "districts": {"type": "FeatureCollection", "features": [_feature({"DISTRICT": "Chennai"})]},
            },
            osm_layers={
                "libraries": {"type": "FeatureCollection", "features": [_feature({"name": "Branch Library"})]},
                "roads": {"type": "FeatureCollection", "features": []},
            },
            councillors=[
                {"ward_no": "1", "councillor_name": "Councillor A", "party": "Party", "phone": "12345"}
            ],
            officers=[
                {"role": "Municipal Commissioner", "name": "Officer A", "service": "IAS"},
                {"role": "Police Commissioner", "name": "Officer B", "service": "IPS"},
            ],
        )

        artifacts = build_city_artifacts(input_data)

        ward = artifacts.layers["wards.geojson"]["features"][0]["properties"]
        self.assertEqual(ward["Name"], "Ward 001 · North")
        self.assertEqual(ward["councillors"], "Councillor A")
        self.assertEqual(artifacts.layers["acs.geojson"]["features"][0]["properties"]["ac_name"], "Assembly One")
        self.assertEqual(artifacts.layers["pcs.geojson"]["features"][0]["properties"]["pc_name"], "Parliament One")
        self.assertIn("districts.geojson", artifacts.layers)
        self.assertIn("libraries.geojson", artifacts.layers)
        self.assertNotIn("roads.geojson", artifacts.layers)
        self.assertEqual(artifacts.governance["municipal_commissioner"], "Officer A")
        self.assertEqual(artifacts.governance["police_commissioner"], "Officer B")
        self.assertEqual(artifacts.city_yaml["id"], "chennai")
        self.assertEqual(artifacts.city_yaml["layers_dir"], "data/cities/chennai/layers")
        self.assertEqual([row["id"] for row in artifacts.manifest["layers"]], ["wards", "districts", "pcs", "acs", "libraries"])


if __name__ == "__main__":
    unittest.main()
