import json
import tempfile
import unittest
from pathlib import Path

from sevent4.adapters.sources_filesystem import FileSourcesInputRepository
from sevent4.application.sources import public_sources_payload, publish_sources_page
from sevent4.sources.build_sources_page import build_sources_page_from_files


def _write_sources_fixture(tmp: Path, *, break_evidence: bool = False) -> tuple[Path, Path]:
    source_dir = tmp / "data" / "cities" / "testville" / "source"
    layers_dir = tmp / "data" / "cities" / "testville" / "layers"
    out_dir = tmp / "public" / "cities" / "testville"
    source_dir.mkdir(parents=True)
    layers_dir.mkdir(parents=True)

    evidence = source_dir / "PROVENANCE.md"
    if not break_evidence:
        evidence.write_text("record\n", encoding="utf-8")

    (source_dir / "public_sources.json").write_text(
        json.dumps(
            {
                "city": "testville",
                "compiled": "2026-07-01",
                "sources": [
                    {
                        "id": "linked_record",
                        "kind": "boundary_dataset",
                        "label": "Ward boundaries via DataMeet",
                        "url": "https://example.org/wards.geojson",
                        "notes": "Backs wards.geojson.",
                        "evidence": "data/cities/testville/source/PROVENANCE.md",
                    },
                    {
                        "id": "unlinked_record",
                        "kind": "facility_register",
                        "label": "Facility register (portal URL never recorded)",
                        "url": None,
                        "notes": "Acquired 2026-05; the portal URL was not captured.",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    city_yaml = tmp / "city.yaml"
    city_yaml.write_text(
        "\n".join(
            [
                "id: testville",
                "name: Testville",
                "country: India",
                "state: Teststate",
                "center: [72.0, 23.0]",
                "bbox: [71.9, 22.9, 72.1, 23.1]",
                "crs_metric: EPSG:32643",
                f"layers_dir: {layers_dir}",
                f"source_dir: {source_dir}",
                f"outputs_dir: {out_dir}",
            ]
        ),
        encoding="utf-8",
    )
    return city_yaml, out_dir


class SourcesPortsTest(unittest.TestCase):
    def test_sources_application_publishes_html_and_json_through_ports(self) -> None:
        class City:
            id = "testville"
            name = "Testville"
            source_dir = Path("data/cities/testville/source")

        class Repository:
            def load(self):
                return type(
                    "Input",
                    (),
                    {
                        "city": City(),
                        "compiled": "2026-07-01",
                        "entries": [
                            {
                                "id": "a",
                                "kind": "boundary_dataset",
                                "label": "A",
                                "url": None,
                                "evidence": "data/x.json",
                            }
                        ],
                    },
                )()

        class HtmlWriter:
            def write_html(self, html: str) -> None:
                self.html = html

        class JsonWriter:
            def write_json(self, payload) -> None:
                self.payload = payload

        html_writer, json_writer = HtmlWriter(), JsonWriter()
        result = publish_sources_page(
            Repository(),
            html_writer,
            json_writer,
            lambda city, compiled, entries: f"{city.name}:{compiled}:{len(entries)}",
        )

        self.assertEqual(html_writer.html, "Testville:2026-07-01:1")
        self.assertEqual(json_writer.payload["schema"], "sevent4.public_sources.v1")
        self.assertEqual(result.payload["count"], 1)
        # the internal evidence path must never reach the public artifact
        self.assertNotIn("evidence", result.payload["sources"][0])

    def test_payload_rejects_non_url_source_and_blank_required_fields(self) -> None:
        with self.assertRaises(ValueError):
            public_sources_payload(
                "t", "T", "", [{"id": "x", "kind": "k", "label": "L", "url": "data/local.pdf"}]
            )
        with self.assertRaises(ValueError):
            public_sources_payload("t", "T", "", [{"id": "x", "kind": "k", "label": " "}])
        with self.assertRaises(ValueError):
            public_sources_payload(
                "t",
                "T",
                "",
                [
                    {"id": "x", "kind": "k", "label": "L"},
                    {"id": "x", "kind": "k", "label": "M"},
                ],
            )

    def test_file_repository_gates_on_missing_evidence_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            city_yaml, _ = _write_sources_fixture(Path(tmp), break_evidence=True)
            with self.assertRaises(FileNotFoundError):
                FileSourcesInputRepository(city_yaml).load()

    def test_sources_cli_builds_page_and_json_through_file_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            city_yaml, out_dir = _write_sources_fixture(Path(tmp))
            sources_out = out_dir / "sources"

            build_sources_page_from_files(str(city_yaml), sources_out)

            page = (sources_out / "index.html").read_text(encoding="utf-8")
            self.assertIn("Where this console's data comes from", page)
            self.assertIn("2 source records", page)
            self.assertIn("1 with no public URL recorded", page)
            self.assertIn("compiled 2026-07-01", page)
            self.assertIn('href="https://example.org/wards.geojson"', page)
            # a url-less record renders as an honest finding, never a guessed link
            self.assertIn("no public URL recorded", page)
            # theme-aware: shared stylesheet + persisted-theme bootstrap
            self.assertIn("../../../assets/theme.css", page)
            self.assertIn("atlas-theme", page)

            payload = json.loads((sources_out / "sources.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "sevent4.public_sources.v1")
            self.assertEqual(payload["city"], "testville")
            self.assertEqual(payload["count"], 2)
            self.assertEqual(payload["sources"][1]["url"], None)
            self.assertTrue(all("evidence" not in s for s in payload["sources"]))


if __name__ == "__main__":
    unittest.main()
