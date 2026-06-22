import json
import unittest
from pathlib import Path

from sevent4.contracts import load_evidence_bundle, validate_page_claim_ids


BOARDS_PATH = Path("public/why/air/boards.json")
CLAIMS_PATH = Path("public/why/air/claims.json")
HTML_PATH = Path("public/why/air/index.html")


class WhyAirClaimContractsTest(unittest.TestCase):
    def test_evidence_bundle_is_discoverable_from_page(self) -> None:
        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('href="claims.json"', html)
        self.assertIn('type="application/json"', html)

    def test_rendered_claim_ids_exist_in_evidence_bundle(self) -> None:
        validate_page_claim_ids(HTML_PATH, load_evidence_bundle(CLAIMS_PATH))

    def test_kspcb_finance_claim_is_backed_by_facts_and_rendered(self) -> None:
        boards = {row["city"]: row for row in json.loads(BOARDS_PATH.read_text())["boards"]}
        kspcb = boards["bengaluru"]
        bundle = load_evidence_bundle(CLAIMS_PATH)

        facts = {fact.metric: fact for fact in bundle.facts if fact.source_id == "in-ka-kspcb-annual-reports"}
        self.assertAlmostEqual(facts["budget_opening_balance"].value, kspcb["cash_opening_balance_cr"])
        self.assertAlmostEqual(facts["budget_total_receipts"].value, kspcb["receipts_cr"])
        self.assertAlmostEqual(facts["budget_total_expenditure"].value, kspcb["expenditure_cr"])
        self.assertAlmostEqual(facts["budget_interest_income"].value, kspcb["interest_cr"])

        claim = bundle.claim_by_id("claim-why-air-kspcb-finance-2023-24")
        self.assertEqual(
            set(claim.fact_ids),
            {
                facts["budget_opening_balance"].id,
                facts["budget_total_receipts"].id,
                facts["budget_total_expenditure"].id,
                facts["budget_interest_income"].id,
            },
        )
        self.assertIn(f'data-claim-id="{claim.id}"', HTML_PATH.read_text(encoding="utf-8"))

    def test_all_pollution_board_finance_claims_are_backed_by_board_data(self) -> None:
        boards = {row["city"]: row for row in json.loads(BOARDS_PATH.read_text())["boards"]}
        bundle = load_evidence_bundle(CLAIMS_PATH)
        facts = {fact.id: fact for fact in bundle.facts}

        expected = {
            "claim-why-air-gpcb-surplus-2024-25": {
                "city": "ahmedabad",
                "source_id": "in-gj-gpcb-annual-reports",
                "metrics": {"accumulated_surplus": "surplus_cr"},
            },
            "claim-why-air-tnpcb-surplus-2024-25": {
                "city": "chennai",
                "source_id": "in-tn-tnpcb-annual-reports",
                "metrics": {
                    "accumulated_surplus": "surplus_cr",
                    "government_grant": "govt_grant_cr",
                    "budget_interest_income": "interest_cr",
                },
            },
            "claim-why-air-kspcb-finance-2023-24": {
                "city": "bengaluru",
                "source_id": "in-ka-kspcb-annual-reports",
                "metrics": {
                    "budget_opening_balance": "cash_opening_balance_cr",
                    "budget_total_receipts": "receipts_cr",
                    "budget_total_expenditure": "expenditure_cr",
                    "budget_interest_income": "interest_cr",
                },
            },
        }

        html = HTML_PATH.read_text(encoding="utf-8")
        for claim_id, spec in expected.items():
            claim = bundle.claim_by_id(claim_id)
            self.assertIn(f'data-claim-id="{claim_id}"', html)
            claim_facts = [facts[fact_id] for fact_id in claim.fact_ids]
            self.assertTrue(claim_facts, f"{claim_id}: no facts")
            self.assertTrue(
                all(fact.source_id == spec["source_id"] for fact in claim_facts),
                f"{claim_id}: mixed or wrong source ids",
            )
            values = {fact.metric: fact.value for fact in claim_facts}
            board = boards[spec["city"]]
            for metric, board_key in spec["metrics"].items():
                self.assertAlmostEqual(values[metric], board[board_key], msg=f"{claim_id}: {metric}")

    def test_finance_board_rows_point_to_claim_records(self) -> None:
        boards = json.loads(BOARDS_PATH.read_text())["boards"]
        bundle = load_evidence_bundle(CLAIMS_PATH)
        claim_ids = {claim.id for claim in bundle.claims}

        rows_with_finance = [row for row in boards if row.get("finance_source")]
        self.assertGreaterEqual(len(rows_with_finance), 3)
        for row in rows_with_finance:
            self.assertIn("finance_claim_id", row, f"{row['city']}: missing finance_claim_id")
            self.assertIn(row["finance_claim_id"], claim_ids, f"{row['city']}: unknown finance_claim_id")

    def test_live_board_capacity_rows_point_to_claim_records(self) -> None:
        boards = json.loads(BOARDS_PATH.read_text())["boards"]
        bundle = load_evidence_bundle(CLAIMS_PATH)
        claim_ids = {claim.id for claim in bundle.claims}

        live_rows = [row for row in boards if row.get("status") == "live"]
        self.assertGreaterEqual(len(live_rows), 5)
        for row in live_rows:
            self.assertIn("capacity_claim_id", row, f"{row['city']}: missing capacity_claim_id")
            self.assertIn(row["capacity_claim_id"], claim_ids, f"{row['city']}: unknown capacity_claim_id")

    def test_live_board_capacity_claims_are_backed_by_board_data(self) -> None:
        boards = json.loads(BOARDS_PATH.read_text())["boards"]
        bundle = load_evidence_bundle(CLAIMS_PATH)
        facts = {fact.id: fact for fact in bundle.facts}

        for row in boards:
            if row.get("status") != "live":
                continue
            claim = bundle.claim_by_id(row["capacity_claim_id"])
            values = {facts[fact_id].metric: facts[fact_id].value for fact_id in claim.fact_ids}
            self.assertEqual(values["posts_sanctioned"], row["sanctioned"], row["city"])
            self.assertEqual(values["posts_vacant"], row["vacant"], row["city"])
            self.assertEqual(values["vacancy_pct"], row["vacancy_pct"], row["city"])

    def test_roster_template_renders_capacity_claim_ids(self) -> None:
        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("data-claim-id=\"${b.capacity_claim_id||''}\"", html)


if __name__ == "__main__":
    unittest.main()
