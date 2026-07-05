import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from sevent4.adapters.transit_filesystem import FileGtfsCorridorInputRepository
from sevent4.application.transit import (
    TransitFeedSpec,
    build_gtfs_corridors,
    build_multimodal_gtfs_layers,
    coastal_multimodal_feed_specs,
)
from sevent4.ports.transit import GtfsCorridorInput
from sevent4.transit.coverage_index import build_transit_coverage_index
from sevent4.transit.gtfs_corridors import build_corridors
from sevent4.transit.multimodal_layers import build_city_multimodal_layers, feed_run_specs_from_manifest
from sevent4.transit.multimodal_layers import _route_label, _stop_label
import scripts.recipes.transit.build_iudx_bus_sample_layers as iudx_bus_sample_recipe
from scripts.recipes.transit.build_iudx_bus_sample_layers import build_iudx_bus_sample_layers
import scripts.recipes.transit.build_iudx_bengaluru_metro_layers as iudx_bengaluru_metro_recipe
import scripts.recipes.transit.build_multimodal_gtfs_layers as multimodal_gtfs_recipe
import scripts.recipes.transit.build_cscl_chennai_suburban_rail as cscl_chennai_rail_recipe
import scripts.recipes.transit.build_constructed_metro_gtfs as constructed_metro_recipe
from scripts.recipes.transit.build_constructed_metro_gtfs import build_constructed_metro_gtfs
from scripts.recipes.transit.build_osm_metro_from_overpass import build_osm_metro_layers


