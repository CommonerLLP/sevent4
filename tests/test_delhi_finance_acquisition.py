import json
import unittest

from scripts.recipes.delhi.acquire_finance import (
    BudgetDocument,
    extract_detail_page_links,
    extract_finance_pdf_links,
    extract_legacy_delhi_budget_refs,
    extract_mcd_budget_entries,
    extract_mcd_menu_guides,
    fiscal_year_from_text,
    safe_filename,
)


class DelhiFinanceAcquisitionTest(unittest.TestCase):
    def test_fiscal_year_from_text_finds_budget_year(self) -> None:
        self.assertEqual(fiscal_year_from_text("Budget Receipt 2026-27"), "2026-27")
        self.assertEqual(fiscal_year_from_text("RBE 22-23 BE 2023-24"), "2022-23")
        self.assertIsNone(fiscal_year_from_text("Budget Speech Hindi 2026-26"))
        self.assertEqual(
            fiscal_year_from_text("Detailed Demands for Grants 2015-16 VOA"),
            "2015-16",
        )
        self.assertIsNone(fiscal_year_from_text("Finance Department"))

    def test_extract_finance_pdf_links_uses_title_and_absolute_urls(self) -> None:
        html = """
        <a class="tab-view" title="Budget at a Glance 2026-27"
           href="/sites/default/files/Finance/generic_multiple_files/bag_compressed_1_2.pdf">
           Download
        </a>
        <a href="https://delhi.gov.in/sites/default/files/2025-04/cyber.pdf">Noise</a>
        """

        docs = extract_finance_pdf_links(
            html,
            source_url="https://finance.delhi.gov.in/finance/budget-glance",
            document_type="budget_at_a_glance",
        )

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["title"], "Budget at a Glance 2026-27")
        self.assertEqual(docs[0]["fiscal_year"], "2026-27")
        self.assertEqual(
            docs[0]["url"],
            "https://finance.delhi.gov.in/sites/default/files/Finance/generic_multiple_files/bag_compressed_1_2.pdf",
        )
        self.assertEqual(docs[0]["document_type"], "budget_at_a_glance")

    def test_extract_finance_pdf_links_uses_url_year_when_title_year_is_invalid(self) -> None:
        html = """
        <a title="Budget Speech Hindi 2026-26"
           href="/sites/default/files/Finance/generic_multiple_files/budget_speech_2026-27_hindi.pdf">
          Download
        </a>
        """

        docs = extract_finance_pdf_links(
            html,
            source_url="https://finance.delhi.gov.in/finance/budget-speech",
            document_type="budget_speech",
        )

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["fiscal_year"], "2026-27")
        self.assertEqual(docs[0]["title"], "Budget Speech Hindi 2026-26")

    def test_extract_finance_pdf_links_does_not_apply_page_title_to_chrome_pdf(self) -> None:
        html = """
        <title>Detailed Demands for Grants 2026-27 | FINANCE DEPARTMENT</title>
        <a href="https://delhi.gov.in/sites/default/files/2025-04/i4c_handbook.pdf">Download</a>
        """

        docs = extract_finance_pdf_links(
            html,
            source_url="https://finance.delhi.gov.in/finance/detailed-demands-grants-2026-27",
            document_type="detailed_demands_for_grants",
        )

        self.assertEqual(docs, [])

    def test_extract_detail_page_links_reads_detailed_demands_table(self) -> None:
        html = """
        <tr><td>Detailed Demands for Grants 2026-27</td>
        <td><a href="/finance/detailed-demands-grants-2026-27"><strong>View</strong></a></td></tr>
        <tr><td>Detailed Demands for Grants 2015-16 VOA</td>
        <td><a href="/finance/detailed-demands-grants-2015-16-voa"><strong>View</strong></a></td></tr>
        """

        pages = extract_detail_page_links(
            html,
            "https://finance.delhi.gov.in/finance/detailed-demands-grants-0",
        )

        self.assertEqual(
            [(p["fiscal_year"], p["url"]) for p in pages],
            [
                (
                    "2026-27",
                    "https://finance.delhi.gov.in/finance/detailed-demands-grants-2026-27",
                ),
                (
                    "2015-16",
                    "https://finance.delhi.gov.in/finance/detailed-demands-grants-2015-16-voa",
                ),
            ],
        )

    def test_extract_mcd_budget_entries_walks_nested_menu_payload(self) -> None:
        payload = {
            "data": [
                {
                    "menuName": "Finance Department",
                    "children": [
                        {
                            "menuName": "Budget Estimate 2025-26",
                            "pdfPath": "/portal/downloadFile/budget_2025_26.pdf",
                        },
                        {
                            "menuName": "Garden Circular",
                            "pdfPath": "/portal/downloadFile/garden.pdf",
                        },
                    ],
                }
            ]
        }

        docs = extract_mcd_budget_entries(
            json.dumps(payload),
            "https://mcdonline.nic.in/portal/showSubMenu?menuguide=finance",
        )

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["fiscal_year"], "2025-26")
        self.assertEqual(docs[0]["document_type"], "mcd_budget")
        self.assertEqual(
            docs[0]["url"],
            "https://mcdonline.nic.in/portal/downloadFile/budget_2025_26.pdf",
        )

    def test_extract_mcd_budget_entries_parses_html_embedded_in_json(self) -> None:
        payload = {
            "menuName": """
            <table><tbody><tr><td>
              <a href=/portal/downloadFile/be_22-23_re-unified_mcd.pdf>
                Budget Estimate 2022-23 of Municipal Corporation of Delhi
              </a>
            </td></tr></tbody></table>
            """,
        }

        docs = extract_mcd_budget_entries(
            json.dumps(payload),
            "https://mcdonline.nic.in/portal/showContent?menuguide=budget",
        )

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["fiscal_year"], "2022-23")
        self.assertEqual(
            docs[0]["url"],
            "https://mcdonline.nic.in/portal/downloadFile/be_22-23_re-unified_mcd.pdf",
        )

    def test_extract_mcd_budget_entries_keeps_income_expenditure_rbe_rows(self) -> None:
        payload = {
            "menuName": """
            <a href=/portal/downloadFile/income_rbe_18-19_&_be_19-20__south_mcd.pdf>
              Income RBE_18-19 & BE 19-20 South MCD
            </a>
            <a href=/portal/downloadFile/expenditure_rbe_17-18_&_be_18-19_south_mcd.pdf>
              Expenditure RBE_17-18 &_BE_18-19 South MCD
            </a>
            """,
        }

        docs = extract_mcd_budget_entries(
            json.dumps(payload),
            "https://mcdonline.nic.in/portal/showContent?menuguide=budget",
        )

        self.assertEqual([doc["fiscal_year"] for doc in docs], ["2018-19", "2017-18"])

    def test_extract_mcd_menu_guides_finds_budget_children(self) -> None:
        payload = {
            "finance": [
                {"menuName": "About Department", "menuGuide": "about"},
                {"menuName": "Budget Documents", "menuGuide": "budget-docs"},
            ]
        }

        guides = extract_mcd_menu_guides(json.dumps(payload))

        self.assertEqual(guides, [{"title": "Budget Documents", "menu_guide": "budget-docs"}])

    def test_extract_legacy_delhi_budget_refs_ports_cbga_subheading_iframe_walk(self) -> None:
        html = """
        <table>
          <tr><td class="subheading"><a href="/finance/legacy/2021-22">Budget 2021-22</a></td></tr>
          <tr><td><a href="/not-budget">Noise</a></td></tr>
        </table>
        <iframe src="/sites/default/files/legacy/budget_2020-21.pdf"></iframe>
        """

        refs = extract_legacy_delhi_budget_refs(
            html,
            "https://delhi.gov.in/wps/wcm/connect/lib_finance/Finance/Home/Budget/Budget+2020_21",
        )

        self.assertEqual(
            refs["pages"],
            [
                {
                    "title": "Budget 2021-22",
                    "url": "https://delhi.gov.in/finance/legacy/2021-22",
                }
            ],
        )
        self.assertEqual(len(refs["documents"]), 1)
        self.assertEqual(refs["documents"][0]["document_type"], "legacy_delhi_budget")
        self.assertEqual(refs["documents"][0]["fiscal_year"], "2020-21")
        self.assertEqual(
            refs["documents"][0]["url"],
            "https://delhi.gov.in/sites/default/files/legacy/budget_2020-21.pdf",
        )

    def test_safe_filename_preserves_pdf_extension_after_truncation(self) -> None:
        doc = BudgetDocument(
            government="Municipal Corporation of Delhi",
            document_type="mcd_budget",
            fiscal_year="2025-26",
            title="Circular " + ("General Account Income and Expenditure Budget " * 12),
            url="https://mcdonline.nic.in/portal/downloadFile/long.pdf",
            source_page="https://mcdonline.nic.in/portal/showContent?menuguide=budget",
        )

        name = safe_filename(doc)

        self.assertLessEqual(len(name), 180)
        self.assertTrue(name.endswith(".pdf"))


if __name__ == "__main__":
    unittest.main()
