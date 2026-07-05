#!/usr/bin/env python3
"""Construct an unofficial static GTFS metro feed from sourced station/timetable inputs."""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

GMRC_SOURCE_URLS = [
    "https://www.gujaratmetrorail.com/ahmedabad/",
    "https://www.gujaratmetrorail.com/wp-content/uploads/2026/05/Revised-Time-Table-on-18.05.2026updated.jpg",
    "https://www.gujaratmetrorail.com/wp-content/uploads/2026/04/Tentative-TT-18.05.26.pdf",
    "https://www.gujaratmetrorail.com/wp-content/uploads/2026/04/Press-note-16.05.26.pdf",
    "https://overpass-api.de/api/interpreter",
]

KOLKATA_METRO_SOURCE_URLS = [
    "https://mtp.indianrailways.gov.in/",
    "https://en.wikipedia.org/wiki/Masterda_Surya_Sen_metro_station",
    "https://en.wikipedia.org/wiki/Gitanjali_metro_station",
]

MUMBAI_METRO_SOURCE_URLS = [
    "https://mmrda.maharashtra.gov.in/en/projects/transport/metro-line-1/overview",
    "https://mmrda.maharashtra.gov.in/en/projects/transport/metro-line-2A/overview",
    "https://timesofindia.indiatimes.com/city/mumbai/mumbai-metropolitan-commissioner-inspects-line-2b-phase-1-issues-directives-for-timely-completion/articleshow/123884545.cms",
    "https://mmrda.maharashtra.gov.in/en/projects/transport/metro-line-7/overview",
    "https://mmrda.maharashtra.gov.in/en/projects/transport/metro-line-9/overview",
    "https://mmrda.maharashtra.gov.in/en/division/mmmocl/overview",
    "https://en.wikipedia.org/wiki/Aarey_JVLR_metro_station",
]

JAIPUR_METRO_SOURCE_URLS = [
    "https://www.jaipurmetrorail.in/",
    "https://en.wikipedia.org/wiki/Jaipur_Metro",
    "https://en.wikipedia.org/wiki/Mansarovar_metro_station",
    "https://en.wikipedia.org/wiki/Badi_Chaupar_metro_station",
]

KANPUR_METRO_SOURCE_URLS = [
    "https://kanpur.upmetrorail.com/",
    "https://en.wikipedia.org/wiki/Kanpur_Metro",
    "https://en.wikipedia.org/wiki/IIT_Kanpur_metro_station",
    "https://en.wikipedia.org/wiki/Kanpur_Central_metro_station",
]

LUCKNOW_METRO_SOURCE_URLS = [
    "https://lucknow.upmetrorail.com/",
    "https://en.wikipedia.org/wiki/Lucknow_Metro",
    "https://en.wikipedia.org/wiki/Munshi_Pulia_metro_station",
    "https://en.wikipedia.org/wiki/Chaudhary_Charan_Singh_International_Airport_metro_station",
]

AHMEDABAD_GMRC_ROUTES = [
    {
        "route_id": "gmrc_east_west",
        "short_name": "EW",
        "long_name": "Ahmedabad Metro East-West Line",
        "stops": [
            "Thaltej Gam",
            "Thaltej",
            "Doordarshan Kendra",
            "Gurukul Road",
            "Gujarat University Station",
            "Commerce Six Roads",
            "Stadium",
            "Old High Court",
            "Shahpur Station",
            "Gheekanta",
            "Kalupur Railway Station",
            "Kankaria East",
            "Apparel Park",
            "Amraiwadi",
            "Rabari Colony",
            "Vastral",
            "Nirant Cross Roads",
            "Vastral Gam",
        ],
        "frequencies": [{"start_time": "06:20:00", "end_time": "22:00:00", "headway_secs": 720}],
    },
    {
        "route_id": "gmrc_north_south",
        "short_name": "NS",
        "long_name": "Ahmedabad Metro North-South Line",
        "stops": [
            "APMC",
            "Jivraj Park",
            "Rajiv Nagar",
            "Shreyas",
            "Paldi",
            "Gandhigram",
            "Old High Court",
            "Usmanpura",
            "Vijay Nagar",
            "Vadaj",
            "Ranip",
            "AEC",
            "Sabarmati",
            "Motera Stadium",
        ],
        "frequencies": [{"start_time": "06:20:00", "end_time": "22:00:00", "headway_secs": 720}],
    },
    {
        "route_id": "gmrc_gandhinagar_mahatma_mandir",
        "short_name": "GJ",
        "long_name": "Ahmedabad-Gandhinagar Metro to Mahatma Mandir",
        "stops": [
            "Motera Stadium",
            "Koteshwar Road",
            "Vishwakarma College",
            "Tapovan Circle",
            "Narmada Canal",
            "Koba Circle",
            "Juna Koba",
            "Koba Gam",
            "GNLU",
            "Raysan",
            "Randesan",
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
        ],
        "frequencies": [{"start_time": "06:20:00", "end_time": "22:00:00", "headway_secs": 720}],
    },
    {
        "route_id": "gmrc_gift_city_branch",
        "short_name": "GIFT",
        "long_name": "Ahmedabad-Gandhinagar Metro GIFT City branch",
        "stops": [
            "GNLU",
            "PDEU",
            "GIFT City",
        ],
        "frequencies": [{"start_time": "06:20:00", "end_time": "22:00:00", "headway_secs": 720}],
    },
]

