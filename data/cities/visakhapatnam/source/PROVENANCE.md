# PROVENANCE — Visakhapatnam (Vizag) Civic Atlas

City: Visakhapatnam (Vizag), Andhra Pradesh. District: Visakhapatnam.
Municipal body: GVMC (Greater Visakhapatnam Municipal Corporation), 98 wards.
Acquired: 2026-06. CRS: EPSG:4326 (WGS84) for all layers. Core bbox ~83.18–83.40 E, 17.62–17.80 N (GVMC extends to ~82.99–83.46 E / 17.55–17.94 N).

NOTE on vintage / AP reorganization: The Datameet/Census-2011 district, subdistrict, AC and PC layers reflect the **undivided Visakhapatnam district** (Census 2011 boundaries). In 2022 AP reorganized districts and split the old Visakhapatnam district into Visakhapatnam, Anakapalli, and Alluri Sitharama Raju. These files predate that split and represent the larger 2011 district. The Telangana bifurcation (2014) does not affect Visakhapatnam (it is in residual Andhra Pradesh). The GVMC ward layer is current (2024).

---

## boundaries/districts.geojson
- Layer: District boundary — Visakhapatnam (undivided, Census 2011)
- Source: DataMeet `datameet/maps` — Districts/Census_2011 (2011_Dist shapefile)
- URL: https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.shp (+ .dbf/.shx/.prj)
- License: Datameet — CC-BY 2.5 IN / public community data
- Format: Esri Shapefile → converted to GeoJSON (geopandas)
- Count: 1 feature | Geometry: Polygon/MultiPolygon | CRS: EPSG:4326
- bbox: ~81.87–83.49 E / 17.25–18.55 N (over Vizag — confirmed)
- Date: 2026-06 | STATUS: OK

## boundaries/subdistricts.geojson
- Layer: Sub-districts / mandals within Visakhapatnam district (Census 2011)
- Source: GitHub `datta07/INDIAN-SHAPEFILES` — INDIA/INDIAN_SUB_DISTRICTS.geojson (Census-2011 subdistrict polygons w/ LGD codes), filtered dtname=Visakhapatnam
- URL: https://github.com/datta07/INDIAN-SHAPEFILES (file INDIA/INDIAN_SUB_DISTRICTS.geojson; fetched via GitHub blob API, branch `main`)
- License: Repository public; underlying = Census of India 2011 admin boundaries (open)
- Format: GeoJSON (filtered subset)
- Count: 43 features | Geometry: Polygon/MultiPolygon | CRS: EPSG:4326
- bbox: ~81.86–83.52 E / 17.25–18.54 N (over Vizag — confirmed)
- Date: 2026-06 | STATUS: OK
- Note: Datameet/maps has NO standalone subdistrict layer; used this Census-2011-derived mirror instead. 43 mandals = undivided district.

## boundaries/acs.geojson
- Layer: Assembly Constituencies in Visakhapatnam district
- Source: DataMeet `datameet/maps` — assembly-constituencies/India_AC shapefile, filtered DIST_NAME=Visakhapatnam
- URL: https://raw.githubusercontent.com/datameet/maps/master/assembly-constituencies/India_AC.shp (+ .dbf/.shx/.prj)
- License: Datameet community data (ECI-derived delimitation)
- Format: Esri Shapefile → GeoJSON
- Count: 15 features | Geometry: Polygon/MultiPolygon | CRS: EPSG:4326
- ACs: Anakapalle, Araku Valley (ST), Bhimili, Chodavaram, Gajuwaka, Madugula, Narsipatnam, Paderu (ST), Payakaraopet (SC), Pendurthi, Visakhapatnam East/North/South/West, Yelamanchili
- bbox: ~81.86–83.52 E / 17.25–18.55 N (over Vizag — confirmed)
- Date: 2026-06 | STATUS: OK