class TransitPortsTest(unittest.TestCase):
    def test_gtfs_corridor_build_fails_loudly_without_shapes_or_stop_times(self) -> None:
        class Writer:
            def write_geojson(self, document) -> None:  # pragma: no cover - must not be reached
                raise AssertionError("writer should not run when the feed is unusable")

        inputs = GtfsCorridorInput(
            stops=[{"stop_id": "s1", "stop_lon": "72.1", "stop_lat": "23.1"}],
            routes=[{"route_id": "r1", "agency_id": "AMTS"}],
            trips=[{"route_id": "r1", "trip_id": "t1"}],
            shapes=[],
            stop_times=[],
        )
        with self.assertRaises(ValueError):
            build_gtfs_corridors(inputs, Writer())

    def test_gtfs_corridor_application_builds_geojson_without_file_io(self) -> None:
        class Writer:
            def __init__(self) -> None:
                self.document = None

            def write_geojson(self, document) -> None:
                self.document = document

        inputs = GtfsCorridorInput(
            stops=[
                {"stop_id": "s1", "stop_lon": "72.1", "stop_lat": "23.1"},
                {"stop_id": "s2", "stop_lon": "72.2", "stop_lat": "23.2"},
            ],
            routes=[
                {
                    "route_id": "r1",
                    "route_short_name": "1",
                    "route_long_name": "Main Road",
                    "agency_id": "AMTS",
                }
            ],
            trips=[{"route_id": "r1", "trip_id": "t1", "shape_id": "shape-a"}],
            shapes=[
                {"shape_id": "shape-a", "shape_pt_sequence": "2", "shape_pt_lon": "72.2", "shape_pt_lat": "23.2"},
                {"shape_id": "shape-a", "shape_pt_sequence": "1", "shape_pt_lon": "72.1", "shape_pt_lat": "23.1"},
            ],
            stop_times=[],
        )
        writer = Writer()

        result = build_gtfs_corridors(inputs, writer)

        self.assertEqual(writer.document, result.document)
        feature = result.document["features"][0]
        self.assertEqual(feature["properties"]["route_id"], "r1")
        self.assertEqual(feature["properties"]["agency_id"], "AMTS")
        self.assertEqual(feature["geometry"]["coordinates"], [[72.1, 23.1], [72.2, 23.2]])

    def test_multimodal_builder_writes_layers_and_missing_feed_provenance(self) -> None:
        inputs = GtfsCorridorInput(
            stops=[
                {"stop_id": "s1", "stop_name": "One", "stop_lon": "72.1", "stop_lat": "23.1"},
                {"stop_id": "s2", "stop_name": "Two", "stop_lon": "72.2", "stop_lat": "23.2"},
            ],
            routes=[
                {
                    "route_id": "r1",
                    "route_short_name": "1",
                    "route_long_name": "Main Road",
                    "agency_id": "BEST",
                    "route_type": "3",
                }
            ],
            trips=[{"route_id": "r1", "trip_id": "t1"}],
            shapes=[],
            stop_times=[
                {"trip_id": "t1", "stop_id": "s2", "stop_sequence": "2"},
                {"trip_id": "t1", "stop_id": "s1", "stop_sequence": "1"},
            ],
        )

        result = build_multimodal_gtfs_layers(
            [
                TransitFeedSpec(
                    feed_id="mumbai_best_bus",
                    city="mumbai",
                    mode="bus",
                    operator="BEST",
                    stop_layer="bus_stops",
                    route_layer="bus_routes",
                    source_url="https://example.invalid/best.zip",
                ),
                TransitFeedSpec(
                    feed_id="mumbai_suburban_rail",
                    city="mumbai",
                    mode="suburban_rail",
                    operator="Western Railway / Central Railway",
                    stop_layer="suburban_rail_stations",
                    route_layer="suburban_rail",
                    status="missing",
                    missing_reason="No local GTFS feed path configured.",
                ),
            ],
            {"mumbai_best_bus": inputs},
        )

        self.assertEqual(
            sorted(result.layers),
            ["bus_routes.geojson", "bus_stops.geojson"],
        )
        stop = result.layers["bus_stops.geojson"]["features"][0]
        self.assertEqual(stop["properties"]["mode"], "bus")
        self.assertEqual(stop["properties"]["operator"], "BEST")
        route = result.layers["bus_routes.geojson"]["features"][0]
        self.assertEqual(route["geometry"]["coordinates"], [[72.1, 23.1], [72.2, 23.2]])
        self.assertEqual(route["properties"]["source_feed_id"], "mumbai_best_bus")
        self.assertEqual(result.provenance["feeds"][0]["status"], "ok")
        self.assertEqual(result.provenance["feeds"][1]["status"], "missing")
        self.assertEqual(result.provenance["feeds"][1]["missing_reason"], "No local GTFS feed path configured.")

    def test_multimodal_cli_accepts_bengaluru_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            city_root = base / "cities"
            manifest = base / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "sevent4.multimodal_transit.manifest.v1",
                        "feeds": [
                            {
                                "feed_id": "bengaluru_bmrcl_iudx_full_network_schedule",
                                "city": "bengaluru",
                                "mode": "metro",
                                "operator": "Bangalore Metro Rail Corporation Limited",
                                "status": "gated",
                                "stop_layer": "metro_gtfs_stops",
                                "route_layer": "metro_gtfs_routes",
                                "missing_reason": "IUDX policy approval pending.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch("sys.argv", [
                "build_multimodal_gtfs_layers.py",
                "bengaluru",
                "--manifest",
                str(manifest),
                "--city-root",
                str(city_root),
            ]):
                multimodal_gtfs_recipe.main()

            sources = json.loads(
                (city_root / "bengaluru" / "source" / "transit" / "multimodal_transit.sources.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(sources["feeds"][0]["feed_id"], "bengaluru_bmrcl_iudx_full_network_schedule")

    def test_manifest_ok_status_is_runnable_as_available_feed(self) -> None:
        runs = feed_run_specs_from_manifest(
            {
                "feeds": [
                    {
                        "feed_id": "bengaluru_bmtc_iudx_full_gtfs",
                        "city": "bengaluru",
                        "mode": "bus",
                        "operator": "BMTC",
                        "status": "ok",
                        "path": "source/transit/gtfs/bengaluru_bmtc_iudx_full_gtfs.zip",
                        "stop_layer": "bus_stops",
                        "route_layer": "bus_routes",
                    }
                ]
            },
            "bengaluru",
        )

        self.assertEqual(runs[0].spec.status, "available")
        self.assertEqual(runs[0].spec.provenance_status, "ok")

    def test_transit_coverage_index_does_not_close_missing_rows_with_fallback_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            city_root = base / "data" / "cities"
            public_root = base / "public" / "cities"
            source = city_root / "metrocity" / "source" / "transit"
            layers = public_root / "metrocity" / "layers"
            source.mkdir(parents=True)
            layers.mkdir(parents=True)
            (layers / "metro_gtfs_stops.geojson").write_text('{"type":"FeatureCollection","features":[]}')
            (layers / "metro_gtfs_routes.geojson").write_text('{"type":"FeatureCollection","features":[]}')
            (source / "multimodal_transit.sources.json").write_text(
                json.dumps(
                    {
                        "schema": "sevent4.multimodal_transit.sources.v1",
                        "feeds": [
                            {
                                "feed_id": "official_metro",
                                "city": "metrocity",
                                "mode": "metro",
                                "operator": "Metro Rail",
                                "status": "missing",
                                "stop_layer": "metro_gtfs_stops.geojson",
                                "route_layer": "metro_gtfs_routes.geojson",
                                "stop_features": 0,
                                "route_features": 0,
                            },
                            {
                                "feed_id": "constructed_metro",
                                "city": "metrocity",
                                "mode": "metro",
                                "operator": "Metro Rail",
                                "status": "unofficial_constructed",
                                "stop_layer": "metro_gtfs_stops.geojson",
                                "route_layer": "metro_gtfs_routes.geojson",
                                "stop_features": 12,
                                "route_features": 1,
                            },
                            {
                                "feed_id": "inventory_mrts",
                                "city": "metrocity",
                                "mode": "mrts",
                                "operator": "Southern Railway",
                                "status": "official_inventory_fallback",
                                "stop_layer": "mrts_stations.geojson",
                                "route_layer": "mrts.geojson",
                                "stop_features": 2,
                                "route_features": 1,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (layers / "mrts_stations.geojson").write_text('{"type":"FeatureCollection","features":[]}')
            (layers / "mrts.geojson").write_text('{"type":"FeatureCollection","features":[]}')

            payload = build_transit_coverage_index(city_root, public_root, compiled="2026-07-04")

            feeds = {feed["feed_id"]: feed for feed in payload["cities"][0]["feeds"]}
            self.assertFalse(feeds["official_metro"]["public_coverage"])
            self.assertTrue(feeds["official_metro"]["public_layer_files"]["stop_layer_exists"])
            self.assertTrue(feeds["constructed_metro"]["public_coverage"])
            self.assertTrue(feeds["inventory_mrts"]["public_coverage"])

    def test_bengaluru_bmrcl_metro_layers_are_in_transit_coverage_index(self) -> None:
        payload = build_transit_coverage_index(
            Path("data/cities"),
            Path("public/cities"),
            compiled="2026-07-04",
        )

        bengaluru = next(city for city in payload["cities"] if city["city"] == "bengaluru")
        feeds = {feed["feed_id"]: feed for feed in bengaluru["feeds"]}

        self.assertIn("bengaluru_bmrcl_metro_iudx_sample", feeds)
        self.assertEqual(feeds["bengaluru_bmrcl_metro_iudx_sample"]["status"], "sample_public_constructed_gtfs")
        self.assertEqual(feeds["bengaluru_bmrcl_metro_iudx_sample"]["stop_features"], 45)
        self.assertEqual(feeds["bengaluru_bmrcl_metro_iudx_sample"]["route_features"], 2)
        self.assertTrue(feeds["bengaluru_bmrcl_metro_iudx_sample"]["public_coverage"])

    def test_bengaluru_bmrcl_iudx_sample_records_yellow_line_gap_in_coverage_index(self) -> None:
        payload = build_transit_coverage_index(
            Path("data/cities"),
            Path("public/cities"),
            compiled="2026-07-04",
        )

        bengaluru = next(city for city in payload["cities"] if city["city"] == "bengaluru")
        feeds = {feed["feed_id"]: feed for feed in bengaluru["feeds"]}
        scope = feeds["bengaluru_bmrcl_metro_iudx_sample"]["coverage_scope"]

        self.assertFalse(scope["coverage_complete"])
        self.assertEqual(scope["sample_route_short_names"], ["Purple Line", "Green Line"])
        self.assertEqual(scope["missing_operational_route_short_names"], ["Yellow Line"])
        self.assertEqual(scope["unverified_or_upcoming_route_short_names"], ["Pink Line", "Blue Line"])

    def test_bengaluru_full_bmrcl_iudx_gate_is_explicit_in_coverage_index(self) -> None:
        payload = build_transit_coverage_index(
            Path("data/cities"),
            Path("public/cities"),
            compiled="2026-07-04",
        )

        bengaluru = next(city for city in payload["cities"] if city["city"] == "bengaluru")
        feeds = {feed["feed_id"]: feed for feed in bengaluru["feeds"]}
        feed = feeds["bengaluru_bmrcl_iudx_full_network_schedule"]

        self.assertEqual(feed["status"], "gated")
        self.assertFalse(feed["public_coverage"])
        self.assertFalse(feed["coverage_scope"]["coverage_complete"])
        self.assertEqual(feed["coverage_scope"]["blocked_resource_ids"]["network_lines"], "e2c3b8a9-e03c-4045-9c80-66d463ca5cda")
        self.assertEqual(feed["coverage_scope"]["blocked_resource_ids"]["schedule"], "7da0557c-3e79-480f-b75e-44b0a933fbfb")
        self.assertIn("Yellow Line", feed["missing_reason"])

    def test_bengaluru_full_bmtc_iudx_gtfs_gate_is_explicit_in_coverage_index(self) -> None:
        payload = build_transit_coverage_index(
            Path("data/cities"),
            Path("public/cities"),
            compiled="2026-07-04",
        )

        bengaluru = next(city for city in payload["cities"] if city["city"] == "bengaluru")
        feeds = {feed["feed_id"]: feed for feed in bengaluru["feeds"]}

        self.assertIn("bengaluru_bmtc_iudx_full_gtfs", feeds)
        self.assertEqual(feeds["bengaluru_bmtc_iudx_full_gtfs"]["status"], "gated")
        self.assertIn("authorization.iudx.org.in", feeds["bengaluru_bmtc_iudx_full_gtfs"]["missing_reason"])
        self.assertIn("APD evaluation failed", feeds["bengaluru_bmtc_iudx_full_gtfs"]["missing_reason"])
        self.assertFalse(feeds["bengaluru_bmtc_iudx_full_gtfs"]["public_coverage"])

    def test_multimodal_builder_preserves_unofficial_constructed_status(self) -> None:
        inputs = GtfsCorridorInput(
            stops=[
                {"stop_id": "s1", "stop_name": "One", "stop_lon": "72.1", "stop_lat": "23.1"},
                {"stop_id": "s2", "stop_name": "Two", "stop_lon": "72.2", "stop_lat": "23.2"},
            ],
            routes=[{"route_id": "r1", "route_short_name": "M", "agency_id": "GMRC", "route_type": "1"}],
            trips=[{"route_id": "r1", "trip_id": "t1", "shape_id": "shape-a"}],
            shapes=[
                {"shape_id": "shape-a", "shape_pt_sequence": "1", "shape_pt_lon": "72.1", "shape_pt_lat": "23.1"},
                {"shape_id": "shape-a", "shape_pt_sequence": "2", "shape_pt_lon": "72.2", "shape_pt_lat": "23.2"},
            ],
            stop_times=[],
        )

        result = build_multimodal_gtfs_layers(
            [
                TransitFeedSpec(
                    feed_id="ahmedabad_gmrc_unofficial",
                    city="ahmedabad",
                    mode="metro",
                    operator="Gujarat Metro Rail Corporation",
                    stop_layer="metro_gtfs_stops",
                    route_layer="metro_gtfs_routes",
                    provenance_status="unofficial_constructed",
                    notes="Constructed from official timetable PDF.",
                )
            ],
            {"ahmedabad_gmrc_unofficial": inputs},
        )

        self.assertEqual(sorted(result.layers), ["metro_gtfs_routes.geojson", "metro_gtfs_stops.geojson"])
        self.assertEqual(result.provenance["feeds"][0]["status"], "unofficial_constructed")
        self.assertEqual(result.provenance["feeds"][0]["notes"], "Constructed from official timetable PDF.")

    def test_chennai_cscl_recipe_splits_mrts_layers_from_combined_suburban_inventory(self) -> None:
        station_fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"station_code": "MSB", "connections": "South Line; MRTS Line"},
                    "geometry": {"type": "Point", "coordinates": [80.1, 13.1]},
                },
                {
                    "type": "Feature",
                    "properties": {"station_code": "MCPT", "connections": "MRTS Line"},
                    "geometry": {"type": "Point", "coordinates": [80.2, 13.2]},
                },
                {
                    "type": "Feature",
                    "properties": {"station_code": "MS", "connections": "South Line"},
                    "geometry": {"type": "Point", "coordinates": [80.3, 13.3]},
                },
            ],
        }
        route_fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "MRTS Line", "mode": "mrts", "station_count": 2},
                    "geometry": {"type": "LineString", "coordinates": [[80.1, 13.1], [80.2, 13.2]]},
                },
                {
                    "type": "Feature",
                    "properties": {"name": "South Line", "mode": "suburban_rail", "station_count": 2},
                    "geometry": {"type": "LineString", "coordinates": [[80.1, 13.1], [80.3, 13.3]]},
                },
            ],
        }

        mrts_stations, mrts_routes = cscl_chennai_rail_recipe._split_mrts_layers(station_fc, route_fc)

        self.assertEqual([f["properties"]["station_code"] for f in mrts_stations["features"]], ["MSB", "MCPT"])
        self.assertEqual(len(mrts_routes["features"]), 1)
        self.assertEqual(mrts_routes["features"][0]["properties"]["mode"], "mrts")

    def test_multimodal_manifest_labels_osm_fallback_gtfs(self) -> None:
        spec = TransitFeedSpec(
            feed_id="kolkata_private_bus_osm",
            city="kolkata",
            mode="regulated_private_bus",
            operator="Kolkata regulated private bus network",
            stop_layer="regulated_private_bus_stops",
            route_layer="regulated_private_bus_routes",
            provenance_status="osm_fallback_constructed",
        )

        self.assertEqual(_stop_label(spec), "Regulated private bus stops (OSM fallback GTFS)")
        self.assertEqual(_route_label(spec), "Regulated private bus routes (OSM fallback GTFS)")

    def test_multimodal_builder_filters_by_gtfs_route_type(self) -> None:
        inputs = GtfsCorridorInput(
            stops=[
                {"stop_id": "bus-a", "stop_name": "Bus A", "stop_lon": "76.1", "stop_lat": "10.1"},
                {"stop_id": "bus-b", "stop_name": "Bus B", "stop_lon": "76.2", "stop_lat": "10.2"},
                {"stop_id": "ferry-a", "stop_name": "Ferry A", "stop_lon": "76.3", "stop_lat": "10.3"},
                {"stop_id": "ferry-b", "stop_name": "Ferry B", "stop_lon": "76.4", "stop_lat": "10.4"},
            ],
            routes=[
                {"route_id": "bus", "route_short_name": "B", "agency_id": "KB", "route_type": "3"},
                {"route_id": "ferry", "route_short_name": "F", "agency_id": "KW", "route_type": "4"},
            ],
            trips=[
                {"route_id": "bus", "trip_id": "bus-trip"},
                {"route_id": "ferry", "trip_id": "ferry-trip"},
            ],
            shapes=[],
            stop_times=[
                {"trip_id": "bus-trip", "stop_id": "bus-a", "stop_sequence": "1"},
                {"trip_id": "bus-trip", "stop_id": "bus-b", "stop_sequence": "2"},
                {"trip_id": "ferry-trip", "stop_id": "ferry-a", "stop_sequence": "1"},
                {"trip_id": "ferry-trip", "stop_id": "ferry-b", "stop_sequence": "2"},
            ],
        )

        result = build_multimodal_gtfs_layers(
            [
                TransitFeedSpec(
                    feed_id="kochi_bus",
                    city="kochi",
                    mode="bus",
                    operator="Kochi buses",
                    stop_layer="bus_stops",
                    route_layer="bus_routes",
                    route_types=("3",),
                ),
                TransitFeedSpec(
                    feed_id="kochi_ferry",
                    city="kochi",
                    mode="ferry",
                    operator="Kochi water transport",
                    stop_layer="ferry_stops",
                    route_layer="ferry_routes",
                    route_types=("4",),
                ),
            ],
            {"kochi_bus": inputs, "kochi_ferry": inputs},
        )

        self.assertEqual(len(result.layers["bus_routes.geojson"]["features"]), 1)
        self.assertEqual(len(result.layers["ferry_routes.geojson"]["features"]), 1)
        self.assertEqual(
            {feature["properties"]["stop_id"] for feature in result.layers["bus_stops.geojson"]["features"]},
            {"bus-a", "bus-b"},
        )
        self.assertEqual(
            {feature["properties"]["stop_id"] for feature in result.layers["ferry_stops.geojson"]["features"]},
            {"ferry-a", "ferry-b"},
        )
        self.assertEqual(result.layers["ferry_routes.geojson"]["features"][0]["properties"]["mode"], "ferry")

    def test_multimodal_builder_filters_by_bbox(self) -> None:
        inputs = GtfsCorridorInput(
            stops=[
                {"stop_id": "in-a", "stop_name": "Inside A", "stop_lon": "83.2", "stop_lat": "17.7"},
                {"stop_id": "in-b", "stop_name": "Inside B", "stop_lon": "83.3", "stop_lat": "17.8"},
                {"stop_id": "out-a", "stop_name": "Outside A", "stop_lon": "80.1", "stop_lat": "16.1"},
                {"stop_id": "out-b", "stop_name": "Outside B", "stop_lon": "80.2", "stop_lat": "16.2"},
            ],
            routes=[
                {"route_id": "city", "route_short_name": "C", "route_type": "3"},
                {"route_id": "outside", "route_short_name": "O", "route_type": "3"},
            ],
            trips=[
                {"route_id": "city", "trip_id": "city-trip"},
                {"route_id": "outside", "trip_id": "outside-trip"},
            ],
            shapes=[],
            stop_times=[
                {"trip_id": "city-trip", "stop_id": "in-a", "stop_sequence": "1"},
                {"trip_id": "city-trip", "stop_id": "in-b", "stop_sequence": "2"},
                {"trip_id": "outside-trip", "stop_id": "out-a", "stop_sequence": "1"},
                {"trip_id": "outside-trip", "stop_id": "out-b", "stop_sequence": "2"},
            ],
        )

        result = build_multimodal_gtfs_layers(
            [
                TransitFeedSpec(
                    feed_id="apsrtc_vizag",
                    city="visakhapatnam",
                    mode="bus",
                    operator="APSRTC",
                    stop_layer="bus_stops",
                    route_layer="bus_routes",
                    route_types=("3",),
                    bbox=(83.0, 17.5, 83.5, 18.0),
                )
            ],
            {"apsrtc_vizag": inputs},
        )

        self.assertEqual(len(result.layers["bus_routes.geojson"]["features"]), 1)
        self.assertEqual(
            {feature["properties"]["stop_id"] for feature in result.layers["bus_stops.geojson"]["features"]},
            {"in-a", "in-b"},
        )
        self.assertEqual(result.provenance["feeds"][0]["bbox"], [83.0, 17.5, 83.5, 18.0])

    def test_coastal_multimodal_specs_cover_issue_107_modes(self) -> None:
        specs = coastal_multimodal_feed_specs()
        by_city_mode = {(spec.city, spec.mode, spec.feed_id) for spec in specs}

        self.assertIn(("chennai", "suburban_rail", "chennai_southern_rail_suburban"), by_city_mode)
        self.assertIn(("chennai", "mrts", "chennai_mrts"), by_city_mode)
        self.assertIn(("chennai", "bus", "chennai_mtc_bus"), by_city_mode)
        self.assertIn(("kolkata", "suburban_rail", "kolkata_eastern_se_suburban"), by_city_mode)
        self.assertIn(("kolkata", "metro", "kolkata_metro"), by_city_mode)
        self.assertIn(("kolkata", "bus", "kolkata_wbtc_bus"), by_city_mode)
        self.assertIn(("kolkata", "regulated_private_bus", "kolkata_regulated_private_bus"), by_city_mode)
        self.assertIn(("mumbai", "suburban_rail", "mumbai_western_central_suburban"), by_city_mode)
        self.assertIn(("mumbai", "bus", "mumbai_best_bus"), by_city_mode)
        self.assertIn(("mumbai", "metro", "mumbai_metro"), by_city_mode)

    def test_build_corridors_cli_boundary_uses_file_adapter_and_writes_geojson(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            gtfs_dir = _write_gtfs_fixture(base)
            out = base / "out" / "corridors.geojson"

            build_corridors(gtfs_dir, out)

            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["type"], "FeatureCollection")
            self.assertEqual(len(data["features"]), 1)
            self.assertEqual(data["features"][0]["properties"]["route_short_name"], "1")
            self.assertEqual(data["features"][0]["geometry"]["coordinates"], [[72.1, 23.1], [72.2, 23.2]])

    def test_iudx_bus_sample_builder_writes_stop_route_layers_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            layers = base / "layers"
            source = base / "source"
            layers.mkdir()
            (layers / "layer_manifest.json").write_text(json.dumps({"layers": []}), encoding="utf-8")
            stops = base / "stops.json"
            routes = base / "routes.json"
            resources = base / "resources.json"
            stops.write_text(
                json.dumps(
                    [
                        {
                            "id": "stop-resource",
                            "stop_id": "s1",
                            "stop_name": "Central",
                            "location": {"type": "Point", "coordinates": [85.84, 20.26]},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            routes.write_text(
                json.dumps(
                    [
                        {
                            "id": "route-resource",
                            "route_id": "r1",
                            "route_long_name": "Central to East",
                            "location": {
                                "type": "LineString",
                                "coordinates": [[85.84, 20.26], [85.85, 20.27]],
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )
            resources.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "id": "stop-resource",
                                "label": "Bus Stop Info",
                                "accessPolicy": "SECURE",
                                "resourceType": "GSLAYER",
                            },
                            {
                                "id": "route-resource",
                                "label": "Bus Route Info",
                                "accessPolicy": "SECURE",
                                "resourceType": "GSLAYER",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = build_iudx_bus_sample_layers(
                city="bhubaneswar",
                operator="CRUT",
                dataset_id="dataset-1",
                stops_json=stops,
                routes_json=routes,
                resources_json=resources,
                out_dir=layers,
                source_dir=source,
            )

            self.assertEqual(result["stop_features"], 1)
            self.assertEqual(result["route_features"], 1)
            stop_layer = json.loads((layers / "bus_stops.geojson").read_text(encoding="utf-8"))
            route_layer = json.loads((layers / "bus_routes.geojson").read_text(encoding="utf-8"))
            manifest = json.loads((layers / "layer_manifest.json").read_text(encoding="utf-8"))
            sources = json.loads((source / "iudx_bus_sample.sources.json").read_text(encoding="utf-8"))
            self.assertEqual(stop_layer["features"][0]["properties"]["operator"], "CRUT")
            self.assertEqual(stop_layer["features"][0]["properties"]["source_dataset_id"], "dataset-1")
            self.assertEqual(route_layer["features"][0]["geometry"]["coordinates"], [[85.84, 20.26], [85.85, 20.27]])
            self.assertEqual([layer["id"] for layer in manifest["layers"]], ["bus_stops", "bus_routes"])
            self.assertEqual(sources["feeds"][0]["status"], "sample_public")

    def test_iudx_bus_sample_builder_writes_static_gtfs_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            stops = base / "stops.json"
            routes = base / "routes.json"
            out_zip = base / "sample_gtfs.zip"
            source = base / "sample_gtfs.sources.json"
            stops.write_text(
                json.dumps(
                    [
                        {
                            "stop_id": "s1",
                            "stop_name": "Central",
                            "location": {"type": "Point", "coordinates": [85.84, 20.26]},
                        },
                        {
                            "stop_id": "s2",
                            "stop_name": "East",
                            "location": {"type": "Point", "coordinates": [85.85, 20.27]},
                        },
                    ]
                ),
                encoding="utf-8",
            )
            routes.write_text(
                json.dumps(
                    [
                        {
                            "route_id": "r1",
                            "route_long_name": "Central to East",
                            "routeStopSequence": ["s1", "s2"],
                            "location": {
                                "type": "LineString",
                                "coordinates": [[85.84, 20.26], [85.85, 20.27]],
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )

            self.assertTrue(hasattr(iudx_bus_sample_recipe, "build_iudx_bus_sample_gtfs"))
            result = iudx_bus_sample_recipe.build_iudx_bus_sample_gtfs(
                city="bhubaneswar",
                operator="CRUT",
                dataset_id="dataset-1",
                agency_url="https://example.test/crut",
                stops_json=stops,
                routes_json=routes,
                out_zip=out_zip,
                provenance_path=source,
                generated_at="2026-07-04T00:00:00Z",
            )

            self.assertEqual(result["stops"], 2)
            self.assertEqual(result["routes"], 1)
            self.assertEqual(result["stop_times"], 4)
            with zipfile.ZipFile(out_zip) as zf:
                self.assertIn("stops.txt", zf.namelist())
                self.assertIn("stop_times.txt", zf.namelist())
                self.assertIn("frequencies.txt", zf.namelist())
                self.assertIn("r1", zf.read("routes.txt").decode("utf-8"))
            source_doc = json.loads(source.read_text(encoding="utf-8"))
            self.assertEqual(source_doc["status"], "sample_public_constructed_gtfs")
            self.assertEqual(source_doc["counts"]["stops"], 2)

    def test_bengaluru_iudx_metro_sample_builder_writes_static_gtfs_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            stations = base / "stations.json"
            lines = base / "lines.json"
            out_zip = base / "bmrcl_sample_gtfs.zip"
            provenance = base / "bmrcl_sample_gtfs.sources.json"
            stations.write_text(
                json.dumps(
                    [
                        {
                            "stop_code": "A",
                            "stop_name": "Alpha",
                            "location": {"type": "Point", "coordinates": [77.1, 12.1]},
                        },
                        {
                            "stop_code": "B",
                            "stop_name": "Beta",
                            "location": {"type": "Point", "coordinates": [77.2, 12.2]},
                        },
                    ]
                ),
                encoding="utf-8",
            )
            lines.write_text(
                json.dumps(
                    [
                        {
                            "route_id": "Line 1",
                            "route_short_name": "Purple Line",
                            "route_long_name": "Alpha to Beta",
                            "routeStopSequence": ["A", "B"],
                            "location": {"type": "LineString", "coordinates": [[77.1, 12.1], [77.2, 12.2]]},
                        }
                    ]
                ),
                encoding="utf-8",
            )

            self.assertTrue(hasattr(iudx_bengaluru_metro_recipe, "build_bmrcl_sample_gtfs"))
            result = iudx_bengaluru_metro_recipe.build_bmrcl_sample_gtfs(
                stations_json=stations,
                lines_json=lines,
                out_zip=out_zip,
                provenance_path=provenance,
                generated_at="2026-07-04T00:00:00Z",
            )

            self.assertEqual(result["stops"], 2)
            self.assertEqual(result["routes"], 1)
            self.assertEqual(result["stop_times"], 4)
            with zipfile.ZipFile(out_zip) as zf:
                self.assertEqual(
                    {
                        "agency.txt",
                        "stops.txt",
                        "routes.txt",
                        "trips.txt",
                        "stop_times.txt",
                        "calendar.txt",
                        "frequencies.txt",
                        "shapes.txt",
                        "feed_info.txt",
                    },
                    set(zf.namelist()),
                )
                self.assertIn("Purple Line", zf.read("routes.txt").decode("utf-8"))
                self.assertIn("Alpha", zf.read("stops.txt").decode("utf-8"))
            source_doc = json.loads(provenance.read_text(encoding="utf-8"))
            self.assertEqual(source_doc["status"], "sample_public_constructed_gtfs")
            self.assertEqual(source_doc["source_dataset_id"], "6c5df87a-38d6-4136-aadb-b3b55842d985")

    def test_bengaluru_iudx_metro_cli_writes_layers_sources_and_sample_gtfs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            stations = base / "stations.json"
            lines = base / "lines.json"
            network = base / "network.json"
            operations = base / "operations.json"
            bmtc = base / "bmtc.json"
            layers = base / "layers"
            source = base / "source"
            out_zip = base / "gtfs" / "bmrcl.zip"
            provenance = source / "bmrcl_sample_gtfs.sources.json"
            layers.mkdir()
            (layers / "layer_manifest.json").write_text(json.dumps({"layers": []}), encoding="utf-8")
            stations.write_text(
                json.dumps(
                    [
                        {
                            "stop_code": "A",
                            "stop_name": "Alpha",
                            "location": {"type": "Point", "coordinates": [77.1, 12.1]},
                        },
                        {
                            "stop_code": "B",
                            "stop_name": "Beta",
                            "location": {"type": "Point", "coordinates": [77.2, 12.2]},
                        },
                    ]
                ),
                encoding="utf-8",
            )
            lines.write_text(
                json.dumps(
                    [
                        {
                            "route_id": "Line 1",
                            "route_short_name": "Purple Line",
                            "route_long_name": "Alpha to Beta",
                            "routeStopSequence": ["A", "B"],
                            "location": {"type": "LineString", "coordinates": [[77.1, 12.1], [77.2, 12.2]]},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            for path, dataset_id in ((network, "network-1"), (operations, "operations-1"), (bmtc, "bmtc-1")):
                path.write_text(
                    json.dumps(
                        {
                            "results": [
                                {
                                    "dataset": {
                                        "id": dataset_id,
                                        "label": dataset_id,
                                        "description": "",
                                        "totalResources": 0,
                                        "provider": {},
                                    },
                                    "resource": [],
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )

            with patch(
                "sys.argv",
                [
                    "build_iudx_bengaluru_metro_layers.py",
                    "--stations-json",
                    str(stations),
                    "--lines-json",
                    str(lines),
                    "--bmrcl-network-detail",
                    str(network),
                    "--bmrcl-operations-detail",
                    str(operations),
                    "--bmtc-detail",
                    str(bmtc),
                    "--out-dir",
                    str(layers),
                    "--source-dir",
                    str(source),
                    "--gtfs-zip",
                    str(out_zip),
                    "--gtfs-provenance",
                    str(provenance),
                    "--generated-at",
                    "2026-07-04T00:00:00Z",
                ],
            ):
                iudx_bengaluru_metro_recipe.main()

            sources = json.loads((source / "iudx_bengaluru_transit.sources.json").read_text(encoding="utf-8"))
            self.assertTrue(out_zip.exists())
            self.assertEqual(sources["constructed_gtfs"]["local"], str(out_zip))
            self.assertEqual(sources["constructed_gtfs"]["counts"]["stop_times"], 4)
            self.assertIn("authorization.iudx.org.in", sources["access_note"])

    def test_osm_metro_builder_writes_fallback_layers_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            layers = base / "layers"
            source = base / "source"
            layers.mkdir()
            (layers / "layer_manifest.json").write_text(json.dumps({"layers": []}), encoding="utf-8")
            lines = base / "metro_lines_overpass.json"
            stations = base / "metro_stations_overpass.json"
            lines.write_text(
                json.dumps(
                    {
                        "elements": [
                            {
                                "type": "way",
                                "id": 1,
                                "tags": {"name": "Red Line", "operator": "Metro Corp"},
                                "geometry": [{"lon": 80.1, "lat": 26.1}, {"lon": 80.2, "lat": 26.2}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            stations.write_text(
                json.dumps(
                    {
                        "elements": [
                            {
                                "type": "node",
                                "id": 2,
                                "lat": 26.1,
                                "lon": 80.1,
                                "tags": {
                                    "name": "Central",
                                    "operator": "Metro Corp",
                                    "railway": "stop",
                                    "subway": "yes",
                                },
                            },
                            {
                                "type": "node",
                                "id": 3,
                                "lat": 26.1001,
                                "lon": 80.1001,
                                "tags": {
                                    "name": "Central",
                                    "operator": "Metro Corp",
                                    "railway": "station",
                                    "station": "subway",
                                    "subway": "yes",
                                },
                            },
                            {
                                "type": "node",
                                "id": 4,
                                "lat": 26.2,
                                "lon": 80.2,
                                "tags": {
                                    "construction": "station",
                                    "name": "Future Central",
                                    "operator": "Metro Corp",
                                    "railway": "construction",
                                    "station": "subway",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = build_osm_metro_layers(
                city="kanpur",
                lines_json=lines,
                stations_json=stations,
                out_dir=layers,
                source_dir=source,
                bbox="26.0,80.0,26.3,80.3",
            )

            self.assertEqual(result["line_features"], 1)
            self.assertEqual(result["station_features"], 1)
            line_layer = json.loads((layers / "metro_lines.geojson").read_text(encoding="utf-8"))
            station_layer = json.loads((layers / "metro.geojson").read_text(encoding="utf-8"))
            manifest = json.loads((layers / "layer_manifest.json").read_text(encoding="utf-8"))
            sources = json.loads((source / "osm_metro.sources.json").read_text(encoding="utf-8"))
            self.assertEqual(line_layer["features"][0]["properties"]["source"], "OpenStreetMap (fallback)")
            self.assertEqual(station_layer["features"][0]["properties"]["mode"], "metro")
            self.assertEqual(station_layer["features"][0]["properties"]["source_node_id"], "3")
            self.assertEqual([layer["id"] for layer in manifest["layers"]], ["metro_lines", "metro"])
            self.assertEqual(sources["status"], "fallback_osm")

    def test_constructed_metro_gtfs_writes_unofficial_zip_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            stations = base / "stations.geojson"
            out_zip = base / "constructed.zip"
            sources = base / "constructed.sources.json"
            stations.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": {"type": "Point", "coordinates": [72.1, 23.1]},
                                "properties": {"name": "One"},
                            },
                            {
                                "type": "Feature",
                                "geometry": {"type": "Point", "coordinates": [72.2, 23.2]},
                                "properties": {"name": "Two"},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = build_constructed_metro_gtfs(
                agency_id="TEST",
                agency_name="Test Metro",
                agency_url="https://example.test/",
                station_geojson=stations,
                routes=[
                    {
                        "route_id": "line_1",
                        "short_name": "L1",
                        "long_name": "Line 1",
                        "stops": ["One", "Two"],
                        "frequencies": [{"start_time": "06:00:00", "end_time": "22:00:00", "headway_secs": 600}],
                    }
                ],
                out_zip=out_zip,
                provenance_path=sources,
                source_urls=["https://example.test/timetable.pdf"],
                generated_at="2026-07-03T00:00:00Z",
            )

            self.assertEqual(result["stops"], 2)
            self.assertEqual(result["routes"], 1)
            self.assertEqual(result["trips"], 2)
            with zipfile.ZipFile(out_zip) as zf:
                names = set(zf.namelist())
                self.assertIn("agency.txt", names)
                self.assertIn("frequencies.txt", names)
                self.assertIn("feed_info.txt", names)
                stops_text = zf.read("stops.txt").decode("utf-8")
                self.assertIn("TEST_one", stops_text)
            source_doc = json.loads(sources.read_text(encoding="utf-8"))
            self.assertEqual(source_doc["status"], "unofficial_constructed")
            self.assertEqual(source_doc["source_urls"], ["https://example.test/timetable.pdf"])

    def test_mumbai_constructed_metro_recipe_tracks_operational_lines_only(self) -> None:
        routes = {route["route_id"]: route for route in constructed_metro_recipe.MUMBAI_METRO_ROUTES}

        self.assertIn("mumbai_yellow_2b_phase_1", routes)
        self.assertEqual(routes["mumbai_yellow_2b_phase_1"]["stops"], ["Mandale", "Mankhurd", "BSNL", "Shivaji Chowk", "Diamond Garden"])
        self.assertNotIn("mumbai_magenta_14", routes)

    def test_wbtc_city_bus_recipe_writes_constructed_gtfs_from_route_table(self) -> None:
        import scripts.recipes.transit.build_wbtc_city_bus_gtfs as wbtc_bus_recipe

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source_html = base / "wbtc.html"
            osm_stops = base / "bus_stops.geojson"
            out_zip = base / "wbtc.zip"
            provenance = base / "wbtc.sources.json"
            source_html.write_text(
                """
                <table><tbody>
                <tr><th>Sl. No.</th><th>Route No.</th><th>Originating Point</th><th>Terminating Point</th><th>Stoppage</th></tr>
                <tr><td>1</td><td>A-1</td><td>Alpha</td><td>Gamma</td><td>Alpha-Beta-Gamma</td></tr>
                <tr><td>2</td><td>B-1</td><td>Unmatched</td><td>Nowhere</td><td>Unmatched-Nowhere</td></tr>
                </tbody></table>
                """,
                encoding="utf-8",
            )
            osm_stops.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {"type": "Feature", "properties": {"name": "Alpha"}, "geometry": {"type": "Point", "coordinates": [88.1, 22.1]}},
                            {"type": "Feature", "properties": {"name": "Beta"}, "geometry": {"type": "Point", "coordinates": [88.2, 22.2]}},
                            {"type": "Feature", "properties": {"name": "Gamma"}, "geometry": {"type": "Point", "coordinates": [88.3, 22.3]}},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = wbtc_bus_recipe.build_wbtc_city_bus_gtfs(
                source_html=source_html,
                osm_stops=osm_stops,
                out_zip=out_zip,
                provenance_path=provenance,
                generated_at="2026-07-04T00:00:00Z",
                source_url="https://wbtconline.in/wbtc-city-bus-routes",
            )

            self.assertEqual(result["routes"], 1)
            self.assertEqual(result["stops"], 3)
            self.assertEqual(result["skipped_routes"], 1)
            with zipfile.ZipFile(out_zip) as zf:
                self.assertIn("routes.txt", zf.namelist())
                self.assertIn("frequencies.txt", zf.namelist())
                self.assertIn("A-1", zf.read("routes.txt").decode("utf-8"))
                self.assertEqual(len(zf.read("stop_times.txt").decode("utf-8").strip().splitlines()), 7)
            source_doc = json.loads(provenance.read_text(encoding="utf-8"))
            self.assertEqual(source_doc["status"], "unofficial_constructed")
            self.assertEqual(source_doc["counts"]["routes"], 1)
            self.assertEqual(source_doc["counts"]["skipped_routes"], 1)

    def test_kolkata_wbtc_recipe_uses_source_backed_anchor_points_to_recover_route_rows(self) -> None:
        import scripts.recipes.transit.build_wbtc_city_bus_gtfs as wbtc_bus_recipe

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            out_zip = base / "wbtc.zip"
            provenance = base / "wbtc.sources.json"

            result = wbtc_bus_recipe.build_wbtc_city_bus_gtfs(
                source_html=Path("data/cities/kolkata/source/transit/wbtc/wbtc_city_bus_routes_20260704.html"),
                osm_stops=Path("data/cities/kolkata/source/osm/bus_stops.geojson"),
                anchor_points=[
                    Path("public/cities/kolkata/layers/regulated_private_bus_stops.geojson"),
                    Path("data/cities/kolkata/source/osm/metro_stations.geojson"),
                    Path("public/cities/kolkata/layers/suburban_rail_stations.geojson"),
                    Path("public/cities/kolkata/layers/suburban_rail_gtfs_stations.geojson"),
                ],
                out_zip=out_zip,
                provenance_path=provenance,
                generated_at="2026-07-04T00:00:00Z",
                source_url="https://wbtconline.in/wbtc-city-bus-routes",
            )

            self.assertEqual(result["source_routes"], 131)
            self.assertGreaterEqual(result["routes"], 120)
            self.assertLessEqual(result["skipped_routes"], 11)
            source_doc = json.loads(provenance.read_text(encoding="utf-8"))
            self.assertEqual(source_doc["counts"]["routes"], result["routes"])
            self.assertEqual(len(source_doc["anchor_points"]), 4)

    def test_bmtc_endpoint_recipe_writes_routes_from_gtfs_route_names(self) -> None:
        import scripts.recipes.transit.build_bmtc_endpoint_gtfs as bmtc_endpoint_recipe

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source_zip = base / "bmtc.zip"
            out_zip = base / "bmtc_endpoint.zip"
            provenance = base / "bmtc_endpoint.sources.json"
            with zipfile.ZipFile(source_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    "agency.txt",
                    "agency_id,agency_name,agency_url,agency_timezone\n"
                    "BMTC,Bangalore Metropolitan Transport Corporation,https://mybmtc.karnataka.gov.in/,Asia/Kolkata\n",
                )
                zf.writestr(
                    "stops.txt",
                    "stop_id,stop_name,stop_lat,stop_lon\n"
                    "s1,Kempegowda Bus Station,12.9781,77.5723\n"
                    "s2,Sarjapura Bus Stand,12.8600,77.7850\n"
                    "s3,Loop Stand,12.9000,77.6000\n",
                )
                zf.writestr(
                    "routes.txt",
                    "route_id,agency_id,route_short_name,route_long_name,route_type\n"
                    "327K,BMTC,BR1646,Kempegowda Bus Station - Sarjapura Bus Stand,3\n"
                    "4,BMTC,BR4,Loop Stand - Loop Stand,3\n"
                    "9,BMTC,BR9,Missing - Nowhere,3\n",
                )
                zf.writestr("trips.txt", "route_id,service_id,trip_id\n327K,daily,t1\n")
                zf.writestr("stop_times.txt", "trip_id,arrival_time,departure_time,stop_id,stop_sequence\nt1,08:00:00,08:00:00,s1,1\n")
                zf.writestr(
                    "calendar.txt",
                    "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
                    "daily,1,1,1,1,1,1,1,20260704,20271231\n",
                )

            result = bmtc_endpoint_recipe.build_bmtc_endpoint_gtfs(
                source_zip=source_zip,
                out_zip=out_zip,
                provenance_path=provenance,
                generated_at="2026-07-04T00:00:00Z",
                source_url="https://example.test/bmtc.zip",
            )

            self.assertEqual(result["routes"], 1)
            self.assertEqual(result["stops"], 2)
            self.assertEqual(result["skipped_routes"], 2)
            with zipfile.ZipFile(out_zip) as zf:
                self.assertIn("shapes.txt", zf.namelist())
                routes_text = zf.read("routes.txt").decode("utf-8")
                self.assertIn("327K", routes_text)
                self.assertNotIn("BR1646", routes_text)
                self.assertEqual(len(zf.read("stop_times.txt").decode("utf-8").strip().splitlines()), 5)
            source_doc = json.loads(provenance.read_text(encoding="utf-8"))
            self.assertEqual(source_doc["status"], "unofficial_constructed")
            self.assertEqual(source_doc["counts"]["source_routes"], 3)
            self.assertEqual(source_doc["counts"]["skipped_routes"], 2)

    def test_osm_private_bus_recipe_writes_gtfs_from_route_relations(self) -> None:
        import scripts.recipes.transit.build_osm_bus_route_gtfs as osm_bus_recipe

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            overpass = base / "bus_routes.json"
            out_zip = base / "private_bus.zip"
            provenance = base / "private_bus.sources.json"
            overpass.write_text(
                json.dumps(
                    {
                        "elements": [
                            {"type": "node", "id": 1, "lat": 22.1, "lon": 88.1},
                            {"type": "node", "id": 2, "lat": 22.2, "lon": 88.2},
                            {"type": "node", "id": 3, "lat": 22.3, "lon": 88.3},
                            {"type": "way", "id": 10, "nodes": [1, 2]},
                            {"type": "way", "id": 11, "nodes": [2, 3]},
                            {
                                "type": "relation",
                                "id": 100,
                                "tags": {
                                    "type": "route",
                                    "route": "bus",
                                    "network": "Kolkata Private Bus",
                                    "ref": "12C",
                                    "from": "Pailan",
                                    "to": "Howrah Station",
                                    "name": "Bus 12C: Pailan - Howrah Station",
                                },
                                "members": [
                                    {"type": "way", "ref": 10, "role": ""},
                                    {"type": "way", "ref": 11, "role": ""},
                                ],
                            },
                            {
                                "type": "relation",
                                "id": 200,
                                "tags": {"type": "route", "route": "bus", "network": "WBSTC", "ref": "V1"},
                                "members": [{"type": "way", "ref": 10, "role": ""}],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = osm_bus_recipe.build_osm_bus_route_gtfs(
                source_json=overpass,
                out_zip=out_zip,
                provenance_path=provenance,
                feed_id="kolkata_private_bus_osm",
                agency_id="KPB",
                agency_name="Kolkata regulated private bus network",
                network="Kolkata Private Bus",
                generated_at="2026-07-04T00:00:00Z",
                source_url="https://overpass-api.de/",
                provenance_status="osm_fallback_constructed",
            )

            self.assertEqual(result["source_routes"], 1)
            self.assertEqual(result["routes"], 1)
            self.assertEqual(result["stops"], 2)
            self.assertEqual(result["shape_points"], 3)
            with zipfile.ZipFile(out_zip) as zf:
                routes_text = zf.read("routes.txt").decode("utf-8")
                self.assertIn("12C", routes_text)
                self.assertNotIn("V1", routes_text)
                self.assertEqual(len(zf.read("stop_times.txt").decode("utf-8").strip().splitlines()), 5)
            source_doc = json.loads(provenance.read_text(encoding="utf-8"))
            self.assertEqual(source_doc["status"], "osm_fallback_constructed")
            self.assertEqual(source_doc["network"], "Kolkata Private Bus")

    def test_osm_bus_recipe_can_filter_by_operator_when_network_is_blank(self) -> None:
        import scripts.recipes.transit.build_osm_bus_route_gtfs as osm_bus_recipe

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            overpass = base / "bus_routes.json"
            out_zip = base / "jaipur_bus.zip"
            provenance = base / "jaipur_bus.sources.json"
            overpass.write_text(
                json.dumps(
                    {
                        "elements": [
                            {"type": "node", "id": 1, "lat": 26.1, "lon": 75.1},
                            {"type": "node", "id": 2, "lat": 26.2, "lon": 75.2},
                            {"type": "node", "id": 3, "lat": 26.3, "lon": 75.3},
                            {"type": "way", "id": 10, "nodes": [1, 2, 3]},
                            {
                                "type": "relation",
                                "id": 100,
                                "tags": {
                                    "type": "route",
                                    "route": "bus",
                                    "operator": "JCTSL",
                                    "ref": "7",
                                    "from": "Khirni Phatak",
                                    "to": "Transport Nagar",
                                },
                                "members": [{"type": "way", "ref": 10, "role": ""}],
                            },
                            {
                                "type": "relation",
                                "id": 200,
                                "tags": {
                                    "type": "route",
                                    "route": "bus",
                                    "operator": "RSRTC",
                                    "ref": "EXP",
                                    "from": "Jaipur",
                                    "to": "Bharatpur",
                                },
                                "members": [{"type": "way", "ref": 10, "role": ""}],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = osm_bus_recipe.build_osm_bus_route_gtfs(
                source_json=overpass,
                out_zip=out_zip,
                provenance_path=provenance,
                feed_id="jaipur_jctsl_osm",
                agency_id="JCTSL",
                agency_name="Jaipur City Transport Services Limited",
                network="",
                operator="JCTSL",
                generated_at="2026-07-04T00:00:00Z",
                source_url="https://overpass-api.de/",
                provenance_status="osm_fallback_constructed",
            )

            self.assertEqual(result["source_routes"], 1)
            with zipfile.ZipFile(out_zip) as zf:
                routes_text = zf.read("routes.txt").decode("utf-8")
                self.assertIn("7", routes_text)
                self.assertNotIn("EXP", routes_text)
            source_doc = json.loads(provenance.read_text(encoding="utf-8"))
            self.assertEqual(source_doc["operator_filter"], "JCTSL")

    def test_constructed_metro_recipe_covers_osm_fallback_metro_cities(self) -> None:
        for city, builder_name, station_names in [
            (
                "jaipur",
                "build_jaipur_metro_unofficial_gtfs",
                [
                    "Manasarovar",
                    "New Aatish Market",
                    "Vivek Vihar",
                    "Shyam Nagar",
                    "Ram Nagar",
                    "Civil Lines",
                    "Railway Station",
                    "Sindhi Camp",
                    "Chandpole",
                    "Choti Chaupar",
                    "Badi Chaupar",
                ],
            ),
            (
                "kanpur",
                "build_kanpur_metro_unofficial_gtfs",
                [
                    "IIT Kanpur",
                    "Kalyanpur",
                    "SPM Hospital",
                    "Vishwavidyalaya",
                    "Gurudev Chauraha",
                    "Geeta Nagar",
                    "Rawatpur",
                    "LLR Hospital",
                    "Moti Jheel",
                    "Chunniganj",
                    "Naveen Market",
                    "Bada Chauraha",
                    "Nayaganj",
                    "Kanpur Central",
                ],
            ),
            (
                "lucknow",
                "build_lucknow_metro_unofficial_gtfs",
                [
                    "Chaudhary Charan Singh International Airport",
                    "Amausi",
                    "Transport Nagar",
                    "Krishna Nagar",
                    "Singar Nagar",
                    "Alambagh",
                    "Alambagh Bus Station",
                    "Mawaiya",
                    "Durgapuri",
                    "Charbagh Railway Station",
                    "Hussainganj",
                    "Sachivalaya",
                    "Hazratganj",
                    "KD Singh Babu Stadium",
                    "Vishwavidyalaya",
                    "IT College",
                    "Badshah Nagar",
                    "Lekhraj Market",
                    "Bhootnath Market",
                    "Indira Nagar",
                    "Munshipulia",
                ],
            ),
        ]:
            with self.subTest(city=city), tempfile.TemporaryDirectory() as tmp:
                city_root = Path(tmp)
                city_dir = city_root / city
                (city_dir / "layers").mkdir(parents=True)
                features = [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [80.0 + idx / 100, 26.0 + idx / 100]},
                        "properties": {"name": station_name},
                    }
                    for idx, station_name in enumerate(station_names)
                ]
                (city_dir / "layers" / "metro.geojson").write_text(
                    json.dumps({"type": "FeatureCollection", "features": features}),
                    encoding="utf-8",
                )

                self.assertTrue(hasattr(constructed_metro_recipe, builder_name), builder_name)
                builder = getattr(constructed_metro_recipe, builder_name)
                result = builder(city_root=city_root, generated_at="2026-07-04T00:00:00Z")

                self.assertEqual(result["stops"], len(station_names))
                self.assertEqual(result["routes"], 1)
                self.assertTrue(
                    (city_dir / "source" / "transit" / "gtfs" / f"{city}_metro_unofficial_constructed_gtfs.zip").exists()
                )

    def test_file_repository_reads_static_gtfs_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            gtfs_dir = _write_gtfs_fixture(base)
            zip_path = base / "feed.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                for path in gtfs_dir.glob("*.txt"):
                    zf.write(path, path.name)

            inputs = FileGtfsCorridorInputRepository(zip_path).load()

            self.assertEqual(inputs.stops[0]["stop_id"], "s1")
            self.assertEqual(inputs.routes[0]["route_short_name"], "1")
            self.assertEqual(inputs.stop_times[0]["trip_id"], "t1")

    def test_multimodal_recipe_boundary_writes_layers_and_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            gtfs_dir = _write_gtfs_fixture(base)
            city_root = base / "cities"
            (city_root / "mumbai").mkdir(parents=True)
            (city_root / "mumbai" / "layers").mkdir()
            (city_root / "mumbai" / "layers" / "layer_manifest.json").write_text(
                json.dumps({"layers": []}),
                encoding="utf-8",
            )
            manifest = {
                "feeds": [
                    {
                        "feed_id": "mumbai_best_bus",
                        "city": "mumbai",
                        "mode": "bus",
                        "operator": "BEST",
                        "stop_layer": "bus_stops",
                        "route_layer": "bus_routes",
                        "path": str(gtfs_dir),
                    },
                    {
                        "feed_id": "mumbai_metro",
                        "city": "mumbai",
                        "mode": "metro",
                        "operator": "Mumbai Metro",
                        "stop_layer": "metro_gtfs_stops",
                        "route_layer": "metro_gtfs_routes",
                    },
                ]
            }

            result = build_city_multimodal_layers(
                "mumbai",
                feed_run_specs_from_manifest(manifest, "mumbai"),
                city_root,
            )

            self.assertEqual(sorted(result.layers), ["bus_routes.geojson", "bus_stops.geojson"])
            bus_routes = json.loads((city_root / "mumbai" / "layers" / "bus_routes.geojson").read_text())
            layer_manifest = json.loads((city_root / "mumbai" / "layers" / "layer_manifest.json").read_text())
            sources = json.loads(
                (city_root / "mumbai" / "source" / "transit" / "multimodal_transit.sources.json").read_text()
            )
            self.assertEqual(bus_routes["features"][0]["properties"]["source_feed_id"], "mumbai_best_bus")
            self.assertEqual([layer["id"] for layer in layer_manifest["layers"]], ["bus_stops", "bus_routes"])
            self.assertEqual(sources["feeds"][0]["status"], "ok")
            self.assertEqual(sources["feeds"][1]["status"], "missing")
            self.assertEqual(sources["feeds"][1]["missing_reason"], "No GTFS path configured.")

    def test_multimodal_recipe_labels_unofficial_constructed_feeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            gtfs_dir = _write_gtfs_fixture(base)
            city_root = base / "cities"
            layers = city_root / "ahmedabad" / "layers"
            layers.mkdir(parents=True)
            (layers / "layer_manifest.json").write_text(json.dumps({"layers": []}), encoding="utf-8")
            manifest = {
                "feeds": [
                    {
                        "feed_id": "ahmedabad_gmrc_unofficial_constructed",
                        "city": "ahmedabad",
                        "mode": "metro",
                        "operator": "Gujarat Metro Rail Corporation",
                        "stop_layer": "metro_gtfs_stops",
                        "route_layer": "metro_gtfs_routes",
                        "path": str(gtfs_dir),
                        "provenance_status": "unofficial_constructed",
                    }
                ]
            }

            build_city_multimodal_layers(
                "ahmedabad",
                feed_run_specs_from_manifest(manifest, "ahmedabad"),
                city_root,
            )

            layer_manifest = json.loads((layers / "layer_manifest.json").read_text())
            labels = {layer["id"]: layer["label"] for layer in layer_manifest["layers"]}
            self.assertEqual(labels["metro_gtfs_stops"], "Metro stops (unofficial GTFS)")
            self.assertEqual(labels["metro_gtfs_routes"], "Metro routes (unofficial GTFS)")

    def test_multimodal_recipe_can_update_one_feed_without_dropping_existing_source_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            gtfs_dir = _write_gtfs_fixture(base)
            city_root = base / "cities"
            sources_dir = city_root / "kolkata" / "source" / "transit"
            layers = city_root / "kolkata" / "layers"
            sources_dir.mkdir(parents=True)
            layers.mkdir(parents=True)
            (sources_dir / "multimodal_transit.sources.json").write_text(
                json.dumps(
                    {
                        "schema": "sevent4.multimodal_transit.sources.v1",
                        "feeds": [
                            {
                                "feed_id": "kolkata_metro",
                                "city": "kolkata",
                                "mode": "metro",
                                "operator": "Kolkata Metro Railway",
                                "status": "not_found",
                                "stop_layer": "metro_gtfs_stops.geojson",
                                "route_layer": "metro_gtfs_routes.geojson",
                            },
                            {
                                "feed_id": "kolkata_wbtc_bus_unofficial_constructed",
                                "city": "kolkata",
                                "mode": "bus",
                                "operator": "West Bengal Transport Corporation",
                                "status": "unofficial_constructed",
                                "stop_layer": "bus_stops.geojson",
                                "route_layer": "bus_routes.geojson",
                                "stop_features": 80,
                                "route_features": 94,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            manifest = {
                "feeds": [
                    {
                        "feed_id": "kolkata_wbtc_bus_unofficial_constructed",
                        "city": "kolkata",
                        "mode": "bus",
                        "operator": "West Bengal Transport Corporation",
                        "stop_layer": "bus_stops",
                        "route_layer": "bus_routes",
                        "path": str(gtfs_dir),
                        "provenance_status": "unofficial_constructed",
                    }
                ]
            }

            build_city_multimodal_layers(
                "kolkata",
                feed_run_specs_from_manifest(manifest, "kolkata"),
                city_root,
                merge_existing_sources=True,
            )

            sources = json.loads((sources_dir / "multimodal_transit.sources.json").read_text(encoding="utf-8"))
            feeds = {feed["feed_id"]: feed for feed in sources["feeds"]}
            self.assertEqual(list(feeds), ["kolkata_metro", "kolkata_wbtc_bus_unofficial_constructed"])
            self.assertEqual(feeds["kolkata_metro"]["status"], "not_found")
            self.assertEqual(feeds["kolkata_wbtc_bus_unofficial_constructed"]["status"], "unofficial_constructed")
            self.assertEqual(feeds["kolkata_wbtc_bus_unofficial_constructed"]["stop_features"], 2)
            self.assertEqual(feeds["kolkata_wbtc_bus_unofficial_constructed"]["route_features"], 1)

    def test_ahmedabad_gmrc_constructed_feed_matches_current_official_station_scope(self) -> None:
        route_ids = {route["route_id"] for route in constructed_metro_recipe.AHMEDABAD_GMRC_ROUTES}
        stop_names = {
            stop_name
            for route in constructed_metro_recipe.AHMEDABAD_GMRC_ROUTES
            for stop_name in route["stops"]
        }

        self.assertEqual(
            route_ids,
            {
                "gmrc_east_west",
                "gmrc_north_south",
                "gmrc_gandhinagar_mahatma_mandir",
                "gmrc_gift_city_branch",
            },
        )
        self.assertEqual(len(stop_names), 53)
        for station in (
            "Dholakuva Circle",
            "Infocity",
            "Sector-1",
            "Sector 10A",
            "Sachivalaya",
            "Akshardham",
            "Juna Sachivalaya",
            "Sector-16",
            "Sector-24",
            "Mahatma Mandir",
            "PDEU",
            "GIFT City",
        ):
            self.assertIn(station, stop_names)

    def test_multimodal_recipe_labels_sample_constructed_feeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            gtfs_dir = _write_gtfs_fixture(base)
            city_root = base / "cities"
            layers = city_root / "bhubaneswar" / "layers"
            layers.mkdir(parents=True)
            (layers / "layer_manifest.json").write_text(json.dumps({"layers": []}), encoding="utf-8")
            manifest = {
                "feeds": [
                    {
                        "feed_id": "bhubaneswar_iudx_sample_constructed",
                        "city": "bhubaneswar",
                        "mode": "bus",
                        "operator": "CRUT",
                        "stop_layer": "bus_stops",
                        "route_layer": "bus_routes",
                        "path": str(gtfs_dir),
                        "provenance_status": "sample_public_constructed_gtfs",
                    }
                ]
            }

            build_city_multimodal_layers(
                "bhubaneswar",
                feed_run_specs_from_manifest(manifest, "bhubaneswar"),
                city_root,
            )

            layer_manifest = json.loads((layers / "layer_manifest.json").read_text())
            labels = {layer["id"]: layer["label"] for layer in layer_manifest["layers"]}
            self.assertEqual(labels["bus_stops"], "Bus stops (IUDX sample GTFS)")
            self.assertEqual(labels["bus_routes"], "Bus routes (IUDX sample GTFS)")


def _write_gtfs_fixture(base: Path) -> Path:
    gtfs_dir = base / "gtfs"
    gtfs_dir.mkdir()
    (gtfs_dir / "stops.txt").write_text(
        "stop_id,stop_lon,stop_lat\ns1,72.1,23.1\ns2,72.2,23.2\n",
        encoding="utf-8",
    )
    (gtfs_dir / "routes.txt").write_text(
        "route_id,route_short_name,route_long_name,agency_id\nr1,1,Main Road,AMTS\n",
        encoding="utf-8",
    )
    (gtfs_dir / "trips.txt").write_text(
        "route_id,trip_id,shape_id\nr1,t1,\n",
        encoding="utf-8",
    )
    (gtfs_dir / "stop_times.txt").write_text(
        "trip_id,stop_id,stop_sequence\nt1,s2,2\nt1,s1,1\n",
        encoding="utf-8",
    )
    return gtfs_dir


if __name__ == "__main__":
    unittest.main()