AHMEDABAD_EXTRA_STATIONS = {
    "Dholakuva Circle": {"coordinates": [72.6433202, 23.1859445]},
    "Infocity": {"coordinates": [72.6397126, 23.1922574]},
    "Sector-1": {"coordinates": [72.6431519, 23.2049077]},
    "Sector 10A": {"coordinates": [72.6501927, 23.2114841]},
    "Sachivalaya": {"coordinates": [72.6587511, 23.2150688]},
    "Akshardham": {"coordinates": [72.6641817, 23.2236772]},
    "Juna Sachivalaya": {"coordinates": [72.6594151, 23.2289260]},
    "Sector-16": {"coordinates": [72.6501659, 23.2338826]},
    "Sector-24": {"coordinates": [72.6414782, 23.2385075]},
    "Mahatma Mandir": {"coordinates": [72.6338714, 23.2339412]},
    "PDEU": {"coordinates": [72.6612117, 23.1548645]},
}

KOLKATA_METRO_ROUTES = [
    {
        "route_id": "kolkata_blue",
        "short_name": "Blue",
        "long_name": "Kolkata Metro Blue Line",
        "stops": [
            "Dakshineshwar",
            "Baranagar",
            "Noapara",
            "Dum Dum",
            "Belgachia",
            "Shyambazar",
            "Shobhabazar Sutanuti",
            "Girish Park",
            "Mahatma Gandhi Road",
            "Central",
            "Chandni Chowk",
            "Esplanade (Line 1)",
            "Park Street",
            "Maidan",
            "Rabindra Sadan",
            "Netaji Bhavan",
            "Jatin Das Park",
            "Kalighat",
            "Rabindra Sarobar",
            "Mahanayak Uttam Kumar",
            "Netaji",
            "Masterda Surya Sen",
            "Gitanjali",
            "Kavi Nazrul",
            "Shahid Khudiram",
            "Kavi Subhash (Blue Line)",
        ],
        "frequencies": [{"start_time": "06:30:00", "end_time": "22:30:00", "headway_secs": 720}],
    },
    {
        "route_id": "kolkata_green",
        "short_name": "Green",
        "long_name": "Kolkata Metro Green Line",
        "stops": [
            "Howrah Maidan",
            "Howrah",
            "Mahakaran",
            "Esplanade (Line 2)",
            "Sealdah",
            "Phoolbagan",
            "Salt Lake Stadium",
            "Bengal Chemical",
            "City Centre",
            "Central Park",
            "Karunamoyee",
            "Salt Lake Sector V",
        ],
        "frequencies": [{"start_time": "06:30:00", "end_time": "22:30:00", "headway_secs": 720}],
    },
    {
        "route_id": "kolkata_purple",
        "short_name": "Purple",
        "long_name": "Kolkata Metro Purple Line",
        "stops": [
            "Joka",
            "Thakurpukur",
            "Sakher Bazar",
            "Behala Chowrasta",
            "Behala Bazar",
            "Taratala",
            "Majerhat",
        ],
        "frequencies": [{"start_time": "06:30:00", "end_time": "22:30:00", "headway_secs": 900}],
    },
    {
        "route_id": "kolkata_orange",
        "short_name": "Orange",
        "long_name": "Kolkata Metro Orange Line",
        "stops": [
            "Kavi Subhash",
            "Satyajit Ray",
            "Jyotirindra Nandi",
            "Kavi Sukanta",
            "Hemanta Mukhopadhyay",
            "VIP Bazar",
            "Ritwik Ghatak",
            "Barun Sengupta",
            "Beleghata",
        ],
        "frequencies": [{"start_time": "06:30:00", "end_time": "22:30:00", "headway_secs": 900}],
    },
    {
        "route_id": "kolkata_yellow",
        "short_name": "Yellow",
        "long_name": "Kolkata Metro Yellow Line",
        "stops": [
            "Noapara",
            "Dum Dum Cantonment",
            "Jessore Road",
            "Jai Hind",
        ],
        "frequencies": [{"start_time": "06:30:00", "end_time": "22:30:00", "headway_secs": 900}],
    },
]

