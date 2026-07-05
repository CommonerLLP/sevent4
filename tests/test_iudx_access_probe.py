import json
import tempfile
import unittest
from pathlib import Path

from sevent4.transit.iudx_access_probe import (
    build_status_packet,
    classify_token_response,
    iter_request_resources,
    load_access_request_packet,
    normalize_probe_payload,
    summarize_bmrcl_export_field_coverage,
    summarize_catalogue_samples,
    summarize_post_approval_readiness,
    summarize_static_gtfs_field_coverage,
    summarize_static_gtfs_resource_map,
    summarize_static_gtfs_table_coverage,
    summarize_probe_results,
    token_request_payload,
)


class IudxAccessProbeTest(unittest.TestCase):
    def test_packet_resources_preserve_priority_order_and_static_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / "packet.json"
            packet.write_text(
                json.dumps(
                    {
                        "request_priority": [
                            {
                                "priority": 1,
                                "name": "BMTC static",
                                "resources": [
                                    {
                                        "id": "agency-id",
                                        "label": "Agency",
                                        "itemType": "resource",
                                        "resourceType": "DATASET",
                                        "required_for_static_gtfs": True,
                                    },
                                    {
                                        "id": "realtime-id",
                                        "label": "Realtime",
                                        "itemType": "resource",
                                        "resourceType": "MESSAGESTREAM",
                                        "required_for_static_gtfs": False,
                                    },
                                ],
                            },
                            {
                                "priority": 2,
                                "name": "Metro schedule",
                                "resources": [
                                    {
                                        "id": "schedule-id",
                                        "label": "Schedule",
                                        "itemType": "resource",
                                        "resourceType": "FILE",
                                        "required_for_static_gtfs": True,
                                    }
                                ],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            loaded = load_access_request_packet(packet)
            resources = list(iter_request_resources(loaded, static_only=True))

        self.assertEqual([resource.id for resource in resources], ["agency-id", "schedule-id"])
        self.assertEqual(resources[0].priority, 1)
        self.assertEqual(resources[0].group_name, "BMTC static")
        self.assertEqual(resources[1].resource_type, "FILE")

    def test_token_request_payload_uses_iudx_consumer_resource_shape(self) -> None:
        resource = next(
            iter_request_resources(
                {
                    "request_priority": [
                        {
                            "priority": 1,
                            "name": "BMTC static",
                            "resources": [
                                {
                                    "id": "stops-id",
                                    "label": "Stops",
                                    "itemType": "resource",
                                    "resourceType": "MESSAGESTREAM",
                                    "required_for_static_gtfs": True,
                                }
                            ],
                        }
                    ]
                }
            )
        )

        self.assertEqual(
            token_request_payload(resource),
            {"itemId": "stops-id", "itemType": "resource", "role": "consumer"},
        )

    def test_token_response_summary_classifies_gate_and_never_includes_token(self) -> None:
        resource = next(
            iter_request_resources(
                {
                    "request_priority": [
                        {
                            "priority": 1,
                            "name": "BMTC static",
                            "resources": [
                                {
                                    "id": "trips-id",
                                    "label": "Trips",
                                    "itemType": "resource",
                                    "resourceType": "MESSAGESTREAM",
                                    "required_for_static_gtfs": True,
                                }
                            ],
                        }
                    ]
                }
            )
        )

        gated = classify_token_response(
            resource,
            403,
            {
                "type": "urn:dx:as:InvalidAuthorization",
                "title": "APD evaluation failed",
                "detail": "No policy exist for given item's Resource Group",
            },
        )
        ok = classify_token_response(
            resource,
            200,
            {"results": {"accessToken": "secret-token-value"}},
        )

        self.assertEqual(gated["status"], "gated")
        self.assertIn("No policy exist", gated["detail"])
        self.assertEqual(ok["status"], "ok")
        self.assertTrue(ok["token_available"])
        self.assertNotIn("secret-token-value", json.dumps(ok))

    def test_probe_result_summary_groups_statuses_without_credentials(self) -> None:
        results = [
            {
                "group": "BMTC static GTFS tables",
                "status": "gated",
                "token_available": False,
            },
            {
                "group": "BMTC static GTFS tables",
                "status": "gated",
                "token_available": False,
            },
            {
                "group": "BMRCL schedule and fare files",
                "status": "ok",
                "token_available": True,
            },
        ]

        summary = summarize_probe_results(results)

        self.assertEqual(summary["by_status"], {"gated": 2, "ok": 1})
        self.assertEqual(
            summary["by_group"],
            {
                "BMTC static GTFS tables": {"gated": 2},
                "BMRCL schedule and fare files": {"ok": 1},
            },
        )
        self.assertNotIn("token", json.dumps(summary).lower())

    def test_normalize_probe_payload_adds_missing_summary_and_normalized_timestamp(self) -> None:
        payload = {
            "schema": "sevent4.iudx_access_probe_results.v1",
            "resource_count": 2,
            "results": [
                {"group": "BMTC static GTFS tables", "status": "gated"},
                {"group": "BMRCL schedule and fare files", "status": "gated"},
            ],
        }

        normalized = normalize_probe_payload(payload, normalized_at="2026-07-04T18:31:00Z")

        self.assertNotIn("generated_at", normalized)
        self.assertEqual(normalized["normalized_at"], "2026-07-04T18:31:00Z")
        self.assertEqual(normalized["summary"]["by_status"], {"gated": 2})
        self.assertEqual(
            normalized["summary"]["by_group"],
            {
                "BMTC static GTFS tables": {"gated": 1},
                "BMRCL schedule and fare files": {"gated": 1},
            },
        )
        self.assertEqual(normalized["results"], payload["results"])

    def test_catalogue_sample_summary_separates_file_links_from_inline_examples(self) -> None:
        summaries = summarize_catalogue_samples(
            [
                {
                    "results": [
                        {
                            "dataset": {"id": "bmtc-dataset", "label": "BMTC GTFS"},
                            "resource": [
                                {
                                    "resourceId": "agency-id",
                                    "label": "GTFS agency",
                                    "accessPolicy": "SECURE",
                                    "resourceType": "DATASET",
                                    "dataSample": {"agency_id": "080"},
                                },
                                {
                                    "resourceId": "schedule-id",
                                    "label": "Metro schedule",
                                    "accessPolicy": "SECURE",
                                    "resourceType": "FILE",
                                    "dataSampleFile": [
                                        {
                                            "name": "Schedule sample",
                                            "hasObject": "",
                                        }
                                    ],
                                },
                                {
                                    "resourceId": "lines-id",
                                    "label": "Metro lines",
                                    "accessPolicy": "SECURE",
                                    "resourceType": "GSLAYER",
                                    "dataSampleFile": [
                                        {
                                            "name": "Lines sample",
                                            "hasObject": "https://example.test/lines.json",
                                        }
                                    ],
                                },
                            ],
                        }
                    ]
                }
            ]
        )

        self.assertEqual(
            summaries,
            [
                {
                    "dataset_id": "bmtc-dataset",
                    "dataset_label": "BMTC GTFS",
                    "resource_count": 3,
                    "secure_resource_count": 3,
                    "public_sample_file_count": 1,
                    "empty_sample_file_count": 1,
                    "inline_sample_resource_count": 1,
                    "public_sample_files": [
                        {
                            "resource_id": "lines-id",
                            "resource_label": "Metro lines",
                            "name": "Lines sample",
                            "url": "https://example.test/lines.json",
                        }
                    ],
                }
            ],
        )

    def test_static_gtfs_table_coverage_flags_missing_stop_times(self) -> None:
        coverage = summarize_static_gtfs_table_coverage(
            [
                {
                    "results": [
                        {
                            "dataset": {"id": "bmtc-dataset", "label": "BMTC GTFS"},
                            "resource": [
                                {"resourceId": "agency-id", "label": "GTFS agency"},
                                {"resourceId": "calendar-id", "label": "GTFS calendar"},
                                {"resourceId": "routes-id", "label": "GTFS routes"},
                                {"resourceId": "stops-id", "label": "GTFS stops"},
                                {"resourceId": "trips-id", "label": "GTFS trips"},
                                {"resourceId": "realtime-id", "label": "GTFS realtime vehicle positions"},
                            ],
                        }
                    ]
                }
            ]
        )

        self.assertEqual(
            coverage,
            [
                {
                    "dataset_id": "bmtc-dataset",
                    "dataset_label": "BMTC GTFS",
                    "required_tables_for_stop_sequence_geometry": [
                        "agency",
                        "calendar",
                        "routes",
                        "stops",
                        "trips",
                        "stop_times",
                    ],
                    "advertised_tables": ["agency", "calendar", "routes", "stops", "trips"],
                    "missing_required_tables": ["stop_times"],
                    "stop_sequence_geometry_ready": False,
                }
            ],
        )

    def test_static_gtfs_field_coverage_checks_required_fields_per_advertised_table(self) -> None:
        coverage = summarize_static_gtfs_field_coverage(
            [
                {
                    "results": [
                        {
                            "dataset": {"id": "bmtc-dataset", "label": "BMTC GTFS"},
                            "resource": [
                                {
                                    "label": "GTFS agency",
                                    "dataDescriptor": {
                                        "agency_id": {},
                                        "agency_name": {},
                                        "agency_url": {},
                                        "agency_timezone": {},
                                    },
                                },
                                {
                                    "label": "GTFS routes",
                                    "dataDescriptor": {
                                        "route_id": {},
                                        "agency_id": {},
                                        "route_short_name": {},
                                        "route_long_name": {},
                                        "route_type": {},
                                    },
                                },
                                {
                                    "label": "GTFS stops",
                                    "dataDescriptor": {
                                        "stop_id": {},
                                        "stop_name": {},
                                        "stop_lat": {},
                                        "stop_lon": {},
                                    },
                                },
                            ],
                        }
                    ]
                }
            ]
        )

        self.assertEqual(
            coverage,
            [
                {
                    "dataset_id": "bmtc-dataset",
                    "dataset_label": "BMTC GTFS",
                    "tables": [
                        {
                            "table": "agency",
                            "required_fields": [
                                "agency_id",
                                "agency_name",
                                "agency_url",
                                "agency_timezone",
                            ],
                            "advertised_fields": [
                                "agency_id",
                                "agency_name",
                                "agency_timezone",
                                "agency_url",
                            ],
                            "missing_required_fields": [],
                        },
                        {
                            "table": "routes",
                            "required_fields": [
                                "route_id",
                                "agency_id",
                                "route_short_name",
                                "route_long_name",
                                "route_type",
                            ],
                            "advertised_fields": [
                                "agency_id",
                                "route_id",
                                "route_long_name",
                                "route_short_name",
                                "route_type",
                            ],
                            "missing_required_fields": [],
                        },
                        {
                            "table": "stops",
                            "required_fields": [
                                "stop_id",
                                "stop_name",
                                "stop_lat",
                                "stop_lon",
                            ],
                            "advertised_fields": [
                                "stop_id",
                                "stop_lat",
                                "stop_lon",
                                "stop_name",
                            ],
                            "missing_required_fields": [],
                        },
                        {
                            "table": "stop_times",
                            "required_fields": [
                                "trip_id",
                                "arrival_time",
                                "departure_time",
                                "stop_id",
                                "stop_sequence",
                            ],
                            "advertised_fields": [],
                            "missing_required_fields": [
                                "trip_id",
                                "arrival_time",
                                "departure_time",
                                "stop_id",
                                "stop_sequence",
                            ],
                        },
                    ],
                    "advertised_table_fields_ready": False,
                }
            ],
        )

    def test_bmrcl_export_field_coverage_checks_network_station_and_schedule_descriptors(self) -> None:
        coverage = summarize_bmrcl_export_field_coverage(
            [
                {
                    "results": [
                        {
                            "dataset": {"id": "network-dataset", "label": "Metro Rail Network Info"},
                            "resource": [
                                {
                                    "resourceId": "lines-id",
                                    "label": "Metro Rail Lines in Bengaluru City",
                                    "resourceType": "GSLAYER",
                                    "dataDescriptor": {
                                        "routeStopSequence": {},
                                        "route_id": {},
                                        "route_short_name": {},
                                        "route_long_name": {},
                                        "location": {},
                                    },
                                },
                                {
                                    "resourceId": "stations-id",
                                    "label": "Metro Station Locations in Bengaluru City",
                                    "resourceType": "GSLAYER",
                                    "dataDescriptor": {
                                        "stop_name": {},
                                        "stop_code": {},
                                        "location": {},
                                    },
                                },
                            ],
                        }
                    ]
                },
                {
                    "results": [
                        {
                            "dataset": {"id": "operations-dataset", "label": "Metro Rail Operations Info"},
                            "resource": [
                                {
                                    "resourceId": "schedule-id",
                                    "label": "Metro Rail Schedule Info in Bengaluru City",
                                    "resourceType": "FILE",
                                    "dataDescriptor": {
                                        "stationCode": {},
                                        "arrival_time": {},
                                        "departure_time": {},
                                        "train_id": {},
                                        "route_id": {},
                                    },
                                },
                                {
                                    "resourceId": "fare-id",
                                    "label": "Metro Rail Fare Info in Bengaluru City",
                                    "resourceType": "FILE",
                                    "dataDescriptor": {
                                        "originDestinationCode": {},
                                        "fareForAdult": {},
                                    },
                                },
                            ],
                        }
                    ]
                },
            ]
        )

        self.assertEqual(
            coverage,
            {
                "required_export_files": ["stations.json", "lines.json", "schedule.json"],
                "export_ready_fields": True,
                "files": [
                    {
                        "export_file": "stations.json",
                        "resource_id": "stations-id",
                        "resource_label": "Metro Station Locations in Bengaluru City",
                        "dataset_id": "network-dataset",
                        "dataset_label": "Metro Rail Network Info",
                        "resource_type": "GSLAYER",
                        "required_fields": ["stop_code", "stop_name", "location"],
                        "advertised_fields": ["location", "stop_code", "stop_name"],
                        "missing_required_fields": [],
                    },
                    {
                        "export_file": "lines.json",
                        "resource_id": "lines-id",
                        "resource_label": "Metro Rail Lines in Bengaluru City",
                        "dataset_id": "network-dataset",
                        "dataset_label": "Metro Rail Network Info",
                        "resource_type": "GSLAYER",
                        "required_fields": [
                            "route_id",
                            "route_short_name",
                            "route_long_name",
                            "routeStopSequence",
                            "location",
                        ],
                        "advertised_fields": [
                            "location",
                            "routeStopSequence",
                            "route_id",
                            "route_long_name",
                            "route_short_name",
                        ],
                        "missing_required_fields": [],
                    },
                    {
                        "export_file": "schedule.json",
                        "resource_id": "schedule-id",
                        "resource_label": "Metro Rail Schedule Info in Bengaluru City",
                        "dataset_id": "operations-dataset",
                        "dataset_label": "Metro Rail Operations Info",
                        "resource_type": "FILE",
                        "required_fields": [
                            "stationCode",
                            "arrival_time",
                            "departure_time",
                            "train_id",
                            "route_id",
                        ],
                        "advertised_fields": [
                            "arrival_time",
                            "departure_time",
                            "route_id",
                            "stationCode",
                            "train_id",
                        ],
                        "missing_required_fields": [],
                    },
                ],
                "missing_export_files": [],
            },
        )

    def test_static_gtfs_resource_map_links_iudx_resources_to_gtfs_files(self) -> None:
        resource_map = summarize_static_gtfs_resource_map(
            [
                {
                    "results": [
                        {
                            "dataset": {"id": "bmtc-dataset", "label": "BMTC GTFS"},
                            "resource": [
                                {
                                    "resourceId": "agency-id",
                                    "label": "GTFS agency",
                                    "resourceType": "DATASET",
                                    "iudxResourceAPIs": ["ATTR"],
                                    "accessPolicy": "SECURE",
                                },
                                {
                                    "resourceId": "routes-id",
                                    "label": "GTFS routes",
                                    "resourceType": "MESSAGESTREAM",
                                    "iudxResourceAPIs": ["ATTR", "TEMPORAL"],
                                    "accessPolicy": "SECURE",
                                },
                            ],
                        }
                    ]
                }
            ]
        )

        self.assertEqual(
            resource_map,
            [
                {
                    "dataset_id": "bmtc-dataset",
                    "dataset_label": "BMTC GTFS",
                    "resources": [
                        {
                            "gtfs_table": "agency",
                            "gtfs_filename": "agency.txt",
                            "resource_id": "agency-id",
                            "resource_label": "GTFS agency",
                            "resource_type": "DATASET",
                            "iudx_resource_apis": ["ATTR"],
                            "access_policy": "SECURE",
                        },
                        {
                            "gtfs_table": "routes",
                            "gtfs_filename": "routes.txt",
                            "resource_id": "routes-id",
                            "resource_label": "GTFS routes",
                            "resource_type": "MESSAGESTREAM",
                            "iudx_resource_apis": ["ATTR", "TEMPORAL"],
                            "access_policy": "SECURE",
                        },
                    ],
                    "missing_gtfs_filenames": [
                        "calendar.txt",
                        "stops.txt",
                        "trips.txt",
                        "stop_times.txt",
                    ],
                }
            ],
        )

    def test_post_approval_readiness_rollup_names_remaining_bmtc_and_bmrcl_gates(self) -> None:
        readiness = summarize_post_approval_readiness(
            post_approval_build={
                "bmtc_static_gtfs": {
                    "required_input_files": [
                        "agency.json",
                        "calendar.json",
                        "routes.json",
                        "stops.json",
                        "trips.json",
                        "stop_times.json",
                    ],
                    "quality_gate": {"route_geometry_ready": True},
                },
                "bmrcl_full_network_schedule": {
                    "required_input_files": ["stations.json", "lines.json", "schedule.json"],
                    "quality_gate": {
                        "route_geometry_ready": True,
                        "missing_scheduled_operational_route_short_names": [],
                    },
                },
            },
            blocked_groups=["BMTC static GTFS tables", "BMRCL schedule and fare files"],
            gtfs_table_coverage=[
                {
                    "missing_required_tables": ["stop_times"],
                    "stop_sequence_geometry_ready": False,
                }
            ],
            gtfs_field_coverage=[{"advertised_table_fields_ready": False}],
            bmrcl_export_field_coverage={
                "export_ready_fields": True,
                "missing_export_files": [],
            },
        )

        self.assertEqual(
            readiness,
            [
                {
                    "build_key": "bmtc_static_gtfs",
                    "feed_id": "bengaluru_bmtc_iudx_full_gtfs",
                    "access_groups": ["BMTC static GTFS tables"],
                    "access_gated": True,
                    "catalogue_inputs_ready": False,
                    "missing_input_files_from_catalogue": ["stop_times.json"],
                    "required_input_files": [
                        "agency.json",
                        "calendar.json",
                        "routes.json",
                        "stops.json",
                        "trips.json",
                        "stop_times.json",
                    ],
                    "quality_gate": {"route_geometry_ready": True},
                    "remaining_gates": [
                        "policy_access",
                        "stop_times_or_equivalent_stop_sequence",
                    ],
                },
                {
                    "build_key": "bmrcl_full_network_schedule",
                    "feed_id": "bengaluru_bmrcl_iudx_full_network_schedule",
                    "access_groups": [
                        "BMRCL schedule and fare files",
                        "BMRCL network geospatial resources",
                    ],
                    "access_gated": True,
                    "catalogue_inputs_ready": True,
                    "missing_input_files_from_catalogue": [],
                    "required_input_files": ["stations.json", "lines.json", "schedule.json"],
                    "quality_gate": {
                        "route_geometry_ready": True,
                        "missing_scheduled_operational_route_short_names": [],
                    },
                    "remaining_gates": [
                        "policy_access",
                        "purple_green_yellow_scheduled_two_stop_trips",
                    ],
                },
            ],
        )

    def test_status_packet_combines_request_probe_and_coverage_gates(self) -> None:
        request_packet = {
            "schema": "sevent4.iudx_access_request_packet.v1",
            "request_priority": [
                {
                    "priority": 1,
                    "name": "BMTC static GTFS tables",
                    "resources": [
                        {
                            "id": "bmtc-stops",
                            "label": "Stops",
                            "itemType": "resource",
                            "resourceType": "MESSAGESTREAM",
                            "required_for_static_gtfs": True,
                        }
                    ],
                },
                {
                    "priority": 2,
                    "name": "BMRCL schedule and fare files",
                    "resources": [
                        {
                            "id": "bmrcl-schedule",
                            "label": "Schedule",
                            "itemType": "resource",
                            "resourceType": "FILE",
                            "required_for_static_gtfs": True,
                        }
                    ],
                },
            ],
            "success_evidence_after_approval": ["downloaded table rows"],
            "post_approval_build": {
                "bmtc_static_gtfs": {
                    "required_input_dir": "data/cities/bengaluru/source/transit/iudx/bmtc-approved-static-json",
                    "required_input_files": [
                        "agency.json",
                        "calendar.json",
                        "routes.json",
                        "stops.json",
                        "trips.json",
                        "stop_times.json",
                    ],
                    "command": ".venv/bin/python scripts/recipes/transit/build_bmtc_iudx_gtfs_from_exports.py --input-dir data/cities/bengaluru/source/transit/iudx/bmtc-approved-static-json --out-zip data/cities/bengaluru/source/transit/gtfs/bengaluru_bmtc_iudx_full_gtfs.zip --provenance data/cities/bengaluru/source/transit/iudx/bmtc_iudx_full_gtfs.sources.json --manifest-row data/cities/bengaluru/source/transit/iudx/bmtc_iudx_full_gtfs.feed.json --feed-manifest data/cities/bengaluru/source/transit/iudx/bmtc_iudx_full_gtfs.manifest.json",
                    "outputs": {
                        "gtfs_zip": "data/cities/bengaluru/source/transit/gtfs/bengaluru_bmtc_iudx_full_gtfs.zip",
                        "provenance": "data/cities/bengaluru/source/transit/iudx/bmtc_iudx_full_gtfs.sources.json",
                        "manifest_row": "data/cities/bengaluru/source/transit/iudx/bmtc_iudx_full_gtfs.feed.json",
                        "feed_manifest": "data/cities/bengaluru/source/transit/iudx/bmtc_iudx_full_gtfs.manifest.json",
                    },
                    "quality_gate": {
                        "route_geometry_ready": True,
                        "trips_with_two_or_more_stops_gt": 0,
                    },
                }
            },
        }
        probe = {
            "schema": "sevent4.iudx_access_probe_results.v1",
            "normalized_at": "2026-07-04T18:31:00Z",
            "results": [
                {"id": "bmtc-stops", "group": "BMTC static GTFS tables", "status": "gated"},
                {"id": "bmrcl-schedule", "group": "BMRCL schedule and fare files", "status": "gated"},
            ],
            "summary": {
                "by_status": {"gated": 2},
                "by_group": {
                    "BMTC static GTFS tables": {"gated": 1},
                    "BMRCL schedule and fare files": {"gated": 1},
                },
            },
        }
        transit_sources = {
            "feeds": [
                {
                    "feed_id": "bengaluru_bmrcl_metro_iudx_sample",
                    "status": "sample_public_constructed_gtfs",
                    "coverage_scope": {
                        "coverage_complete": False,
                        "expected_operational_route_short_names": [
                            "Purple Line",
                            "Green Line",
                            "Yellow Line",
                        ],
                        "sample_route_short_names": ["Purple Line", "Green Line"],
                        "missing_operational_route_short_names": ["Yellow Line"],
                        "unverified_or_upcoming_route_short_names": ["Pink Line", "Blue Line"],
                    },
                },
                {"feed_id": "bengaluru_bmtc_iudx_full_gtfs", "status": "gated"},
                {
                    "feed_id": "bengaluru_bmrcl_iudx_full_network_schedule",
                    "status": "gated",
                    "coverage_scope": {
                        "coverage_complete": False,
                        "expected_operational_route_short_names": [
                            "Purple Line",
                            "Green Line",
                            "Yellow Line",
                        ],
                        "sample_route_short_names": ["Purple Line", "Green Line"],
                        "missing_operational_route_short_names": ["Yellow Line"],
                        "unverified_or_upcoming_route_short_names": ["Pink Line", "Blue Line"],
                    },
                },
            ]
        }

        packet = build_status_packet(
            request_packet=request_packet,
            probe_payload=probe,
            transit_sources=transit_sources,
            catalogue_details=[
                {
                    "results": [
                        {
                            "dataset": {"id": "bmrcl-network", "label": "BMRCL network"},
                            "resource": [
                                {
                                    "resourceId": "lines-id",
                                    "label": "Metro lines",
                                    "accessPolicy": "SECURE",
                                    "resourceType": "GSLAYER",
                                    "dataSampleFile": [
                                        {
                                            "name": "Lines sample",
                                            "hasObject": "https://example.test/lines.json",
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                },
                {
                    "results": [
                        {
                            "dataset": {"id": "bmtc-dataset", "label": "BMTC GTFS"},
                            "resource": [
                                {
                                    "resourceId": "agency-id",
                                    "label": "GTFS agency",
                                    "dataDescriptor": {
                                        "agency_id": {},
                                        "agency_name": {},
                                        "agency_url": {},
                                        "agency_timezone": {},
                                    },
                                },
                                {
                                    "resourceId": "calendar-id",
                                    "label": "GTFS calendar",
                                    "dataDescriptor": {
                                        "service_id": {},
                                        "monday": {},
                                        "tuesday": {},
                                        "wednesday": {},
                                        "thursday": {},
                                        "friday": {},
                                        "saturday": {},
                                        "sunday": {},
                                        "start_date": {},
                                        "end_date": {},
                                    },
                                },
                                {
                                    "resourceId": "routes-id",
                                    "label": "GTFS routes",
                                    "dataDescriptor": {
                                        "route_id": {},
                                        "agency_id": {},
                                        "route_short_name": {},
                                        "route_long_name": {},
                                        "route_type": {},
                                    },
                                },
                                {
                                    "resourceId": "stops-id",
                                    "label": "GTFS stops",
                                    "dataDescriptor": {
                                        "stop_id": {},
                                        "stop_name": {},
                                        "stop_lat": {},
                                        "stop_lon": {},
                                    },
                                },
                                {
                                    "resourceId": "trips-id",
                                    "label": "GTFS trips",
                                    "dataDescriptor": {
                                        "route_id": {},
                                        "service_id": {},
                                        "trip_id": {},
                                    },
                                },
                            ],
                        }
                    ]
                }
            ],
            compiled_at="2026-07-04T18:42:00Z",
        )

        self.assertEqual(packet["schema"], "sevent4.iudx_bengaluru_status.v1")
        self.assertEqual(packet["compiled_at"], "2026-07-04T18:42:00Z")
        self.assertEqual(packet["requested_resource_count"], 2)
        self.assertEqual(packet["static_required_resource_count"], 2)
        self.assertEqual(packet["latest_probe"]["summary"]["by_status"], {"gated": 2})
        self.assertEqual(
            packet["blocked_groups"],
            ["BMTC static GTFS tables", "BMRCL schedule and fare files"],
        )
        self.assertEqual(
            packet["gated_feed_ids"],
            ["bengaluru_bmtc_iudx_full_gtfs", "bengaluru_bmrcl_iudx_full_network_schedule"],
        )
        self.assertEqual(
            packet["sample_coverage_gaps"],
            [
                {
                    "feed_id": "bengaluru_bmrcl_metro_iudx_sample",
                    "expected_operational_route_short_names": [
                        "Purple Line",
                        "Green Line",
                        "Yellow Line",
                    ],
                    "sample_route_short_names": ["Purple Line", "Green Line"],
                    "missing_operational_route_short_names": ["Yellow Line"],
                }
            ],
        )
        self.assertEqual(
            packet["bmrcl_operational_line_scope"],
            {
                "confirmed_operational_route_short_names": [
                    "Purple Line",
                    "Green Line",
                    "Yellow Line",
                ],
                "confirmed_operational_route_count": 3,
                "public_iudx_sample_route_short_names": ["Purple Line", "Green Line"],
                "public_iudx_sample_route_count": 2,
                "missing_from_public_iudx_sample": ["Yellow Line"],
                "unverified_or_upcoming_route_short_names": ["Pink Line", "Blue Line"],
                "coverage_complete": False,
                "sample_feed_id": "bengaluru_bmrcl_metro_iudx_sample",
                "full_feed_id": "bengaluru_bmrcl_iudx_full_network_schedule",
            },
        )
        self.assertEqual(
            packet["catalogue_sample_availability"],
            [
                {
                    "dataset_id": "bmrcl-network",
                    "dataset_label": "BMRCL network",
                    "resource_count": 1,
                    "secure_resource_count": 1,
                    "public_sample_file_count": 1,
                    "empty_sample_file_count": 0,
                    "inline_sample_resource_count": 0,
                    "public_sample_files": [
                        {
                            "resource_id": "lines-id",
                            "resource_label": "Metro lines",
                            "name": "Lines sample",
                            "url": "https://example.test/lines.json",
                        }
                    ],
                },
                {
                    "dataset_id": "bmtc-dataset",
                    "dataset_label": "BMTC GTFS",
                    "resource_count": 5,
                    "secure_resource_count": 0,
                    "public_sample_file_count": 0,
                    "empty_sample_file_count": 0,
                    "inline_sample_resource_count": 0,
                    "public_sample_files": [],
                }
            ],
        )
        self.assertEqual(
            packet["gtfs_table_coverage"],
            [
                {
                    "dataset_id": "bmtc-dataset",
                    "dataset_label": "BMTC GTFS",
                    "required_tables_for_stop_sequence_geometry": [
                        "agency",
                        "calendar",
                        "routes",
                        "stops",
                        "trips",
                        "stop_times",
                    ],
                    "advertised_tables": ["agency", "calendar", "routes", "stops", "trips"],
                    "missing_required_tables": ["stop_times"],
                    "stop_sequence_geometry_ready": False,
                }
            ],
        )
        self.assertEqual(
            packet["gtfs_field_coverage"][0]["tables"][-1],
            {
                "table": "stop_times",
                "required_fields": [
                    "trip_id",
                    "arrival_time",
                    "departure_time",
                    "stop_id",
                    "stop_sequence",
                ],
                "advertised_fields": [],
                "missing_required_fields": [
                    "trip_id",
                    "arrival_time",
                    "departure_time",
                    "stop_id",
                    "stop_sequence",
                ],
            },
        )
        self.assertFalse(packet["gtfs_field_coverage"][0]["advertised_table_fields_ready"])
        self.assertEqual(
            packet["gtfs_resource_map"][0]["missing_gtfs_filenames"],
            ["stop_times.txt"],
        )
        self.assertEqual(
            [resource["gtfs_filename"] for resource in packet["gtfs_resource_map"][0]["resources"]],
            ["agency.txt", "calendar.txt", "routes.txt", "stops.txt", "trips.txt"],
        )
        self.assertEqual(
            packet["post_approval_build"]["bmtc_static_gtfs"]["outputs"]["gtfs_zip"],
            "data/cities/bengaluru/source/transit/gtfs/bengaluru_bmtc_iudx_full_gtfs.zip",
        )
        self.assertEqual(
            packet["post_approval_build"]["bmtc_static_gtfs"]["quality_gate"],
            {
                "route_geometry_ready": True,
                "trips_with_two_or_more_stops_gt": 0,
            },
        )
        self.assertEqual(
            packet["post_approval_readiness"][0]["remaining_gates"],
            ["policy_access", "stop_times_or_equivalent_stop_sequence"],
        )
        self.assertEqual(packet["next_action"], "submit_iudx_policy_request")
        self.assertNotIn("token", json.dumps(packet).lower())


if __name__ == "__main__":
    unittest.main()
