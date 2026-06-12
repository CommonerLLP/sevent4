# Kolkata — Source Layer Provenance

City: Kolkata | State: West Bengal | District: Kolkata | Municipal body: KMC (Kolkata Municipal Corporation), 144 wards / 16 boroughs.
Acquired: 2026-06. CRS for all layers: EPSG:4326 (urn:ogc:def:crs:OGC:1.3:CRS84). bbox sanity: ~88.2–88.5 E, 22.4–22.7 N (confirmed per layer).

## Boundaries

| Layer | Source | URL | License | Format | Features | CRS | Date | Status | Note |
|-------|--------|-----|---------|--------|----------|-----|------|--------|------|
| districts | DataMeet maps (Census 2011) | https://raw.githubusercontent.com/datameet/maps/master/docs/data/geojson/dists11.geojson | CC-BY-SA 2.5 IN | GeoJSON | 1 | 4326 | 2026-06 | got | Filtered DISTRICT=Kolkata. bbox 88.27–88.41 / 22.50–22.63. |
| subdistricts | Derived (KMC boroughs) from ward dissolve | (see wards source) + KMC published ward→borough map | CC-BY-SA 2.5 IN (derived) | GeoJSON | 13 | 4326 | 2026-06 | partial | Kolkata district has NO census sub-districts/CD-blocks (wholly urban). Block proxy = 16 KMC boroughs, dissolved from ward polygons. 13 of 16 present; boroughs XIV/XV/XVI (wards 142/143/144) missing because those ward geometries are absent in the open ward source. |
| acs | DataMeet maps (Assembly Constituencies) | https://raw.githubusercontent.com/datameet/maps/master/docs/data/geojson/ac.geojson | CC-BY-SA 2.5 IN | GeoJSON | 11 | 4326 | 2026-06 | got | Filtered DIST_NAME=KOLKATA: ACs 158–168 (Kolkata Port, Bhabanipur, Rashbehari, Ballygunge, Chowringhee, Entally, Beleghata, Jorasanko, Shyampukur, Maniktala, Kashipur-Belgachhia). KMC area also overlaps a few neighbouring ACs (Jadavpur/Behala/Kasba) not in Kolkata district. |
| pcs | DataMeet maps (Parliamentary Constituencies 2014) | https://raw.githubusercontent.com/datameet/maps/master/docs/data/geojson/pc_14.geojson | CC-BY-SA 2.5 IN | GeoJSON | 2 | 4326 | 2026-06 | got | Filtered PC_NAME contains "Kolkata": Kolkata Uttar, Kolkata Dakshin. |
| wards | DataMeet Municipal_Spatial_Data (KMC wards, via J. Meyers/DataMeet thread) | https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Kolkata/kolkata.geojson | CC-BY-SA 2.5 IN | GeoJSON | 141 | 4326 | 2026-06 | partial | KMC has 144 wards; this open source covers wards 1–141. Wards 142, 143, 144 (newer Joka / Garden Reach additions) are MISSING — no openly licensed geometry found (checked OpenCity, DataMeet, GitHub code/repo search). population_2020 added per ward from WorldPop. |

## Sub-district note
The Census of India does not subdivide Kolkata district into sub-districts (tehsils/CD-blocks); it is treated as a single fully-urban unit. The administrative tier directly below the district here is the KMC borough (16 boroughs). `subdistricts.geojson` therefore holds KMC boroughs (block proxy), dissolved from ward polygons using the standard published KMC ward→borough mapping.

## OSM geolayers (Overpass API)
Source: OpenStreetMap via Overpass API. License: ODbL 1.0. Format: GeoJSON, EPSG:4326. Date: 2026-06.
Query bbox: S22.40, W88.20, N22.70, E88.50 (covers KMC + immediate periphery).

| Layer | Overpass filter | Features | Geom | Status |
|-------|-----------------|----------|------|--------|
| roads | highway in {motorway,trunk,primary,secondary,tertiary} | 5641 | LineString | got |
| metro_lines | railway=subway | 226 | LineString | got |
| metro_stations | railway=station + station=subway | 56 | Point | got |
| bus_stops | highway=bus_stop | 502 | Point | got |
| hospitals | amenity=hospital / healthcare=hospital | 261 | Point | got |
| schools | amenity=school | 93 | Point | got |
| libraries | amenity=library | 7 | Point | got |
| toilets | amenity=toilets | 60 | Point | got |
| police | amenity=police | 30 | Point | got |
| fire | amenity=fire_station | 3 | Point | got |

Roads restricted to major classes to keep file size reasonable; residential/service streets intentionally excluded.

## Population (WorldPop)
Source: WorldPop wpgppop (Global per-pixel population), year 2020, via https://api.worldpop.org/v1/services/stats (POST, per-ward polygon, 5-dp coords) → task poll → data.total_population.
Written onto `boundaries/wards.geojson` property `population_2020` (per ward). License: CC-BY 4.0 (WorldPop).
Coverage: wards 1–141 (the 141 wards with geometry). MultiPolygon wards summed across constituent polygons (API accepts Polygons only).

## MISSING / gaps
- Ward geometries for KMC wards 142, 143, 144 — no open source located.
- KMC boroughs XIV, XV, XVI — absent because they consist solely of wards 142–144.
- Census sub-districts for Kolkata — none exist (genuine; not a data gap).
