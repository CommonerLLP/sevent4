# Jaipur — Source Data Provenance

City: Jaipur | State: Rajasthan | District: Jaipur
Acquisition date: 2026-06 | CRS: EPSG:4326 (WGS84) for all layers
bbox of interest: ~75.70–75.92 E, 26.80–27.00 N

## Municipal body note (2019 split)
The erstwhile single **Jaipur Municipal Corporation** (Nagar Nigam, ~91/77 wards) was
**split in 2019** into two bodies:
- **Jaipur Greater Municipal Corporation** — 150 wards
- **Jaipur Heritage Municipal Corporation** — 100 wards (~250 wards total)

Open ward geometry is available for **Greater (150 wards)** only. A dedicated
**Heritage (100 wards)** boundary file was **NOT found** in any open portal
(OpenCity, DataMeet, GitHub mirrors, Rajasthan portals) as of 2026-06 — see wards
STATUS below. The pre-split single-corporation file (77 wards, DataMeet) exists but
is superseded and was not used as the primary `wards.geojson`.

---

## boundaries/

### districts.geojson
- Source: DataMeet `maps` (Census 2011 district shapefile, `2011_Dist.shp`)
- URL: https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.{shp,shx,dbf,prj}
- License: CC-BY 2.5 IN (DataMeet community)
- Format: Esri Shapefile -> GeoJSON (geopandas), filtered DISTRICT="Jaipur"
- Count: 1 (Polygon) | CRS: EPSG:4326 | Date: 2026-06
- STATUS: OK — bbox 74.92–76.29 E, 26.44–27.86 N covers the city.

### subdistricts.geojson  (tehsils)
- Source: datta07/INDIAN-SHAPEFILES `INDIAN_SUB_DISTRICTS.geojson` (Census/LGD sub-districts)
- URL: https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/INDIA/INDIAN_SUB_DISTRICTS.geojson
- License: Open (repository; derived from Census 2011 / LGD)
- Format: GeoJSON, filtered dtname="Jaipur" & stname="RAJASTHAN"
- Count: 13 (Polygon) — Amber, Bassi, Chaksu, Chomu, Jaipur, Jamwa Ramgarh, Kotputli,
  Mauzamabad, Phagi, Phulera, Sanganer, Shahpura, Viratnagar
- CRS: EPSG:4326 | Date: 2026-06 | STATUS: OK.

### acs.geojson  (Assembly Constituencies)
- Source: DataMeet `maps` assembly-constituencies (`India_AC.shp`)
- URL: https://raw.githubusercontent.com/datameet/maps/master/assembly-constituencies/India_AC.{shp,shx,dbf,prj}
- License: CC-BY 2.5 IN (DataMeet)
- Format: Esri Shapefile -> GeoJSON (geopandas), filtered DIST_NAME="JAIPUR"
- Count: 19 (Polygon/MultiPolygon) | CRS: EPSG:4326 | Date: 2026-06
- STATUS: OK — incl. Hawa Mahal, Civil Lines, Sanganer, Malviya Nagar, Adarsh Nagar, etc.

### pcs.geojson  (Parliamentary Constituencies)
- Source: DataMeet `maps` parliamentary-constituencies (2019, simplified)
- URL: https://raw.githubusercontent.com/datameet/maps/master/parliamentary-constituencies/india_pc_2019_simplified.geojson
- License: CC-BY 2.5 IN (DataMeet)
- Format: GeoJSON, filtered st_name="Rajasthan" & pc_name contains "Jaipur"
- Count: 2 (MultiPolygon) — "Jaipur", "Jaipur Rural" | CRS: EPSG:4326 | Date: 2026-06
- STATUS: OK.

### wards.geojson  (PRIMARY — Greater Jaipur, 150 wards)
- Source: OpenCity (data.opencity.in) — "Greater Jaipur Nagar Nigam Wards 2024"
  (LGD 2024 snapshot; town_lgd_code 293844)
- URL: https://data.opencity.in/dataset/9a088bcc-0192-4070-b2e6-6cb050c742e0/resource/97dc97d0-baac-485f-93c1-0f2163d75dc3/download/43a00975-c97f-45d8-9b36-b3acbf0fb5eb.kml
- License: OpenCity / Open Data (LGD-derived)
- Format: KML -> GeoJSON (geopandas); fields: ward_no, wardcode, ward_lgd_code,
  ward_lgd_name, town_lgd_code, townname, state, corporation="Jaipur Greater"
- Count: 150 (MultiPolygon), wardcode 1–150 | CRS: EPSG:4326 | Date: 2026-06
- bbox 75.69–75.91 E, 26.77–27.03 N — confirmed over Jaipur city.
- population_2020: added per ward via WorldPop wpgppop 2020 (see below).
- STATUS: OK (Greater corporation only).

### Jaipur Heritage Municipal Corporation wards (100 wards)
- STATUS: **MISSING** — No open ward-boundary geometry located for the Heritage
  corporation (separate LGD town code) in OpenCity, DataMeet Municipal_Spatial_Data,
  datta07/INDIAN-SHAPEFILES, yashveeeeeeer/india-geodata, or Rajasthan state portals
  as of 2026-06. Only the Greater (150) file and the superseded pre-2019 single
  corporation file (77 wards, DataMeet) are openly published. No geometry fabricated.
- Pre-split reference (NOT used as primary): DataMeet `Jaipur_Wards.geojson` (77 wards),
  https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Jaipur/Jaipur_Wards.geojson

---

## osm/  (OpenStreetMap via Overpass API, fetched 2026-06)
- Source: OpenStreetMap contributors, Overpass API (overpass-api.de / kumi.systems)
- License: ODbL 1.0 | Format: GeoJSON | CRS: EPSG:4326
- bbox queried: S26.75 W75.65 N27.05 E75.95 (Jaipur city, widened slightly)
- Fetch script: osm/_fetch_osm.py | counts in osm/_fetch_summary.json
- STATUS: OK for all layers below. Counts:
  - roads.geojson — 71,487 (LineString/Polygon)
  - metro_lines.geojson — 46 (LineString/MultiLineString) — Jaipur Metro Pink Line
  - metro_stations.geojson — 12 (Point) — operational Pink Line stations
  - bus_stops.geojson — 388 (Point) — JCTSL / general bus stops
  - hospitals.geojson — 436 (Point/Polygon)
  - schools.geojson — 73 (Point/Polygon) [amenity=school; many JP schools tagged otherwise]
  - libraries.geojson — 12 (Point/Polygon)
  - toilets.geojson — 52 (Point/Polygon)
  - police.geojson — 24 (Point/Polygon)
  - fire.geojson — 1 (Point) [sparse OSM coverage]

---

## population (WorldPop)
- Source: WorldPop Global Project Population Data, `wpgppop`, year 2020,
  via https://api.worldpop.org/v1/services/stats (async task + poll)
- Applied to wards.geojson as property `population_2020` (per Greater ward, 150 wards).
- Geometry sent at 5-decimal precision. Script: boundaries/_worldpop.py
- License: CC-BY 4.0 (WorldPop) | Date: 2026-06
- STATUS / totals: see summary at top of repo handoff (covers Greater corp only;
  Heritage population not computed — no Heritage geometry).
