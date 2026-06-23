import json
import tempfile
import unittest
from pathlib import Path

from sevent4.application.representatives import (
    build_representative_source_manifest,
    build_ward_representative_document,
    parse_ahmedabad_councillor_rows,
    validate_councillor_rows,
)
from sevent4.adapters.representatives_filesystem import (
    CsvCouncillorWriter,
    JsonRepresentativeManifestWriter,
    JsonRepresentativeOfficerWriter,
    WardRepresentativeLayerWriter,
)


class RepresentativePortsTest(unittest.TestCase):
    def test_source_manifest_application_shapes_rows_without_file_io(self) -> None:
        document = build_representative_source_manifest(
            "ahmedabad",
            [
                {
                    "id": "ward_councillors_2026_27",
                    "label": "Councillors 2026-27",
                    "url": "https://example.test/councillors.pdf",
                    "notes": "Ward councillor roster.",
                }
            ],
            lambda source: f"data/cities/ahmedabad/source/representatives/docs/{source['id']}.pdf",
        )

        self.assertEqual(document["city"], "ahmedabad")
        self.assertEqual(
            document["items"][0],
            {
                "id": "ward_councillors_2026_27",
                "label": "Councillors 2026-27",
                "url": "https://example.test/councillors.pdf",
                "notes": "Ward councillor roster.",
                "city": "ahmedabad",
                "path": "data/cities/ahmedabad/source/representatives/docs/ward_councillors_2026_27.pdf",
            },
        )

    def test_ahmedabad_councillor_parser_builds_rows_from_pdftotext_output(self) -> None:
        text = "\n".join(
            [
                "1 ખાડિયા મ ય ઝોન જાગૃતિબેન પરીખ",
                "ભાજપ 9876543210",
                "2 ખાડિયા મ ય ઝોન ઇમરાનભાઇ શેખ",
                "ક ેસ 9123456789",
            ]
        )

        rows = parse_ahmedabad_councillor_rows(text, lambda ward_no: f"{ward_no:02d} TEST WARD")

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["serial"], "1")
        self.assertEqual(rows[0]["ward_no"], "01")
        self.assertEqual(rows[0]["ward_name"], "01 TEST WARD")
        self.assertEqual(rows[0]["ward_name_gu"], "ખાડિયા")
        self.assertEqual(rows[0]["party"], "BJP")
        self.assertEqual(rows[0]["phones"], "9876543210")
        self.assertEqual(rows[1]["party"], "INC")

    def test_councillor_validation_accepts_configurable_ward_counts(self) -> None:
        rows = [
            {"ward_no": "01", "serial": "1"},
            {"ward_no": "01", "serial": "2"},
            {"ward_no": "02", "serial": "3"},
            {"ward_no": "02", "serial": "4"},
        ]

        validate_councillor_rows(rows, expected_rows=4, expected_wards=2, councillors_per_ward=2)

    def test_ward_representative_application_shapes_geojson_without_file_io(self) -> None:
        document = build_ward_representative_document(
            _ward_document(),
            [
                {
                    "ward_no": "01",
                    "councillor_name_gu": "જાગૃતિબેન પરીખ",
                    "councillor_name_en": "",
                    "party": "BJP",
                    "phones": "9876543210",
                },
                {
                    "ward_no": "01",
                    "councillor_name_gu": "ઇમરાનભાઇ શેખ",
                    "councillor_name_en": "",
                    "party": "INC",
                    "phones": "9123456789",
                },
            ],
            {
                "name": "Commissioner",
                "phone_office": "079-00000000",
                "email": "mc@example.test",
                "source_url": "https://example.test/contact.pdf",
            },
        )

        props = document["features"][0]["properties"]
        self.assertEqual(props["ward_no"], "01")
        self.assertEqual(props["councillor_count"], "2")
        self.assertEqual(props["councillor_parties"], "BJP; INC")
        self.assertEqual(props["municipal_commissioner"], "Commissioner")

    def test_filesystem_adapters_write_manifest_csv_officers_and_ward_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            manifest_path = base / "representative_sources.json"
            csv_path = base / "ward_councillors.csv"
            officers_path = base / "city_officers.json"
            wards_path = base / "wards.geojson"

            JsonRepresentativeManifestWriter(manifest_path).write_manifest({"city": "test", "items": []})
            CsvCouncillorWriter(csv_path).write_rows([{"serial": "1", "ward_no": "01"}])
            JsonRepresentativeOfficerWriter(officers_path).write_officers("test", [{"name": "Officer"}])
            WardRepresentativeLayerWriter(wards_path).write_document(_ward_document())

            self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8")), {"city": "test", "items": []})
            self.assertIn("serial,ward_no", csv_path.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(officers_path.read_text(encoding="utf-8"))["items"][0]["name"], "Officer")
            self.assertEqual(json.loads(wards_path.read_text(encoding="utf-8"))["features"][0]["properties"]["Name"], "01 TEST")


def _ward_document() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"Name": "01 TEST"},
                "geometry": {"type": "Polygon", "coordinates": []},
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
