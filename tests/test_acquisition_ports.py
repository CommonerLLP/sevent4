import json
import tempfile
import unittest
from pathlib import Path

from sevent4.application.acquisition import build_atlas_source_inventory
from sevent4.application.acquisition import build_document_manifest, build_runlog_record
from sevent4.application.acquisition import (
    build_opencity_atlas_scope_markdown,
    google_drive_download_url,
    classify_mj_library_pdf,
    mj_library_proactive_disclosure_year,
    mj_library_year_from_text,
    opencity_atlas_axis_labels,
    opencity_cut_hits,
    parliament_probe_filter,
    parse_session_range,
    parse_dpl_staffing_text,
    text_needs_ocr,
)
from sevent4.adapters.acquisition_filesystem import CsvJsonAtlasInventoryWriter, JsonCatalogueRepository
from sevent4.ports.acquisition import OpenDataCatalogueInput, SourceDocument


class AcquisitionPortsTest(unittest.TestCase):
    def test_atlas_source_inventory_application_builds_rows_without_file_io(self) -> None:
        catalogue = OpenDataCatalogueInput(
            source_catalogue="data/sources/opencity/catalogue.json",
            datasets=[
                {
                    "name": "delhi-budget",
                    "title": "Municipal Corporation of Delhi Budget",
                    "url": "https://data.opencity.in/dataset/delhi-budget",
                    "organization": "government-of-delhi",
                    "groups": ["delhi"],
                    "tags": ["budget"],
                    "metadata_modified": "2026-01-01T00:00:00",
                    "resources": [
                        {
                            "id": "r1",
                            "name": "Budget PDF",
                            "format": "PDF",
                            "url": "https://example.test/budget.pdf",
                        }
                    ],
                },
                {
                    "name": "bengaluru-budget",
                    "title": "Bengaluru Budget",
                    "groups": ["bengaluru"],
                    "resources": [{"format": "PDF"}],
                },
            ],
        )

        result = build_atlas_source_inventory(
            catalogue,
            city="delhi",
            classify=lambda dataset: {"pays"} if "budget" in dataset.get("name", "") else set(),
            inventory_filename="delhi_opencity_inventory.csv",
            shortlist_filename="delhi_opencity_atlas_shortlist.csv",
        )

        self.assertEqual(result.manifest["dataset_count"], 1)
        self.assertEqual(result.manifest["resource_row_count"], 1)
        self.assertEqual(result.manifest["shortlist_resource_row_count"], 1)
        self.assertEqual(result.inventory_rows[0]["dataset_name"], "delhi-budget")
        self.assertEqual(result.inventory_rows[0]["axis_labels"], "pays")
        self.assertEqual(result.shortlist_rows[0]["shortlist"], "1")

    def test_opencity_inventory_file_adapter_reads_catalogue_and_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogue_path = root / "catalogue.json"
            out_dir = root / "out"
            catalogue_path.write_text(
                json.dumps(
                    {
                        "datasets": [
                            {
                                "name": "delhi-wards",
                                "title": "Delhi Ward Boundary",
                                "groups": ["delhi"],
                                "resources": [{"id": "r1", "format": "GEOJSON"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            catalogue = JsonCatalogueRepository(catalogue_path, repo_root=root).load()
            result = build_atlas_source_inventory(
                catalogue,
                city="delhi",
                classify=lambda dataset: {"base"},
                inventory_filename="inventory.csv",
                shortlist_filename="shortlist.csv",
            )
            CsvJsonAtlasInventoryWriter(
                out_dir,
                inventory_filename="inventory.csv",
                shortlist_filename="shortlist.csv",
                manifest_filename="manifest.json",
            ).write(result)

            self.assertTrue((out_dir / "inventory.csv").exists())
            self.assertTrue((out_dir / "shortlist.csv").exists())
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_catalogue"], "catalogue.json")
            self.assertEqual(manifest["dataset_count"], 1)

    def test_document_manifest_application_shapes_records_without_file_io(self) -> None:
        docs = [
            SourceDocument(
                government="Municipal Corporation of Delhi",
                document_type="mcd_budget",
                fiscal_year="2025-26",
                title="Budget Estimate 2025-26",
                url="https://mcdonline.nic.in/portal/downloadFile/budget.pdf",
                source_page="https://mcdonline.nic.in/portal/showContent?menuguide=budget",
            )
        ]

        manifest = build_document_manifest(
            docs,
            generated_at="2026-06-23T17:00:00",
            scope="mcd",
            sources={"mcd_seed_urls": ["https://mcdonline.nic.in/portal/officialLink"]},
        )

        self.assertEqual(manifest["generated_at"], "2026-06-23T17:00:00")
        self.assertEqual(manifest["scope"], "mcd")
        self.assertEqual(manifest["documents"][0]["status"], "discovered")
        self.assertEqual(manifest["documents"][0]["government"], "Municipal Corporation of Delhi")

    def test_runlog_application_counts_statuses_and_uses_stable_run_id(self) -> None:
        docs = [
            SourceDocument(
                government="Government of NCT of Delhi",
                document_type="budget_at_a_glance",
                fiscal_year="2026-27",
                title="Budget at a Glance 2026-27",
                url="https://finance.delhi.gov.in/budget.pdf",
                source_page="https://finance.delhi.gov.in/finance/budget-glance",
            ),
            SourceDocument(
                government="Municipal Corporation of Delhi",
                document_type="mcd_discovery_error",
                fiscal_year=None,
                title="Discovery failed",
                url="https://mcdonline.nic.in/portal/showContent?menuguide=budget",
                source_page="https://mcdonline.nic.in/portal/showContent?menuguide=budget",
                status="curl failed",
            ),
        ]

        runlog = build_runlog_record(
            docs,
            tool="scripts/recipes/delhi/acquire_finance.py",
            scope="all",
            started_at="2026-06-23T17:00:00",
            ended_at="2026-06-23T17:01:00",
            sources={
                "gnctd_finance_pages": ["https://finance.delhi.gov.in/finance/budget-glance"],
                "mcd_seed_urls": ["https://mcdonline.nic.in/portal/officialLink"],
            },
        )

        self.assertEqual(runlog["documents"], 2)
        self.assertEqual(runlog["statuses"], {"discovered": 1, "curl failed": 1})
        self.assertEqual(len(runlog["run_id"]), 16)

    def test_library_source_archive_application_normalizes_drive_and_ocr_signals(self) -> None:
        self.assertEqual(
            google_drive_download_url("https://drive.google.com/file/d/abc123/view?usp=sharing"),
            "https://drive.google.com/uc?export=download&id=abc123",
        )
        self.assertEqual(
            google_drive_download_url("https://dpl.gov.in/images/annualreport910.pdf"),
            "https://dpl.gov.in/images/annualreport910.pdf",
        )
        self.assertTrue(text_needs_ocr("ANNUAL REPORT\n2020-2021", min_chars=200))
        self.assertFalse(text_needs_ocr("x" * 250, min_chars=200))

    def test_library_source_archive_application_parses_dpl_staffing(self) -> None:
        text = """
        (2) Library Administration: (as on 31-03-2024)
        Total Posts Sanctioned : 274 Filled up Post : 138 Vacant Post : 136
        Professional Ministerial Professional Ministerial Professional Ministerial
        199 75 97 41 102 34
        """

        row = parse_dpl_staffing_text("2023-24", text)

        self.assertEqual(row["total_posts_sanctioned"], "274")
        self.assertEqual(row["total_posts_filled"], "138")
        self.assertEqual(row["total_posts_vacant"], "136")
        self.assertEqual(row["professional_posts_vacant"], "102")
        self.assertEqual(row["ministerial_posts_vacant"], "34")
        self.assertEqual(row["vacancy_rate_pct"], "49.6")
        self.assertEqual(row["extraction_status"], "observed_split")

    def test_dpl_parliament_probe_application_filters_and_parses_sessions(self) -> None:
        self.assertTrue(parliament_probe_filter("Delhi Public Library staffing", "vacant posts"))
        self.assertTrue(parliament_probe_filter("Culture grant", "Delhi Library Board"))
        self.assertTrue(parliament_probe_filter("Library branches in Delhi", "staff vacancies"))
        self.assertFalse(parliament_probe_filter("Public libraries in Kerala", "staff vacancies"))
        self.assertEqual(parse_session_range("214-216,220"), [214, 215, 216, 220])

    def test_mj_library_application_classifies_pdfs_and_years(self) -> None:
        self.assertEqual(mj_library_year_from_text("_RTI_201718_MJ%20Library_Discloser.pdf"), "2017-18")
        self.assertEqual(mj_library_year_from_text("2020-2021.pdf"), "2020-21")
        self.assertEqual(mj_library_year_from_text("2022_2023.pdf"), "2022-23")
        self.assertEqual(
            mj_library_proactive_disclosure_year("PRO ACTIVE DISCLOSURE 2024-25 - "),
            "2024-25",
        )
        self.assertEqual(
            classify_mj_library_pdf(
                "PRO ACTIVE DISCLOSURE 2024-25",
                "https://mjlibrary.in/assets/img/pdf/mj_discloser_rti_2024-25.pdf",
                "2024-25",
                proactive_context=True,
            ),
            "proactive_disclosure",
        )
        self.assertEqual(
            classify_mj_library_pdf("", "https://mjlibrary.in/assets/img/pdf/list_of_ccc.pdf", ""),
            "civic_centres",
        )
        self.assertEqual(
            classify_mj_library_pdf("", "https://mjlibrary.in/assets/img/pdf/admissionformeng.pdf", ""),
            "forms",
        )

    def test_opencity_scope_application_classifies_cuts_and_markdown_without_file_io(self) -> None:
        datasets = [
            {
                "title": "Delhi Ward Boundary Map",
                "name": "delhi-ward-boundary",
                "url": "https://data.opencity.in/dataset/delhi-ward-boundary",
                "organization": "State Election Commission",
                "groups": ["delhi"],
                "tags": ["ward", "boundary"],
                "notes": "GIS ward boundaries",
                "num_resources": 2,
                "resources": [{"format": "GEOJSON"}, {"format": "CSV"}],
            },
            {
                "title": "Municipal Budget",
                "name": "delhi-budget",
                "url": "https://data.opencity.in/dataset/delhi-budget",
                "organization": "MCD",
                "groups": ["delhi"],
                "tags": ["finance"],
                "notes": "Budget expenditure",
                "num_resources": 1,
                "resources": [{"format": "PDF"}],
            },
            {
                "title": "Restaurant Licences",
                "name": "restaurant-licences",
                "url": "https://data.opencity.in/dataset/restaurants",
                "organization": "MCD",
                "groups": ["delhi"],
                "tags": [],
                "notes": "",
                "num_resources": 1,
                "resources": [{"format": "PDF"}],
            },
        ]

        self.assertEqual(opencity_atlas_axis_labels(datasets[0]), {"base", "decides"})
        self.assertEqual(opencity_cut_hits(datasets[0]), {"ward": True, "assembly": False, "parliament": False})

        markdown, axis_totals = build_opencity_atlas_scope_markdown(
            datasets,
            cities=["delhi"],
            generator_path="scripts/recipes/scope_opencity_for_atlas.py",
        )

        self.assertEqual(axis_totals["base"], 1)
        self.assertEqual(axis_totals["pays"], 1)
        self.assertIn("## Delhi  ·  3 datasets  ·  2 atlas-relevant", markdown)
        self.assertIn("- ★ **Delhi Ward Boundary Map**", markdown)
        self.assertIn("_ward_: **Delhi Ward Boundary Map**", markdown)
        self.assertIn("### (unclassified — 1; frame may be missing a keyword)", markdown)

    def test_opencity_cut_hits_requires_geometry_not_just_tabular(self) -> None:
        # A ward-titled dataset whose only resource is a CSV/XLS table cannot
        # satisfy a slice-by-geometry cut, even though the title matches.
        tabular = {
            "title": "Delhi Ward Population Table",
            "name": "delhi-ward-population",
            "tags": ["ward"],
            "notes": "Ward-wise population counts",
            "resources": [{"format": "CSV"}, {"format": "XLSX"}],
        }
        self.assertEqual(
            opencity_cut_hits(tabular), {"ward": False, "assembly": False, "parliament": False}
        )
        geo = {**tabular, "resources": [{"format": "GEOJSON"}]}
        self.assertEqual(
            opencity_cut_hits(geo), {"ward": True, "assembly": False, "parliament": False}
        )


if __name__ == "__main__":
    unittest.main()