KOLKATA_EXTRA_STATIONS = {
    "Masterda Surya Sen": {"coordinates": [88.360871, 22.473521]},
    "Gitanjali": {"coordinates": [88.369985, 22.469426]},
}

MUMBAI_METRO_ROUTES = [
    {
        "route_id": "mumbai_blue_1",
        "short_name": "1",
        "long_name": "Mumbai Metro Blue Line 1",
        "stops": [
            "Versova",
            "D. N. Nagar",
            "Azad Nagar",
            "Andheri L1",
            "Western Express Highway",
            "Chakala",
            "Airport Road",
            "Marol Naka Line 1",
            "Saki Naka",
            "Asalpha",
            "Jagruti Nagar",
            "Ghatkopar Metro",
        ],
        "frequencies": [{"start_time": "05:30:00", "end_time": "23:30:00", "headway_secs": 600}],
    },
    {
        "route_id": "mumbai_yellow_2a",
        "short_name": "2A",
        "long_name": "Mumbai Metro Yellow Line 2A",
        "stops": [
            "Dahisar (East) [Line 2]",
            "Anand Nagar",
            "Kandarpada",
            "Mandapeshwar - I.C. Colony",
            "Eksar",
            "Borivali (West)",
            "Shimpoli",
            "Kandivali (West)",
            "Dahanukarwadi",
            "Valnai-Meeth Chowky",
            "Malad (West)",
            "Lower Malad",
            "Bangur Nagar",
            "Goregaon (West)",
            "Oshiwara",
            "Lower Oshiwara",
            "Andheri (West)",
        ],
        "frequencies": [{"start_time": "05:30:00", "end_time": "23:30:00", "headway_secs": 600}],
    },
    {
        "route_id": "mumbai_yellow_2b_phase_1",
        "short_name": "2B",
        "long_name": "Mumbai Metro Yellow Line 2B Phase 1",
        "stops": [
            "Mandale",
            "Mankhurd",
            "BSNL",
            "Shivaji Chowk",
            "Diamond Garden",
        ],
        "frequencies": [{"start_time": "05:30:00", "end_time": "23:30:00", "headway_secs": 600}],
    },
    {
        "route_id": "mumbai_red_7",
        "short_name": "7",
        "long_name": "Mumbai Metro Red Line 7",
        "stops": [
            "Gundavali",
            "Mogra",
            "Jogeshwari (East)",
            "Goregaon (East)",
            "Aarey",
            "Dindoshi",
            "Kurar",
            "Akurli",
            "Poisar",
            "Magathane",
            "Devipada",
            "Rashtriya Udyan",
            "Ovaripada",
            "Dahisar (East) [Line 7]",
        ],
        "frequencies": [{"start_time": "05:30:00", "end_time": "23:30:00", "headway_secs": 600}],
    },
    {
        "route_id": "mumbai_red_9_phase_1",
        "short_name": "9",
        "long_name": "Mumbai Metro Red Line 9 Phase 1",
        "stops": [
            "Dahisar (East) [Line 9]",
            "Pandurang Wadi",
            "Miragaon",
            "Kashigaon",
        ],
        "frequencies": [{"start_time": "05:30:00", "end_time": "23:30:00", "headway_secs": 600}],
    },
    {
        "route_id": "mumbai_aqua_3",
        "short_name": "3",
        "long_name": "Mumbai Metro Aqua Line 3",
        "stops": [
            "Cuffe Parade",
            "Vidhan Bhavan",
            "Churchgate",
            "Hutatma Chowk",
            "Chhatrapati Shivaji Maharaj Terminus",
            "Kalbadevi",
            "Girgaon",
            "Grant Road",
            "Jagannath Shankar Sheth Metro",
            "Mahalaxmi",
            "Science Centre",
            "Acharya Atre Chowk",
            "Worli",
            "Siddhivinayak Temple",
            "Dadar",
            "Shitala Devi Mandir",
            "Dharavi",
            "Bandra Kurla Complex (BKC)",
            "Bandra Colony",
            "Santacruz",
            "CSMI Airport Domestic T1",
            "Sahar Road",
            "CSMI Airport International T2",
            "Marol Naka (Line 3)",
            "MIDC - Andheri",
            "SEEPZ",
            "Aarey JVLR",
        ],
        "frequencies": [{"start_time": "05:30:00", "end_time": "23:30:00", "headway_secs": 600}],
    },
]

