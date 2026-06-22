import unittest

from sevent4.contracts import (
    ClaimRecord,
    FactRecord,
    SourceProfile,
    validate_claims_against_facts,
)


def source_profile(**overrides):
    data = {
        "id": "in-ka-kspcb-annual-reports",
        "country": "IN",
        "institution": "Karnataka State Pollution Control Board",
        "source_family": "annual_reports",
        "transport": "browser-rendered",
        "source_role": "official_record",
        "owner_repo": "commoner-probe",
        "retrieval_date": "2026-06-22",
    }
    data.update(overrides)
    return data


def fact_record(**overrides):
    data = {
        "id": "fact-kspcb-budget-total-expenditure-2023-24",
        "kind": "AirBoardFinanceFact",
        "metric": "budget_total_expenditure",
        "value": 78.85,
        "unit": "INR_crore",
        "period": "2023-24",
        "source_id": "in-ka-kspcb-annual-reports",
        "source_locator": "chapter 9 finance table",
        "extractor": "pollution-board-annual-report-finance-v1",
        "confidence": "high",
        "status": "found",
        "geography": {
            "country": "IN",
            "state": "Karnataka",
            "city": "Bengaluru",
        },
    }
    data.update(overrides)
    return data


def claim_record(**overrides):
    data = {
        "id": "claim-why-air-kspcb-expenditure-2023-24",
        "text": "KSPCB spent Rs 78.85 crore in 2023-24.",
        "fact_ids": ["fact-kspcb-budget-total-expenditure-2023-24"],
        "public_route": "/why/air/",
        "constitutional_relevance": {
            "twelfth_schedule_function": "public health, sanitation, conservancy and solid waste management",
            "gap_type": "regulator-without-municipal-accountability",
        },
    }
    data.update(overrides)
    return data


class ArchitectureContractsTest(unittest.TestCase):
    def test_source_profile_names_source_not_fetcher_class(self) -> None:
        profile = SourceProfile.from_dict(source_profile())
        self.assertEqual(profile.id, "in-ka-kspcb-annual-reports")
        with self.assertRaisesRegex(ValueError, "not an implementation class"):
            SourceProfile.from_dict(source_profile(id="KspcbWebsiteFetcher"))

    def test_source_profile_separates_source_identity_from_transport(self) -> None:
        direct = SourceProfile.from_dict(source_profile(transport="direct-http"))
        socks = SourceProfile.from_dict(source_profile(transport="india-fetch-box-socks"))
        self.assertEqual(direct.id, socks.id)
        with self.assertRaisesRegex(ValueError, "invalid transport"):
            SourceProfile.from_dict(source_profile(transport="kspcb-website"))

    def test_fact_record_requires_value_for_found_facts(self) -> None:
        fact = FactRecord.from_dict(fact_record())
        self.assertEqual(fact.source_id, "in-ka-kspcb-annual-reports")
        with self.assertRaisesRegex(ValueError, "found facts must carry a value"):
            FactRecord.from_dict(fact_record(value=None))

    def test_not_found_fact_must_not_carry_a_value(self) -> None:
        fact = FactRecord.from_dict(fact_record(status="not_found", value=None))
        self.assertEqual(fact.status, "not_found")
        with self.assertRaisesRegex(ValueError, "not_found facts must use null value"):
            FactRecord.from_dict(fact_record(status="not_found", value=12))

    def test_claim_requires_absolute_route_and_constitutional_hook(self) -> None:
        claim = ClaimRecord.from_dict(claim_record())
        self.assertEqual(claim.public_route, "/why/air/")
        with self.assertRaisesRegex(ValueError, "public_route"):
            ClaimRecord.from_dict(claim_record(public_route="why/air"))
        with self.assertRaisesRegex(ValueError, "Twelfth Schedule"):
            ClaimRecord.from_dict(claim_record(constitutional_relevance={"gap_type": "missing"}))

    def test_claim_fact_references_are_checked(self) -> None:
        facts = [FactRecord.from_dict(fact_record())]
        claims = [ClaimRecord.from_dict(claim_record())]
        validate_claims_against_facts(claims, facts)
        bad_claims = [ClaimRecord.from_dict(claim_record(fact_ids=["missing-fact"]))]
        with self.assertRaisesRegex(ValueError, "unknown facts"):
            validate_claims_against_facts(bad_claims, facts)


if __name__ == "__main__":
    unittest.main()
