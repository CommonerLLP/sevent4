import unittest

from scripts.recipes.comparators.build_library_ifla_audit import (
    governance_rows,
    ifla_rows,
    legal_rows,
    service_detail_rows,
)


class LibraryIflaAuditTest(unittest.TestCase):
    def test_ifla_rows_audit_ahmedabad_and_delhi_core_metrics(self) -> None:
        rows = ifla_rows()
        by_city_metric = {(row["city"], row["metric_name"]): row for row in rows}

        self.assertEqual(by_city_metric[("ahmedabad", "service_points")]["status"], "available")
        self.assertEqual(by_city_metric[("ahmedabad", "registered_users")]["value"], "26834")
        self.assertEqual(by_city_metric[("delhi", "service_points")]["value"], "111")
        self.assertEqual(by_city_metric[("delhi", "full_time_staff")]["status"], "partial")
        self.assertEqual(by_city_metric[("delhi", "physical_visits")]["status"], "partial")

    def test_governance_rows_keep_verified_and_unverified_names_separate(self) -> None:
        rows = governance_rows()
        by_role = {(row["city"], row["role"]): row for row in rows}

        self.assertEqual(by_role[("ahmedabad", "Librarian")]["name"], "Dr Bipin J Modi")
        self.assertEqual(by_role[("ahmedabad", "Librarian")]["source_status"], "official_site_capture")
        self.assertEqual(by_role[("delhi", "Director General")]["source_status"], "secondary_web_unverified")

    def test_service_detail_rows_show_branchwise_capacity_gap(self) -> None:
        rows = service_detail_rows()
        by_city_field = {(row["city"], row["detail_field"]): row for row in rows}

        self.assertEqual(by_city_field[("ahmedabad", "max_seating_capacity")]["locations_with_value"], "0")
        self.assertEqual(by_city_field[("delhi", "opening_hours")]["locations_with_value"], "0")
        self.assertEqual(by_city_field[("delhi", "collection_types")]["status"], "missing_branchwise_public_detail")

    def test_legal_rows_include_dpl_board_and_mj_library_board(self) -> None:
        rows = legal_rows()
        instruments = {(row["city"], row["instrument_or_body"]) for row in rows}

        self.assertIn(("delhi", "Delhi Library Board"), instruments)
        self.assertIn(("ahmedabad", "M.J. Library Board / Library Committee"), instruments)


if __name__ == "__main__":
    unittest.main()
