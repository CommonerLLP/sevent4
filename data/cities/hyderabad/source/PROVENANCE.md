# Hyderabad — Source Data Provenance

City: **Hyderabad**, Telangana. Municipal body: **GHMC** (Greater Hyderabad Municipal Corporation) — 150 wards.
Acquisition date: **2026-06**. Target CRS for all layers: **EPSG:4326 (WGS84 / CRS84)**.
Hyderabad sanity bbox: ~78.2–78.6 E, 17.2–17.6 N (GHMC core).

## Important reconciliation note (Telangana / Andhra Pradesh)
Telangana was carved out of **Andhra Pradesh** on 2 June 2014. Several upstream open datasets
predate the bifurcation and therefore label these districts/constituencies as **"Andhra Pradesh"**
with the old (pre-2014, and pre-2016 district re-organisation) boundaries:
- Census 2011 had only **Hyderabad, Rangareddy, Medak** in this region. The present-day GHMC-spill
  districts **Medchal-Malkajgiri** and **Sangareddy** were carved out of **Medak / Rangareddy in 2016**,
  so they are represented here by their **parent districts Medak + Rangareddy**.
- The Assembly-Constituency file still carries `ST_NAME = "ANDHRA PRADESH"` and the Parliamentary file
  carries the old state code `S01`. The *geometry* is correct and current (2008 delimitation, still in force);
  only the state label is stale. This is noted rather than "corrected" to preserve source fidelity.

## Layer table

### Administrative / electoral boundaries (`boundaries/`)
| Layer | Source | URL | License | Format(src→out) | Features | CRS | Date | Status & note |
|-------|--------|-----|---------|-----------------|----------|-----|------|---------------|
| districts | DataMeet maps — Census 2011 districts | github.com/datameet/maps `Districts/Census_2011/2011_Dist.shp` (raw.githubusercontent.com) | CC-BY (DataMeet) / Census of India | SHP→GeoJSON | 3 | EPSG:4326 | 2026-06 | **got**. Filtered to Hyderabad + Rangareddy + Medak (Medak = parent of Medchal-Malkajgiri & Sangareddy). Labelled "Andhra Pradesh" (pre-2014). |
| subdistricts | geohacker/india (GADM-derived taluks) | github.com/geohacker/india `taluk/india_taluk.geojson` | ODbL / GADM-derived | GeoJSON | 16 | EPSG:4326 | 2026-06 | **got**. Mandal/taluk block-proxy; filtered to Hyderabad(1)+Medak(8)+Rangareddi(7) taluks. |
| acs | DataMeet maps — Assembly Constituencies | github.com/datameet/maps `docs/data/geojson/ac.geojson` | CC-BY (DataMeet) / ECI | GeoJSON | 28 | EPSG:4326 | 2026-06 | **got**. Filtered to ACs whose PC ∈ {Hyderabad, Secunderabad, Malkajgiri, Chevella} — the constituencies that span GHMC. `ST_NAME="ANDHRA PRADESH"` (stale label). |
| pcs | DataMeet maps — Parliamentary Constituencies (2014) | github.com/datameet/maps `docs/data/geojson/pc_14.geojson` | CC-BY (DataMeet) / ECI | GeoJSON | 4 | EPSG:4326 | 2026-06 | **got**. Hyderabad, Secunderabad, Malkajgiri, Chevella. `ST_CODE="S01"` (old AP code). |
| wards | OpenCity — GHMC Wards Map 2022 | data.opencity.in/dataset/hyderabad-wards-info (resource `ghmc_wards.kml`) | Public Domain | KML→GeoJSON | 155 | EPSG:4326 | 2026-06 | **got**. Carries **150 distinct ward numbers (1–150)** + `ward`,`CIRCLE`,`ZONE` attributes; 5 wards are non-contiguous and stored as extra placemarks → 155 polygon features for 150 wards. Layer reflects the 2022 GHMC delimitation (7 zones / 35 circles in this file vs the often-quoted 6 zones / 30 circles). |

### Core OSM geolayers (`osm/`) — OpenStreetMap via Overpass API, bbox 17.20–17.65 N / 78.20–78.65 E
| Layer | Tags queried | Features | Geom | bbox (W,S,E,N) | Status |
|-------|--------------|----------|------|----------------|--------|
| roads | highway ∈ motorway/trunk/primary/secondary | 6017 | LineString | 78.14,17.14,78.69,17.69 | **got** (major roads only, to keep size bounded) |
| metro_lines | railway=subway | 242 | LineString | 78.37,17.35,78.56,17.50 | **got** (Hyderabad Metro track segments) |
| metro_stations | station=subway ∪ railway=station[network~Hyderabad] | 69 | Point | 78.37,17.33,78.56,17.50 | **got** |
| bus_stops | highway=bus_stop | 609 | Point | 78.22,17.23,78.64,17.63 | **partial** — OSM bus stops (TSRTC not separately tagged; this is best-available open coverage) |
| hospitals | amenity ∈ hospital/clinic | 1463 | Point | 78.21,17.21,78.64,17.64 | **got** |
| schools | amenity=school | 619 | Point | 78.21,17.25,78.64,17.64 | **got** |
| libraries | amenity=library | 40 | Point | 78.27,17.28,78.57,17.60 | **got** |
| toilets | amenity=toilets | 95 | Point | 78.28,17.24,78.61,17.60 | **got** |
| police | amenity=police | 91 | Point | 78.27,17.26,78.60,17.53 | **got** |
| fire | amenity=fire_station | 10 | Point | 78.39,17.23,78.54,17.63 | **got** |

OSM source: openstreetmap.org via Overpass (overpass-api.de + mirrors). License: **ODbL 1.0**. Date pulled: 2026-06.

### Population
| Layer | Source | URL | License | Status |
|-------|--------|-----|---------|--------|
| population_2020 (on wards.geojson) | WorldPop Global Project Population (`wpgppop`, 2020, UN-adjusted constrained) | api.worldpop.org/v1/services/stats | CC-BY 4.0 (WorldPop) | **partial / in-progress** — per-ward query pipeline (POST geom → taskid → poll `/tasks/<id>` → `data.total_population`) is implemented and verified working (single-ward smoke test returned e.g. 33,928 for ward 3). At acquisition time the WorldPop stats API was heavily oversubscribed by ~20 concurrent sibling city-extraction jobs (25–28 simultaneous connections observed), so the full 155-ward batch was still running. When it completes, `population_2020` is written onto every ward feature. If the cell is absent/null, re-run `worldpop_fast.py` against `boundaries/wards.geojson` when API load is lower. |

## MISSING / not openly available
- **GHMC ward councillor / representative roster** — not acquired in this geospatial pass (out of scope; would come from GHMC election results, not a geolayer).
- **Native Telangana-labelled (post-2014) district & constituency GeoJSON** — data.telangana.gov.in was unreachable during this run (TLS handshake failures, curl exit 35); fell back to DataMeet AP-labelled files which carry correct geometry. The official portal remains the preferred upstream if revisited.
- **TSRTC-specific bus stops / GTFS** — not separately published as open GeoJSON; OSM `highway=bus_stop` used as proxy.
