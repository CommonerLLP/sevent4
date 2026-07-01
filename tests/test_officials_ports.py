import json
import tempfile
import unittest
from pathlib import Path

from sevent4.adapters.officials_filesystem import FileOfficialsInputRepository
from sevent4.application.officials import publish_officials_directory
from sevent4.officials.build_officials_directory import build_officials_directory_from_files


class OfficialsPortsTest(unittest.TestCase):
    def test_officials_directory_application_publishes_through_ports(self) -> None:
        class City:
            name = "Testville"
            layers_dir = Path("data/cities/testville/layers")

        class Repository:
            def load(self):
                return type(
                    "Input",
                    (),
                    {
                        "city": City(),
                        "as_of": "2026-06-30",
                        "attribution": "fixture attribution",
                        "records": [{"department": "municipal_corp_hq", "name": "Someone"}],
                    },
                )()

        class Writer:
            def __init__(self) -> None:
                self.html = ""

            def write_html(self, html: str) -> None:
                self.html = html

        writer = Writer()
        result = publish_officials_directory(
            Repository(),
            writer,
            lambda city, as_of, attribution, records: f"{city.name}:{as_of}:{len(records)}",
        )

        self.assertEqual(writer.html, "Testville:2026-06-30:1")
        self.assertEqual(result.html, "Testville:2026-06-30:1")

    def test_officials_file_repository_loads_city_and_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            city_yaml, _layers_dir, _out = _write_officials_fixture(Path(tmp))

            inputs = FileOfficialsInputRepository(city_yaml).load()

            self.assertEqual(inputs.city.name, "Testville")
            self.assertEqual(inputs.as_of, "2026-06-30")
            self.assertIn("Vonter/city-officials", inputs.attribution)
            self.assertEqual(len(inputs.records), 3)

    def test_officials_directory_cli_builds_html_through_file_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            city_yaml, _layers_dir, out_dir = _write_officials_fixture(Path(tmp))
            officials_out = out_dir / "officials" / "index.html"

            build_officials_directory_from_files(str(city_yaml), str(officials_out))

            page = officials_out.read_text(encoding="utf-8")
            self.assertIn("Who holds the seat", page)
            self.assertIn("Municipal corporation", page)
            self.assertIn("Someone, IAS", page)
            # the blank-name record renders as a ghost finding, not a silent drop
            self.assertIn("not publicly confirmed as of 2026-06-30", page)
            self.assertIn("3 tracked", page)
            self.assertIn("1 not publicly confirmed", page)
            # a non-URL provenance note must render as plain text, never as a
            # broken <a href> — this was a real bug caught by the public-site
            # dead-link checker
            self.assertIn(
                '<span class="rsrc rsrc-text">data/cities/testville/layers/pcs.geojson '
                '(internal repo asset, already verified)</span>',
                page,
            )
            self.assertNotIn('href="data/cities/testville/layers/pcs.geojson', page)
            self.assertNotIn('data-theme="dark"', page)
            self.assertIn('href="../../../assets/theme.css"', page)
            self.assertIn("localStorage.getItem('atlas-theme')", page)
            # search box + sector jump-nav, keyed by department so both work across cities
            self.assertIn('id="osearch"', page)
            self.assertIn('href="#dept-municipal_corp_hq"', page)
            self.assertIn('href="#dept-municipal_corp_zone"', page)
            self.assertIn('id="dept-municipal_corp_hq"', page)
            self.assertIn('data-search="testville corp citywide municipal commissioner someone, ias"', page)


def _write_officials_fixture(base: Path) -> tuple[Path, Path, Path]:
    repo = base / "repo"
    city_dir = repo / "data" / "cities" / "testville"
    layers_dir = city_dir / "layers"
    out_dir = repo / "public" / "cities" / "testville"
    layers_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='fake'\n", encoding="utf-8")
    (city_dir / "city.yaml").write_text(
        "\n".join(
            [
                "id: testville",
                "name: Testville",
                "country: India",
                "state: State",
                "center: [72.0, 23.0]",
                "bbox: [71.0, 22.0, 73.0, 24.0]",
                "crs_metric: EPSG:32643",
                "layers_dir: data/cities/testville/layers",
                "source_dir: data/cities/testville/source",
                "outputs_dir: public/cities/testville",
            ]
        ),
        encoding="utf-8",
    )
    (layers_dir / "officials.json").write_text(
        json.dumps(
            {
                "schema": "sevent4.officials_directory.v1",
                "city": "testville",
                "attribution": "Record shape inspired by Vonter/city-officials (CC-BY 4.0).",
                "as_of": "2026-06-30",
                "records": [
                    {
                        "institution": "Testville Corp",
                        "institution_type": "corporation",
                        "department": "municipal_corp_hq",
                        "area": "citywide",
                        "designation": "Municipal Commissioner",
                        "name": "Someone, IAS",
                        "source": "https://example.org/commissioner",
                        "notes": "",
                    },
                    {
                        "institution": "Testville Corp",
                        "institution_type": "corporation",
                        "department": "municipal_corp_zone",
                        "area": "West zone",
                        "designation": "Deputy Municipal Commissioner",
                        "name": "",
                        "source": "",
                        "notes": "no current officeholder found",
                    },
                    {
                        "institution": "Lok Sabha",
                        "institution_type": "state_dept",
                        "department": "election_pc",
                        "area": "Testville (PC 1)",
                        "designation": "Member of Parliament",
                        "name": "Reused Rep",
                        "source": "data/cities/testville/layers/pcs.geojson (internal repo asset, already verified)",
                        "notes": "reused directly from the repo's own layer, not a live URL",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return city_dir / "city.yaml", layers_dir, out_dir


if __name__ == "__main__":
    unittest.main()