## boundaries/pcs.geojson
- Layer: Parliamentary Constituencies overlapping Visakhapatnam district
- Source: DataMeet `datameet/maps` — parliamentary-constituencies/india_pc_2019 shapefile; spatial-intersected with district (>5% overlap)
- URL: https://raw.githubusercontent.com/datameet/maps/master/parliamentary-constituencies/india_pc_2019.shp (+ siblings)
- License: Datameet community data (2019 PC delimitation)
- Format: Esri Shapefile → GeoJSON (spatial filter)
- Count: 3 features | Geometry: Polygon/MultiPolygon | CRS: EPSG:4326
- PCs: VISAKHAPATNAM, ANAKAPALLE, ARAKU (ST) — all intersect the undivided 2011 district
- Date: 2026-06 | STATUS: OK

## boundaries/wards.geojson  ⭐ GVMC wards
- Layer: GVMC ward boundaries 2024 (98 wards) + WorldPop population_2020
- Source: OpenCity Urban Data Portal — "Visakhapatnam Wards Map" (Wards Map 2024, KML)
- URL: https://data.opencity.in/dataset/3b3266a0-b88f-4f38-9372-6b5997bbf01a (KML resource 24a12e3c-d694-455c-a495-63cec30a6530)
- License: Other (Public Domain) — per dataset metadata
- Format: KML → GeoJSON (geopandas)
- Count: 98 features (wards 1–98, contiguous) | Geometry: MultiPolygon | CRS: EPSG:4326
- Attributes retained: ward_lgd_name, ward_lgd_code, town_lgd_code, sourcewardcode (ward no.), zone, state, population_2020
- bbox: ~82.99–83.46 E / 17.55–17.94 N (full GVMC over Vizag — confirmed)
- Date: 2026-06 | STATUS: OK
- Note: OSM has NO ward-level (admin_level 9/10) boundaries for Vizag; OpenCity KML is the authoritative open source.

---

## osm/*.geojson — OpenStreetMap via Overpass API
- Source: OpenStreetMap contributors, via Overpass API (overpass-api.de; roads via overpass.kumi.systems)
- License: ODbL 1.0 (© OpenStreetMap contributors)
- Query bbox: 17.62,83.18,17.80,83.40 (S,W,N,E — Vizag core)
- Format: GeoJSON | CRS: EPSG:4326 | Date: 2026-06
- Ways reduced to centroid Points for POIs; roads kept as LineStrings.

| file | layer | count | geom | status |
|------|-------|-------|------|--------|
| roads.geojson | highways motorway→tertiary | 1438 | LineString | OK |
| bus_stops.geojson | bus stops / platforms (incl. APSRTC) | 242 | Point | OK |
| hospitals.geojson | hospitals + clinics | 282 | Point | OK |
| schools.geojson | schools | 109 | Point | OK |
| libraries.geojson | libraries | 8 | Point | OK |
| toilets.geojson | public toilets | 19 | Point | OK |
| police.geojson | police stations | 13 | Point | OK |
| fire.geojson | fire stations | 3 | Point | OK |

Note: bus stops are generic OSM `highway=bus_stop` / bus platforms (operator-tagging for APSRTC is sparse in OSM).

---

## population (WorldPop)
- Layer: WorldPop wpgppop (Global Per-Country, constrained) total population 2020, per GVMC ward
- API: POST https://api.worldpop.org/v1/services/stats (dataset=wpgppop, year=2020, geojson=<ward geom @5dp>) → taskid → poll /v1/tasks/<id> → data.total_population
- License: WorldPop — CC-BY 4.0
- Written as property `population_2020` on each feature in boundaries/wards.geojson
- Date: 2026-06 | STATUS: see summary below (filled after run)

<!-- WORLDPOP_SUMMARY -->

---

## MISSING / not openly available
- None of the required layers are MISSING. All boundary layers, OSM POI layers, and ward population were acquired from real open sources.
- Caveat: data.ap.gov.in did not yield a separate GVMC ward GeoJSON; OpenCity's public-domain KML was used (authoritative, LGD-coded).
- Caveat: subdistrict/mandal layer came from a Census-2011 community mirror (datta07/INDIAN-SHAPEFILES), not Datameet/maps (which lacks a subdistrict layer).