MUMBAI_EXTRA_STATIONS = {
    # Line 1 station points are derived from the local OSM Line 1 route geometry
    # and MMRDA's published station order, not from an agency-published GTFS feed.
    "Versova": {"coordinates": [72.8213871, 19.1302777]},
    "D. N. Nagar": {"coordinates": [72.8304619, 19.1282551]},
    "Azad Nagar": {"coordinates": [72.8395648, 19.1264785]},
    "Andheri L1": {"coordinates": [72.8471294, 19.1215452]},
    "Western Express Highway": {"coordinates": [72.8550575, 19.1166916]},
    "Chakala": {"coordinates": [72.8636080, 19.1133811]},
    "Airport Road": {"coordinates": [72.8725008, 19.1107372]},
    "Marol Naka Line 1": {"coordinates": [72.8812377, 19.1075648]},
    "Saki Naka": {"coordinates": [72.8888791, 19.1029699]},
    "Asalpha": {"coordinates": [72.8951305, 19.0962781]},
    "Jagruti Nagar": {"coordinates": [72.9032561, 19.0918406]},
    "Ghatkopar Metro": {"coordinates": [72.9081226, 19.0862860]},
    "Aarey JVLR": {"coordinates": [72.884309, 19.130699]},
    "BSNL": {"coordinates": [72.9186, 19.0486]},
    "Shivaji Chowk": {"coordinates": [72.9069806, 19.0479383]},
}

