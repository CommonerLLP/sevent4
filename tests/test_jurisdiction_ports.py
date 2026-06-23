import unittest


class JurisdictionPortsTest(unittest.TestCase):
    def test_pick_populated_field_skips_empty_case_insensitive_matches(self) -> None:
        from sevent4.application.jurisdiction import pick_populated_field

        rows = [
            {"AC_NAME": "Yelahanka", "ac_name": ""},
            {"AC_NAME": "", "ac_name": ""},
        ]

        self.assertEqual(pick_populated_field(rows, ("ac_name", "Name")), "AC_NAME")
        self.assertIsNone(pick_populated_field(rows, ("missing",)))

    def test_representative_point_crosswalk_shapes_flat_records(self) -> None:
        from sevent4.application.jurisdiction import build_representative_point_crosswalk

        document = build_representative_point_crosswalk(
            "kolkata",
            [
                {"ward_name": " Ward 1 ", "ac_name": "AC North", "pc_name": "PC 1", "district_name": None},
                {"ward_name": "", "ac_name": "AC South", "pc_name": "PC 2", "district_name": "District"},
            ],
        )

        self.assertEqual(document["schema"], "sevent4.jurisdiction_crosswalk.v1")
        self.assertEqual(document["city"], "kolkata")
        self.assertEqual(document["levels"], ["state", "district"])
        self.assertEqual(document["records"], [{"ward_name": "Ward 1", "ac_name": "AC North", "pc_name": "PC 1", "district_name": ""}])

    def test_overlap_crosswalk_preserves_ahmedabad_record_schema_and_sort_order(self) -> None:
        from sevent4.application.jurisdiction import build_overlap_crosswalk

        document = build_overlap_crosswalk(
            city="ahmedabad",
            state="Gujarat",
            records=[
                {
                    "district_name": "Ahmedabad",
                    "pc_name": "Ahmedabad East",
                    "pc_code": "7.0",
                    "ac_no": "44.0",
                    "ac_name": "Vatva",
                    "ward_no": "2",
                    "ward_name": "02 Ward",
                    "overlap_area_m2": 2000.456,
                    "overlap_pct_of_ward": 0.123456,
                    "overlap_pct_of_ac": 0.00045678,
                },
                {
                    "district_name": "Ahmedabad",
                    "pc_name": "Ahmedabad East",
                    "pc_code": "7.0",
                    "ac_no": "43",
                    "ac_name": "Maninagar",
                    "ward_no": "1",
                    "ward_name": "01 Ward",
                    "overlap_area_m2": 3000,
                    "overlap_pct_of_ward": 0.2,
                    "overlap_pct_of_ac": 0.001,
                },
            ],
            thresholds={"min_ward_pct": 0.005, "min_area_m2": 2500.0},
            excluded_acs=["Parent AC"],
        )

        self.assertEqual(document["levels"], ["state", "district", "pc", "ac", "ward"])
        self.assertEqual(document["excluded_acs"][0]["ac_name"], "Parent AC")
        self.assertEqual([row["ac_name"] for row in document["records"]], ["Maninagar", "Vatva"])
        self.assertEqual(document["records"][1]["pc_code"], "7")
        self.assertEqual(document["records"][1]["ac_no"], "44")
        self.assertEqual(document["records"][1]["overlap_area_m2"], 2000.46)
        self.assertEqual(document["records"][1]["overlap_pct_of_ward"], 0.12346)

    def test_publisher_uses_repository_and_writer_ports(self) -> None:
        from sevent4.application.jurisdiction import publish_representative_point_crosswalk

        class Repository:
            def load_representative_point_records(self, city):
                return ({"ward_name": "Ward 1", "ac_name": "AC 1", "pc_name": "PC 1", "district_name": "D"},)

        class Writer:
            def __init__(self) -> None:
                self.document = None

            def write_crosswalk(self, city, document):
                self.document = document
                return "out/jurisdiction_crosswalk.json"

        writer = Writer()
        result = publish_representative_point_crosswalk("testville", Repository(), writer)

        self.assertEqual(writer.document, result.document)
        self.assertEqual(result.output_path, "out/jurisdiction_crosswalk.json")
        self.assertEqual(result.ward_count, 1)
        self.assertEqual(result.ac_count, 1)
        self.assertEqual(result.pc_count, 1)


if __name__ == "__main__":
    unittest.main()
