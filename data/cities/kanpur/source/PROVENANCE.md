# PROVENANCE — Kanpur (SevenT4 Civic Atlas)

City: Kanpur | State: Uttar Pradesh | District: Kanpur Nagar
Municipal body: Kanpur Nagar Nigam (KMC) | Acquired: 2026-06
City bbox (OSM extraction): 80.20–80.42 E, 26.38–26.55 N
CRS for all layers: EPSG:4326 (WGS84) unless noted.

---

## Boundaries

### districts.geojson — STATUS: OK
- Source: DataMeet `maps` — Census 2011 district boundaries
- URL: https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.shp
- License: CC BY 4.0 (DataMeet)
- Format: Shapefile (native EPSG:4326) → filtered to ST_NM="Uttar Pradesh", DISTRICT="Kanpur Nagar" → GeoJSON
- Count: 1 feature (Kanpur Nagar district)
- bbox: 79.94–80.57 E, 25.92–26.96 N (full district; covers city) ✓
- Note: Properties DISTRICT, ST_NM, ST_CEN_CD, DT_CEN_CD, censuscode.

### subdistricts.geojson — STATUS: OK
- Source: GADM 4.1, India, administrative level 3 (taluk/tehsil)
- URL: https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IND_3.json.zip
- License: GADM (free for academic/non-commercial use; attribution required)
- Format: GeoJSON (native EPSG:4326) → filtered NAME_2="KanpurNagar" → GeoJSON
- Count: 3 features — taluks: Bilhaur, Ghatampur, Kanpur
- bbox: 79.88–80.56 E, 25.92–26.97 N ✓
- Note: DataMeet `maps` repo has no sub-district layer; GADM L3 used as the standard open tehsil source (same dataset/schema used for the Chennai reference city). Props: state, district, taluk, TYPE_3, ENGTYPE_3.

### acs.geojson — STATUS: OK
- Source: DataMeet `maps` — Assembly Constituencies (India_AC)
- URL: https://raw.githubusercontent.com/datameet/maps/master/assembly-constituencies/India_AC.shp
- License: CC BY 4.0 (DataMeet)
- Format: Shapefile (EPSG:4326) → filtered ST_NAME="Uttar Pradesh", DIST_NAME="KANPUR NAGAR" → GeoJSON
- Count: 10 features (AC 209–218): Bilhaur (SC), Bithoor, Kalyanpur, Govindnagar, Sishamau, Arya Nagar, Kidwai Nagar, Kanpur Cantt., Maharajpur, Ghatampur (SC)
- bbox: 79.89–80.59 E, 25.92–26.96 N ✓
- Note: Props ST_NAME, DIST_NAME, AC_NO, AC_NAME, PC_NO, PC_NAME.

### pcs.geojson — STATUS: OK
- Source: DataMeet `maps` — Parliamentary Constituencies 2019 (india_pc_2019)
- URL: https://raw.githubusercontent.com/datameet/maps/master/parliamentary-constituencies/india_pc_2019.shp
- License: CC BY 4.0 (DataMeet)
- Format: Shapefile (EPSG:4326) → filtered to PCs covering Kanpur Nagar ACs → GeoJSON
- Count: 3 features — KANPUR, AKBARPUR, MISRIKH (SC)
- bbox: 79.85–80.83 E, 25.92–27.52 N (full PC extents) ✓
- Note: Kanpur Nagar district's ACs fall across 3 PCs; all 3 included. KANPUR is the core city PC. Props: st_name, pc_name, pc_code, st_code, pc_category.

