# Bengaluru — Source Data Provenance

**City:** Bengaluru (Bangalore)
**State:** Karnataka · **District:** Bengaluru Urban
**Municipal body:** BBMP (Bruhat Bengaluru Mahanagara Palike)
**Wards:** 198 (2012 delimitation, BBMP) → 243 (2022 KSRSAC delimitation). The recent Greater Bengaluru Governance Act (GBA) / Greater Bengaluru Authority context proposes splitting BBMP into multiple corporations; the 243-ward layer reflects the latest KGIS delimitation and is used as the primary `wards.geojson`.
**Acquired:** 2026-06 · **CRS:** EPSG:4326 (WGS84) for all layers.
**City bbox (BBMP):** ~77.46–77.78 E, 12.83–13.14 N — all city layers validated inside this envelope. District/AC/PC layers extend south to ~12.65 N (Anekal taluk) which is correct for Bengaluru Urban district.

## Administrative & Electoral Boundaries

| Layer | File | Source | URL | License | Format | Features | CRS | Date | Status | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| Districts | boundaries/districts.geojson | DataMeet maps (Census 2011) | https://github.com/datameet/maps `Districts/Census_2011/2011_Dist.shp` | CC-BY-SA / ODbL (DataMeet) | GeoJSON (from SHP) | 1 | 4326 | 2026-06 | got | Bengaluru Urban only (Census name "Bangalore"). |
| Sub-districts / taluks | — | — | — | — | — | — | — | 2026-06 | **missing** | No openly-available taluk/sub-district polygon layer in DataMeet maps (repo only carries country/state/district + constituencies). 28 ACs below serve as the intra-district subdivision proxy. |
| Assembly constituencies (AC) | boundaries/acs.geojson | DataMeet assembly-constituencies | https://github.com/datameet/maps `assembly-constituencies/India_AC.shp` | CC-BY-SA / ODbL | GeoJSON (from SHP) | 28 | 4326 | 2026-06 | got | DIST_NAME=BANGALORE, AC_NO 150–177. One junk null-name feature (AC_NO 0) dropped. Matches the 28 ACs of Bengaluru Urban. |
| Parliamentary constituencies (PC) | boundaries/pcs.geojson | DataMeet parliamentary-constituencies (2019) | https://github.com/datameet/maps `parliamentary-constituencies/india_pc_2019_simplified.geojson` | CC-BY-SA / ODbL | GeoJSON | 3 | 4326 | 2026-06 | got | Bangalore Central / North / South (the 3 urban PCs). Bangalore Rural PC excluded as it lies mostly outside Bengaluru Urban. |
| BBMP wards (current) | boundaries/wards.geojson | DataMeet Municipal_Spatial_Data (scraped from KSRSAC / KGIS bengalurugis) | https://github.com/datameet/Municipal_Spatial_Data `Bangalore/BBMP.geojson` | CC-BY-SA 2.5 IN | GeoJSON | 243 | 4326 | 2026-06 | got | 2022 delimitation. Props: KGISWardID, KGISWardCode, LGD_WardCode, KGISWardNo, KGISWardName, KGISTownCode. **Primary ward layer**; carries `population_2020`. |
| BBMP wards (2012) | boundaries/wards_198_2012.geojson | DataMeet Municipal_Spatial_Data / OpenBangalore | https://github.com/datameet/Municipal_Spatial_Data `Bangalore/BBMP_oldWards.geojson` | CC-BY-SA 2.5 IN / ODbL | GeoJSON | 198 | 4326 | 2026-06 | got | 2012 delimitation, retained for reference. Carries census attributes (POP_TOTAL, POP_SC/ST, RESERVATION, AREA_SQ_KM, AC mapping). |

## Core Geolayers (OpenStreetMap via Overpass API)

Source: OpenStreetMap contributors, ODbL. Fetched via Overpass (overpass-api.de / overpass.kumi.systems) with bbox (12.83,77.45,13.15,77.80). Date 2026-06. CRS 4326.

| Layer | File | Geom | Features | Status | Note |
|---|---|---|---|---|---|
| Major roads | osm/roads.geojson | LineString | 7170 | got | highway = motorway/trunk/primary/secondary. |
| Namma Metro lines | osm/metro_lines.geojson | LineString | 550 | got | railway=subway way segments. |
| Namma Metro stations | osm/metro_stations.geojson | Point | 89 | got | subway stations (includes platform/entrance-adjacent nodes). |
| BMTC bus stops | osm/bus_stops.geojson | Point | 3378 | got | highway=bus_stop + PT platforms (bus). |
| Hospitals/clinics | osm/hospitals.geojson | Point | 1849 | got | amenity=hospital/clinic. |
| Schools | osm/schools.geojson | Point | 620 | got | amenity=school. |
| Libraries | osm/libraries.geojson | Point | 73 | got | amenity=library. |
| Public toilets | osm/toilets.geojson | Point | 423 | got | amenity=toilets. |
| Police | osm/police.geojson | Point | 71 | got | amenity=police. |
| Fire stations | osm/fire.geojson | Point | 4 | partial | amenity=fire_station; OSM under-mapped for fire in BLR. |

## Transit GTFS

| Feed | Source | Status | Note |
|---|---|---|---|
| BMTC GTFS | Transitland / OpenMobilityData | **missing** | Transitland REST API now requires an API key (HTTP 401 without one). No openly-downloadable BMTC GTFS located without authentication. BMTC has historically not published an open GTFS feed; Namma Metro/BMTC live data sits behind app APIs. Metro & bus-stop geometry captured via OSM above as a fallback.

## Population

| Layer | Source | Status | Note |
|---|---|---|---|
| WorldPop 2020 | WorldPop wpgppop (api.worldpop.org stats service) | see wards.geojson | Per-ward zonal total population (dataset=wpgppop, year=2020) written to `boundaries/wards.geojson` as `population_2020`. Computed via POST to /v1/services/stats (geometry rounded to 5dp) + task polling. License: WorldPop CC-BY 4.0.
