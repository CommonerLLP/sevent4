import unittest


class DevolutionScorecardPortsTest(unittest.TestCase):
    def test_scorecard_builder_computes_registry_rows_and_preserves_special_cases(self) -> None:
        from sevent4.application.public_site import build_devolution_scorecard

        service_map = {
            "ahmedabad": {
                "water": {"type": "corporation", "provider": "AMC"},
                "metro": {"type": "spv", "provider": "GMRC"},
                "electricity": {"type": "private", "provider": "Torrent"},
                "police": {"type": "state_dept", "provider": "Gujarat Police"},
            },
            "nagpur": {
                "water": {"type": "corporation", "provider": "NMC"},
            },
        }
        existing = {
            "delhi": {
                "name": "Delhi",
                "elected": 2,
                "n": 10,
                "pct": 20,
                "decided": {"city": 2, "state": 6, "centre": 2, "total": 10, "pct_city": 20},
                "taken": [],
            }
        }

        result = build_devolution_scorecard(service_map, ("ahmedabad", "delhi"), existing)

        self.assertEqual(result.preserved, ("delhi",))
        self.assertEqual(result.dropped, ("nagpur",))
        self.assertEqual(set(result.scorecard), {"ahmedabad", "delhi"})
        self.assertEqual(result.scorecard["ahmedabad"]["elected"], 1)
        self.assertEqual(result.scorecard["ahmedabad"]["n"], 2)
        self.assertEqual(result.scorecard["ahmedabad"]["pct"], 50)
        self.assertEqual(
            result.scorecard["ahmedabad"]["decided"],
            {"city": 1, "state": 3, "centre": 0, "total": 4, "pct_city": 25},
        )
        self.assertEqual(
            result.scorecard["ahmedabad"]["taken"],
            [{"service": "Metro", "provider": "GMRC", "by": "a state SPV"}],
        )
        self.assertEqual(
            result.governance_updates["ahmedabad"],
            {
                "devolution": {"elected": 1, "total": 2, "pct": 50},
                "decided_by": {"city": 1, "state": 3, "centre": 0, "total": 4, "pct_city": 25},
            },
        )

    def test_scorecard_publisher_uses_repository_and_writer_ports(self) -> None:
        from sevent4.application.public_site import publish_devolution_scorecard_from_repository

        class Repository:
            def load_service_providers(self):
                return {
                    "ahmedabad": {
                        "water": {"type": "corporation", "provider": "AMC"},
                        "metro": {"type": "spv", "provider": "GMRC"},
                    }
                }

            def load_registry_city_ids(self):
                return ("ahmedabad",)

            def load_existing_scorecard(self):
                return {}

        class Publisher:
            def __init__(self) -> None:
                self.scorecard = None
                self.governance_updates = []

            def write_scorecard(self, scorecard):
                self.scorecard = scorecard

            def write_governance_metrics(self, city_id, update):
                self.governance_updates.append((city_id, update))
                return True

        publisher = Publisher()
        result = publish_devolution_scorecard_from_repository(Repository(), publisher)

        self.assertEqual(publisher.scorecard, result.scorecard)
        self.assertEqual(
            publisher.governance_updates,
            [
                (
                    "ahmedabad",
                    {
                        "devolution": {"elected": 1, "total": 2, "pct": 50},
                        "decided_by": {"city": 1, "state": 1, "centre": 0, "total": 2, "pct_city": 50},
                    },
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
