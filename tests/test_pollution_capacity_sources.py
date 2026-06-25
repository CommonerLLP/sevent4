"""Tests for the five-city PCB/PCC regulator-capacity source inventories.

The pollution layer pairs pollution *burden* (AQI stations, already present) with
regulator *capacity* (sanctioned/filled/vacant posts, budget, labs, inspections,
consents, enforcement). These tests assert that every ready city has a structured,
honestly-labelled source inventory + capacity-fact file, per the source-role
discipline in docsx/source-policy-and-readiness.md.
"""

import json
import unittest
from pathlib import Path

READY_CITIES = ["ahmedabad", "bengaluru", "chennai", "delhi", "kolkata"]

VALID_SOURCE_ROLES = {
    "official_record",
    "court_record",
    "secondary_research",
    "news_corroboration",
}
VALID_STATUS = {"found", "partial", "not_found"}


def pollution_dir(city: str) -> Path:
    return Path("data/cities") / city / "source" / "pollution"


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class PollutionCapacitySourcesTest(unittest.TestCase):
    def test_every_ready_city_has_a_pollution_source_inventory(self) -> None:
        for city in READY_CITIES:
            sources_path = pollution_dir(city) / "sources.json"
            self.assertTrue(
                sources_path.exists(),
                f"{city}: missing pollution sources.json",
            )
            data = load(sources_path)
            self.assertEqual(data.get("city"), city)
            self.assertTrue(data.get("board"), f"{city}: no board named")
            self.assertGreaterEqual(
                len(data.get("sources", [])),
                1,
                f"{city}: no pollution sources listed",
            )

    def test_every_source_has_a_valid_role_and_url(self) -> None:
        for city in READY_CITIES:
            data = load(pollution_dir(city) / "sources.json")
            for src in data["sources"]:
                self.assertIn(
                    src.get("source_role"),
                    VALID_SOURCE_ROLES,
                    f"{city}: bad source_role on {src.get('id')}",
                )
                self.assertTrue(src.get("id"), f"{city}: a source has no id")
                self.assertTrue(src.get("url"), f"{city}: {src.get('id')} has no url")

    def test_every_ready_city_has_capacity_facts(self) -> None:
        for city in READY_CITIES:
            cap_path = pollution_dir(city) / "capacity.json"
            self.assertTrue(cap_path.exists(), f"{city}: missing capacity.json")
            data = load(cap_path)
            facts = data.get("facts", [])
            self.assertGreaterEqual(len(facts), 1, f"{city}: no capacity facts")
            source_ids = {s["id"] for s in load(pollution_dir(city) / "sources.json")["sources"]}
            for fact in facts:
                self.assertIn(
                    fact.get("status"),
                    VALID_STATUS,
                    f"{city}: bad status on metric {fact.get('metric')}",
                )
                self.assertTrue(fact.get("metric"), f"{city}: a fact has no metric")
                self.assertTrue(
                    fact.get("source_url"),
                    f"{city}: {fact.get('metric')} has no source_url",
                )
                # not_found facts must carry a null value; found facts must not.
                if fact.get("status") == "not_found":
                    self.assertIsNone(
                        fact.get("value"),
                        f"{city}: {fact.get('metric')} is not_found but has a value",
                    )
                # every fact must reference a declared source row
                self.assertIn(
                    fact.get("source_id"),
                    source_ids,
                    f"{city}: {fact.get('metric')} references unknown source_id "
                    f"{fact.get('source_id')}",
                )

    def test_national_baseline_present(self) -> None:
        base = Path("data/national/pollution")
        self.assertTrue((base / "sources.json").exists(), "national sources.json missing")
        self.assertTrue((base / "capacity.json").exists(), "national capacity.json missing")
        cap = load(base / "capacity.json")
        metrics = {f["metric"] for f in cap["facts"]}
        self.assertIn("spcb_vacancy_pct", metrics)

    def test_at_least_three_cities_have_a_found_capacity_fact(self) -> None:
        # Delhi (CPR), Kolkata (Rajya Sabha), Bengaluru (Deccan Herald) carry hard
        # board-specific numbers; assert acquisition produced real data, not only stubs.
        cities_with_found = 0
        for city in READY_CITIES:
            facts = load(pollution_dir(city) / "capacity.json")["facts"]
            if any(f.get("status") == "found" and f.get("scope") in {"state", "nct"} for f in facts):
                cities_with_found += 1
        self.assertGreaterEqual(
            cities_with_found,
            3,
            "expected board-specific found facts for at least 3 ready cities",
        )


if __name__ == "__main__":
    unittest.main()