JAIPUR_METRO_ROUTES = [
    {
        "route_id": "jaipur_pink",
        "short_name": "Pink",
        "long_name": "Jaipur Metro Pink Line",
        "stops": [
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
        "frequencies": [{"start_time": "06:00:00", "end_time": "22:00:00", "headway_secs": 900}],
    },
]

KANPUR_METRO_ROUTES = [
    {
        "route_id": "kanpur_orange",
        "short_name": "Orange",
        "long_name": "Kanpur Metro Orange Line",
        "stops": [
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
        "frequencies": [{"start_time": "06:00:00", "end_time": "22:30:00", "headway_secs": 600}],
    },
]

LUCKNOW_METRO_ROUTES = [
    {
        "route_id": "lucknow_red",
        "short_name": "Red",
        "long_name": "Lucknow Metro Red Line",
        "stops": [
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
        "frequencies": [{"start_time": "06:00:00", "end_time": "22:00:00", "headway_secs": 420}],
    },
]


def build_constructed_metro_gtfs(
    *,
    agency_id: str,
    agency_name: str,
    agency_url: str,
    station_geojson: Path,
    routes: list[dict[str, Any]],
    out_zip: Path,
    provenance_path: Path,
    source_urls: list[str],
    generated_at: str,
    extra_stations: dict[str, dict[str, Any]] | None = None,
    feed_start_date: str = "20260703",
    feed_end_date: str = "20271231",
    default_segment_minutes: int = 3,
) -> dict[str, int]:
    station_lookup = _station_lookup(station_geojson)
    station_lookup.update(extra_stations or {})
    route_rows = []
    trip_rows = []
    stop_time_rows = []
    frequency_rows = []
    shape_rows = []
    used_stops: dict[str, dict[str, Any]] = {}

    for route in routes:
        route_id = route["route_id"]
        stop_names = route["stops"]
        for stop_name in stop_names:
            used_stops[stop_name] = station_lookup[stop_name]
        route_rows.append(
            {
                "route_id": route_id,
                "agency_id": agency_id,
                "route_short_name": route.get("short_name", route_id),
                "route_long_name": route.get("long_name", route_id),
                "route_type": "1",
            }
        )
        for direction_id, direction_stops in enumerate((stop_names, list(reversed(stop_names)))):
            trip_id = f"{route_id}_{direction_id}"
            shape_id = f"{route_id}_{direction_id}"
            trip_rows.append(
                {
                    "route_id": route_id,
                    "service_id": "daily",
                    "trip_id": trip_id,
                    "trip_headsign": direction_stops[-1],
                    "direction_id": str(direction_id),
                    "shape_id": shape_id,
                }
            )
            for idx, stop_name in enumerate(direction_stops, 1):
                elapsed = (idx - 1) * int(route.get("segment_minutes", default_segment_minutes))
                hh = elapsed // 60
                mm = elapsed % 60
                stop_time_rows.append(
                    {
                        "trip_id": trip_id,
                        "arrival_time": f"{hh:02d}:{mm:02d}:00",
                        "departure_time": f"{hh:02d}:{mm:02d}:00",
                        "stop_id": _stop_id(agency_id, stop_name),
                        "stop_sequence": str(idx),
                    }
                )
                lon, lat = station_lookup[stop_name]["coordinates"]
                shape_rows.append(
                    {
                        "shape_id": shape_id,
                        "shape_pt_lat": f"{lat:.7f}",
                        "shape_pt_lon": f"{lon:.7f}",
                        "shape_pt_sequence": str(idx),
                    }
                )
            for frequency in route.get("frequencies", []):
                frequency_rows.append(
                    {
                        "trip_id": trip_id,
                        "start_time": frequency["start_time"],
                        "end_time": frequency["end_time"],
                        "headway_secs": str(frequency["headway_secs"]),
                        "exact_times": str(frequency.get("exact_times", 0)),
                    }
                )

    stop_rows = [
        {
            "stop_id": _stop_id(agency_id, name),
            "stop_name": name,
            "stop_lat": f"{value['coordinates'][1]:.7f}",
            "stop_lon": f"{value['coordinates'][0]:.7f}",
        }
        for name, value in sorted(used_stops.items())
    ]
    documents = {
        "agency.txt": _csv_text(
            ["agency_id", "agency_name", "agency_url", "agency_timezone"],
            [{"agency_id": agency_id, "agency_name": agency_name, "agency_url": agency_url, "agency_timezone": "Asia/Kolkata"}],
        ),
        "stops.txt": _csv_text(["stop_id", "stop_name", "stop_lat", "stop_lon"], stop_rows),
        "routes.txt": _csv_text(["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"], route_rows),
        "calendar.txt": _csv_text(
            ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"],
            [
                {
                    "service_id": "daily",
                    "monday": "1",
                    "tuesday": "1",
                    "wednesday": "1",
                    "thursday": "1",
                    "friday": "1",
                    "saturday": "1",
                    "sunday": "1",
                    "start_date": feed_start_date,
                    "end_date": feed_end_date,
                }
            ],
        ),
        "trips.txt": _csv_text(["route_id", "service_id", "trip_id", "trip_headsign", "direction_id", "shape_id"], trip_rows),
        "stop_times.txt": _csv_text(["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"], stop_time_rows),
        "frequencies.txt": _csv_text(["trip_id", "start_time", "end_time", "headway_secs", "exact_times"], frequency_rows),
        "shapes.txt": _csv_text(["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"], shape_rows),
        "feed_info.txt": _csv_text(
            ["feed_publisher_name", "feed_publisher_url", "feed_lang", "feed_start_date", "feed_end_date", "feed_version"],
            [
                {
                    "feed_publisher_name": f"{agency_name} unofficial construction",
                    "feed_publisher_url": agency_url,
                    "feed_lang": "en",
                    "feed_start_date": feed_start_date,
                    "feed_end_date": feed_end_date,
                    "feed_version": generated_at,
                }
            ],
        ),
    }

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, text in documents.items():
            zf.writestr(name, text)

    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(
        json.dumps(
            {
                "schema": "sevent4.constructed_gtfs.sources.v1",
                "status": "unofficial_constructed",
                "agency": agency_name,
                "generated_at": generated_at,
                "gtfs_zip": str(out_zip),
                "source_urls": source_urls,
                "counts": {
                    "stops": len(stop_rows),
                    "routes": len(route_rows),
                    "trips": len(trip_rows),
                    "stop_times": len(stop_time_rows),
                    "frequencies": len(frequency_rows),
                },
                "note": "Unofficial static GTFS constructed from official public timetable/station source material; not an agency-published GTFS feed.",
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"stops": len(stop_rows), "routes": len(route_rows), "trips": len(trip_rows), "stop_times": len(stop_time_rows)}


def build_ahmedabad_gmrc_unofficial_gtfs(*, city_root: Path, generated_at: str) -> dict[str, int]:
    city_dir = city_root / "ahmedabad"
    return build_constructed_metro_gtfs(
        agency_id="GMRC",
        agency_name="Gujarat Metro Rail Corporation",
        agency_url="https://www.gujaratmetrorail.com/",
        station_geojson=city_dir / "layers" / "metro.geojson",
        routes=AHMEDABAD_GMRC_ROUTES,
        out_zip=city_dir / "source" / "transit" / "gtfs" / "ahmedabad_gmrc_unofficial_constructed_gtfs.zip",
        provenance_path=city_dir / "source" / "transit" / "ahmedabad_gmrc_unofficial_gtfs.sources.json",
        source_urls=GMRC_SOURCE_URLS,
        generated_at=generated_at,
        extra_stations=AHMEDABAD_EXTRA_STATIONS,
        feed_start_date="20260518",
        feed_end_date="20271231",
    )


def build_kolkata_metro_unofficial_gtfs(*, city_root: Path, generated_at: str) -> dict[str, int]:
    city_dir = city_root / "kolkata"
    return build_constructed_metro_gtfs(
        agency_id="KOLMETRO",
        agency_name="Metro Railway, Kolkata",
        agency_url="https://mtp.indianrailways.gov.in/",
        station_geojson=city_dir / "layers" / "metro.geojson",
        routes=KOLKATA_METRO_ROUTES,
        out_zip=city_dir / "source" / "transit" / "gtfs" / "kolkata_metro_unofficial_constructed_gtfs.zip",
        provenance_path=city_dir / "source" / "transit" / "kolkata_metro_unofficial_gtfs.sources.json",
        source_urls=KOLKATA_METRO_SOURCE_URLS,
        generated_at=generated_at,
        extra_stations=KOLKATA_EXTRA_STATIONS,
        feed_start_date="20260704",
        feed_end_date="20271231",
    )


def build_mumbai_metro_unofficial_gtfs(*, city_root: Path, generated_at: str) -> dict[str, int]:
    city_dir = city_root / "mumbai"
    return build_constructed_metro_gtfs(
        agency_id="MUMMETRO",
        agency_name="Mumbai Metro operators",
        agency_url="https://www.mmmocl.co.in/",
        station_geojson=city_dir / "source" / "osm" / "rail_stations.geojson",
        routes=MUMBAI_METRO_ROUTES,
        out_zip=city_dir / "source" / "transit" / "gtfs" / "mumbai_metro_unofficial_constructed_gtfs.zip",
        provenance_path=city_dir / "source" / "transit" / "mumbai_metro_unofficial_gtfs.sources.json",
        source_urls=MUMBAI_METRO_SOURCE_URLS,
        generated_at=generated_at,
        extra_stations=MUMBAI_EXTRA_STATIONS,
        feed_start_date="20260704",
        feed_end_date="20271231",
    )


def build_jaipur_metro_unofficial_gtfs(*, city_root: Path, generated_at: str) -> dict[str, int]:
    city_dir = city_root / "jaipur"
    return build_constructed_metro_gtfs(
        agency_id="JAIPURMETRO",
        agency_name="Jaipur Metro Rail Corporation",
        agency_url="https://www.jaipurmetrorail.in/",
        station_geojson=city_dir / "layers" / "metro.geojson",
        routes=JAIPUR_METRO_ROUTES,
        out_zip=city_dir / "source" / "transit" / "gtfs" / "jaipur_metro_unofficial_constructed_gtfs.zip",
        provenance_path=city_dir / "source" / "transit" / "jaipur_metro_unofficial_gtfs.sources.json",
        source_urls=JAIPUR_METRO_SOURCE_URLS,
        generated_at=generated_at,
        feed_start_date="20260704",
        feed_end_date="20271231",
    )


def build_kanpur_metro_unofficial_gtfs(*, city_root: Path, generated_at: str) -> dict[str, int]:
    city_dir = city_root / "kanpur"
    return build_constructed_metro_gtfs(
        agency_id="KANPURMETRO",
        agency_name="Uttar Pradesh Metro Rail Corporation - Kanpur Metro",
        agency_url="https://kanpur.upmetrorail.com/",
        station_geojson=city_dir / "layers" / "metro.geojson",
        routes=KANPUR_METRO_ROUTES,
        out_zip=city_dir / "source" / "transit" / "gtfs" / "kanpur_metro_unofficial_constructed_gtfs.zip",
        provenance_path=city_dir / "source" / "transit" / "kanpur_metro_unofficial_gtfs.sources.json",
        source_urls=KANPUR_METRO_SOURCE_URLS,
        generated_at=generated_at,
        feed_start_date="20260704",
        feed_end_date="20271231",
    )


def build_lucknow_metro_unofficial_gtfs(*, city_root: Path, generated_at: str) -> dict[str, int]:
    city_dir = city_root / "lucknow"
    return build_constructed_metro_gtfs(
        agency_id="LUCKNOWMETRO",
        agency_name="Uttar Pradesh Metro Rail Corporation - Lucknow Metro",
        agency_url="https://lucknow.upmetrorail.com/",
        station_geojson=city_dir / "layers" / "metro.geojson",
        routes=LUCKNOW_METRO_ROUTES,
        out_zip=city_dir / "source" / "transit" / "gtfs" / "lucknow_metro_unofficial_constructed_gtfs.zip",
        provenance_path=city_dir / "source" / "transit" / "lucknow_metro_unofficial_gtfs.sources.json",
        source_urls=LUCKNOW_METRO_SOURCE_URLS,
        generated_at=generated_at,
        feed_start_date="20260704",
        feed_end_date="20271231",
    )


def _station_lookup(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for feature in data.get("features", []):
        name = (feature.get("properties") or {}).get("name")
        geometry = feature.get("geometry") or {}
        if not name or geometry.get("type") != "Point":
            continue
        out.setdefault(name, {"coordinates": geometry.get("coordinates")})
    return out


def _stop_id(agency_id: str, name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")
    return f"{agency_id}_{normalized}"


def _csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    handle = io.StringIO()
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return handle.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build unofficial constructed metro GTFS feeds.")
    parser.add_argument("city", choices=("ahmedabad", "jaipur", "kanpur", "kolkata", "lucknow", "mumbai"))
    parser.add_argument("--city-root", type=Path, default=Path("data/cities"))
    parser.add_argument("--generated-at", required=True)
    args = parser.parse_args()
    if args.city == "ahmedabad":
        result = build_ahmedabad_gmrc_unofficial_gtfs(city_root=args.city_root, generated_at=args.generated_at)
        print(
            f"[ahmedabad] unofficial GMRC GTFS: {result['stops']} stops, "
            f"{result['routes']} routes, {result['trips']} trips"
        )
    if args.city == "kolkata":
        result = build_kolkata_metro_unofficial_gtfs(city_root=args.city_root, generated_at=args.generated_at)
        print(
            f"[kolkata] unofficial Metro Railway GTFS: {result['stops']} stops, "
            f"{result['routes']} routes, {result['trips']} trips"
        )
    if args.city == "jaipur":
        result = build_jaipur_metro_unofficial_gtfs(city_root=args.city_root, generated_at=args.generated_at)
        print(
            f"[jaipur] unofficial Jaipur Metro GTFS: {result['stops']} stops, "
            f"{result['routes']} routes, {result['trips']} trips"
        )
    if args.city == "kanpur":
        result = build_kanpur_metro_unofficial_gtfs(city_root=args.city_root, generated_at=args.generated_at)
        print(
            f"[kanpur] unofficial Kanpur Metro GTFS: {result['stops']} stops, "
            f"{result['routes']} routes, {result['trips']} trips"
        )
    if args.city == "lucknow":
        result = build_lucknow_metro_unofficial_gtfs(city_root=args.city_root, generated_at=args.generated_at)
        print(
            f"[lucknow] unofficial Lucknow Metro GTFS: {result['stops']} stops, "
            f"{result['routes']} routes, {result['trips']} trips"
        )
    if args.city == "mumbai":
        result = build_mumbai_metro_unofficial_gtfs(city_root=args.city_root, generated_at=args.generated_at)
        print(
            f"[mumbai] unofficial Mumbai Metro GTFS: {result['stops']} stops, "
            f"{result['routes']} routes, {result['trips']} trips"
        )


if __name__ == "__main__":
    main()