### wards.geojson — STATUS: PARTIAL (see note)
- Source: DataMeet `Municipal_Spatial_Data` (Kanpur_wards.geojson); cross-confirmed identical on BharatLas (OpenCity/Oorvani Foundation)
- URL: https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Kanpur/Kanpur_wards.geojson
- Mirror: https://bharatlas.com/api/dl/admin/wards-kanpur/wards_kanpur.geojson
- License: ODbL-1.0 / OpenCity-Oorvani (CC-BY-SA style); DataMeet community
- Format: GeoJSON, native coords in **EPSG:3857 (Web Mercator)** — REPROJECTED to EPSG:4326 on ingest
- Count: 58 features (57 numbered wards + 1 empty placeholder, id=0, no ward_no)
- bbox after reprojection: 80.198–80.473 E, 26.335–26.533 N — squarely over Kanpur city ✓
- Props: ward_no, ward_name, zone_no, id, population_2020
- **HONEST NOTE — ward count mismatch:** KMC currently has 110 wards. The only openly-available digitized ward-boundary dataset is this older 58-polygon delimitation; ward_no values are sparse and range 1–110 (gaps). The current full 110-ward GIS boundary set is NOT openly published by UP/KMC (KMC publishes only a PDF chak-boundary list at kmc.up.nic.in, no geometry). This file is the best available real geometry; treat as legacy/partial ward coverage, not the current 110-ward map.

---

## OSM layers (osm/*.geojson) — STATUS: OK
- Source: OpenStreetMap via Overpass API (overpass-api.de)
- Query bbox: S26.38, W80.20, N26.55, E80.42
- License: ODbL 1.0 (© OpenStreetMap contributors)
- Format: GeoJSON, EPSG:4326. Props carry osm_id, osm_type + original OSM tags.
- Date: 2026-06

| layer | count | geom | note |
|-------|------:|------|------|
| roads.geojson | 31519 | LineString + 644 tagged nodes | all highway=* ways |
| metro.geojson | 154 | LineString + Point | Kanpur Metro Orange Line (Line 1, IIT Kanpur–Naubasta): route ways + stations (Kanpur Central, IIT Kanpur, Bada Chauraha, etc.) |
| bus_stops.geojson | 6 | Point | highway=bus_stop + bus platforms — OSM coverage sparse |
| hospitals.geojson | 234 | Point + Polygon | amenity hospital/clinic |
| schools.geojson | 57 | Point + Polygon | school/college/university |
| libraries.geojson | 1 | Point | amenity=library — OSM coverage sparse |
| toilets.geojson | 25 | Point + Polygon | amenity=toilets |
| police.geojson | 7 | Point + Polygon | amenity=police |
| fire.geojson | 1 | Point | amenity=fire_station — OSM coverage sparse |

All OSM layer bboxes validated within/around the Kanpur city bbox. ✓
Sparse layers (libraries, fire, bus_stops) reflect genuine thin OSM coverage in Kanpur, not extraction error.

---

## Population (WorldPop) — STATUS: INCOMPLETE / API UNAVAILABLE
- Method: per-ward WorldPop API — POST dataset=wpgppop, year=2020, geojson=<5dp ward geom> → taskid → poll task → data.total_population.
- Endpoint: https://api.worldpop.org/v1/services/stats ; https://api.worldpop.org/v1/tasks/<taskid>
- Dataset: WorldPop Global Project Population (wpgppop) 2020, ~100m. License: CC BY 4.0.
- Property `population_2020` is present on all 58 ward features but is currently **null** for every ward.
- **HONEST NOTE:** The WorldPop stats API was hit with REAL POST requests (no fabricated values). Early in the run ~16–18 wards returned valid populations (e.g. ward 1 = 13314, ward 43 = 26319, ward 76 = 12722), but the public API became saturated/unresponsive — single-ward submit calls then timed out repeatedly at 120s+ and returned malformed (concatenated-JSON) bodies. A hardened, checkpointing, resumable client (`worldpop_robust.py`, tolerant JSON parse + 4× retry/backoff + 150s timeouts) was written and run, but the upstream API could not complete even one full submit→poll→finish cycle under load. No values were fabricated; partial early results were not persisted because the API failed before a clean full pass.
- TO COMPLETE LATER (when WorldPop API recovers): from this dir run `python3 worldpop_robust.py` — it resumes, skipping any ward that already has a non-null `population_2020`, and checkpoints after every ward.
- The empty placeholder feature (id=0, no ward_no/name) is intentionally left null and skipped by the client.
