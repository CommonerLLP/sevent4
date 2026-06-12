# Chennai — Source Data Provenance

City: Chennai, Tamil Nadu. District: Chennai (GCC services spill into Tiruvallur / Kancheepuram post-expansion).
Municipal body: Greater Chennai Corporation (GCC) — 200 wards in 15 zones.
CRS for all layers: EPSG:4326 (WGS84). Acquisition date: 2026-06.

## Administrative & Electoral Boundaries

| Layer | File | Source | URL | License | Format | Features | CRS | Date | Status / Note |
|---|---|---|---|---|---|---|---|---|---|
| Districts | boundaries/districts.geojson | DataMeet maps (Census 2011) | https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.shp | CC-BY-4.0 (DataMeet) | GeoJSON (from SHP) | 3 | EPSG:4326 | 2026-06 | GOT — Chennai + Thiruvallur + Kancheepuram (GCC catchment). |
| Sub-districts / taluks (block proxy) | boundaries/subdistricts.geojson | geohacker/india (GADM-derived taluks) | https://raw.githubusercontent.com/geohacker/india/master/taluk/india_taluk.geojson | Open (GADM-derived, attribution) | GeoJSON | 18 | EPSG:4326 | 2026-06 | PARTIAL — 5 Chennai-district taluks + 13 from Thiruvallur/Kancheepuram. DataMeet has no TN sub-district GeoJSON; taluks used as block proxy. GADM vintage; boundaries pre-date recent TN district splits. |
| Assembly constituencies (AC) | boundaries/acs.geojson | DataMeet maps (India_AC) | https://raw.githubusercontent.com/datameet/maps/master/assembly-constituencies/India_AC.shp | CC-BY-4.0 (DataMeet) | GeoJSON (from SHP) | 16 | EPSG:4326 | 2026-06 | GOT — all 16 ACs in Chennai district. |
| Parliamentary constituencies (PC) | boundaries/pcs.geojson | DataMeet maps (india_pc_2019) | https://raw.githubusercontent.com/datameet/maps/master/parliamentary-constituencies/india_pc_2019_simplified.geojson | CC-BY-4.0 (DataMeet) | GeoJSON | 6 | EPSG:4326 | 2026-06 | GOT — Chennai North/Central/South + neighbouring Sriperumbudur, Thiruvallur, Kancheepuram (GCC spill). |
| GCC wards (200) | boundaries/wards.geojson | DataMeet Municipal_Spatial_Data | https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Chennai/Wards.geojson | CC-BY-4.0 (DataMeet) | GeoJSON | 200 | EPSG:4326 | 2026-06 | GOT — exactly 200 wards (1–200) across 15 zones. Dropped 1 non-ward polygon (Ward_No=0, St. Thomas Mount cantonment, Zone_No "-"). population_2020 attribute added from WorldPop (see below). |

## Core OSM Geolayers (Overpass, bbox 12.83–13.25 N, 80.10–80.34 E)

Source: OpenStreetMap via Overpass API (https://overpass-api.de/api/interpreter). License: ODbL 1.0. Date: 2026-06. CRS: EPSG:4326.

| Layer | File | Features | Geometry | Status / Note |
|---|---|---|---|---|
| Roads (motorway/trunk/primary/secondary) | osm/roads.geojson | 4214 | LineString (+28 Polygon) | GOT |
| Metro lines | osm/metro_lines.geojson | 136 | LineString | GOT — Chennai Metro subway way segments. |
| Metro stations | osm/metro_stations.geojson | 69 | Point | GOT |
| MTC bus stops | osm/bus_stops.geojson | 971 | Point | GOT |
| Hospitals | osm/hospitals.geojson | 835 | Point (way centroids) | GOT |
| Schools | osm/schools.geojson | 630 | Point (way centroids) | GOT |
| Libraries | osm/libraries.geojson | 102 | Point | GOT |
| Public toilets | osm/toilets.geojson | 105 | Point | GOT |
| Police stations | osm/police.geojson | 105 | Point | GOT |
| Fire stations | osm/fire_stations.geojson | 15 | Point | GOT |

## Population

| Layer | Source | Dataset | Year | Status / Note |
|---|---|---|---|---|
| Ward population | WorldPop (api.worldpop.org/v1/services/stats) | wpgppop | 2020 | See wards.geojson `population_2020`. Per-ward zonal-stats over WorldPop 100m constrained grid. Total = TBD_TOTAL across TBD_GOT/200 wards. |

## MISSING / Notes
- No authoritative TN/Chennai sub-district (revenue block) GeoJSON in DataMeet; GADM taluks substituted as block proxy (marked PARTIAL).
- GCC 200-ward boundaries sourced from DataMeet's municipal mirror of the 2011-delimitation GCC ward map (matches current 200-ward / 15-zone structure).
