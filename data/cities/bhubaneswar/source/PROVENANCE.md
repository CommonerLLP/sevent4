# Bhubaneswar — Geospatial Source Provenance

City: Bhubaneswar | State: Odisha | District: Khordha | Municipal body: BMC (Bhubaneswar Municipal Corporation, 67 wards) | Dev authority: BDA
City bbox (approx): 85.75–85.92 E, 20.20–20.40 N
Acquisition date: 2026-06
CRS: EPSG:4326 (lon/lat, urn:ogc:def:crs:OGC:1.3:CRS84) for all layers.

## Boundaries

### districts.geojson
- Source: DataMeet `maps` (Census 2011 districts), filtered to Khordha, Odisha.
- URL: https://raw.githubusercontent.com/datameet/maps/master/docs/data/geojson/dists11.geojson
- License: DataMeet Community (CC-BY 2.5 IN / ODbL-style community license)
- Format: GeoJSON | Count: 1 (Khordha) | Geometry: Polygon | CRS: EPSG:4326
- STATUS: OK. bbox 84.94,19.68 → 86.08,20.43 covers Bhubaneswar/Khordha.

### subdistricts.geojson
- Source: datta07/INDIAN-SHAPEFILES (Census 2011 sub-district/tehsil boundaries), Odisha set, filtered to Khordha district (dtname=Khordha).
- URL: https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/STATES/ORISSA/ODISHA_SUBDISTRICTS.geojson
- License: Open (Census 2011 derived; repo redistributes openly)
- Format: GeoJSON | Count: 22 sub-districts | Geometry: Polygon | CRS: EPSG:4326
- STATUS: OK. Includes "Bhubaneswar (M.Corp.)", Khandagiri, Lingaraj, Mancheswar, Chandaka etc. DataMeet `maps` has no sub-district layer; this Census-2011-derived repo used as the open substitute.

### acs.geojson (Assembly Constituencies)
- Source: DataMeet `maps` assembly constituencies, filtered to PC_NAME = BHUBANESWAR.
- URL: https://raw.githubusercontent.com/datameet/maps/master/docs/data/geojson/ac.geojson
- License: DataMeet Community
- Format: GeoJSON | Count: 6 ACs | Geometry: Polygon | CRS: EPSG:4326
- ACs: Jatani, Bhubaneswar(Uttar), Bhubaneswar(Madhya), Ekamra-Bhubaneshwar, Begunia, Khurda (all in Khordha dist, Bhubaneswar PC). The 3 Bhubaneswar(Uttar/Madhya/Ekamra) ACs cover the city core.
- STATUS: OK. bbox 85.20,19.85 → 85.90,20.44 covers the city.

### pcs.geojson (Parliamentary Constituency)
- Source: DataMeet `maps` parliamentary constituencies (PC_14), filtered to PC_NAME = Bhubaneswar, ST_NAME = OD.
- URL: https://raw.githubusercontent.com/datameet/maps/master/docs/data/geojson/pc_14.geojson
- License: DataMeet Community
- Format: GeoJSON | Count: 1 (Bhubaneswar PC) | Geometry: Polygon | CRS: EPSG:4326
- STATUS: OK. bbox 85.20,19.84 → 85.89,20.43.

### wards.geojson (BMC wards) — PRIMARY CIVIC LAYER
- Source: DataMeet `Municipal_Spatial_Data`, Bhubaneswar/Wards.GeoJSON (BMC official ward GIS with attributes).
- URL: https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bhubaneswar/Wards.GeoJSON
- License: DataMeet Community
- Format: GeoJSON | Count: 67 wards | Geometry: Polygon | CRS: EPSG:4326
- Attributes retained: wardno (W1–W67), municipalzone, nameofthecorporator, numberofhouseholds, totalwardpopulation (Census), SC/ST breakdowns, ward officer.
- Enriched: `population_2020` = WorldPop wpgppop 2020 per ward (see Population).
- STATUS: OK. 67 wards, matches BMC. bbox 85.7533,20.2113 → 85.9034,20.3664 — precisely over the city.

### bmc_boundary.geojson (bonus)
- Source: DataMeet Municipal_Spatial_Data, Bhubaneswar/BMC Boundary.GeoJSON
- URL: https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bhubaneswar/BMC%20Boundary.GeoJSON
- License: DataMeet Community | Format: GeoJSON | Count: 1 | Geometry: Polygon | CRS: EPSG:4326 | STATUS: OK.

### bda_boundary.geojson (bonus)
- Source: DataMeet Municipal_Spatial_Data, Bhubaneswar/BDA_Boundary.GeoJSON (Bhubaneswar Development Authority planning area).
- URL: https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bhubaneswar/BDA_Boundary.GeoJSON
- License: DataMeet Community | Format: GeoJSON | Count: 1 | Geometry: Polygon | CRS: EPSG:4326 | STATUS: OK.

## OSM (osm/*.geojson)
- Source: OpenStreetMap via Overpass API (https://overpass-api.de/api/interpreter)
- Query bbox (S,W,N,E): 20.18,85.73,20.42,85.94
- License: ODbL 1.0 (© OpenStreetMap contributors)
- Date: 2026-06 | CRS: EPSG:4326
- roads.geojson — 23012 LineString — STATUS: OK (all highway=* ways)
- bus_stops.geojson — 30 Point — STATUS: OK (highway=bus_stop + bus platforms; Mo Bus stop coverage in OSM is sparse)
- hospitals.geojson — 197 (185 Point, 12 Polygon) — STATUS: OK (amenity=hospital/clinic)
- schools.geojson — 60 (30 Point, 30 Polygon) — STATUS: OK (amenity=school/college)
- libraries.geojson — 4 (1 Point, 3 Polygon) — STATUS: OK (amenity=library)
- toilets.geojson — 15 (12 Point, 3 Polygon) — STATUS: OK (amenity=toilets)
- police.geojson — 6 (4 Point, 2 Polygon) — STATUS: OK (amenity=police)
- fire.geojson — 2 Polygon — STATUS: OK (amenity=fire_station; sparse in OSM)

## Population (WorldPop)
- Source: WorldPop Global Project Population Data (dataset=wpgppop), year=2020, 100m resolution.
- Method: per-ward POST to https://api.worldpop.org/v1/services/stats (geometry rounded to 5dp), poll https://api.worldpop.org/v1/tasks/<taskid> to completion, read data.total_population.
- License: CC-BY 4.0 (WorldPop, University of Southampton)
- Output: `population_2020` property on each feature in wards.geojson.
- See run summary appended below.
- STATUS: see RUN SUMMARY.

## MISSING / NOTES
- No openly-available dedicated sub-district layer in DataMeet `maps`; substituted Census-2011-derived datta07/INDIAN-SHAPEFILES (real geometry, validated over Khordha). Not fabricated.
- Mo Bus (BSCL) GTFS / official stop feed not openly downloaded; OSM bus_stop points used as proxy (30 stops — under-represents the real Mo Bus network).
- Odisha state open-data portal (odisha.data.gov.in) was not the ward source; the DataMeet Municipal_Spatial_Data BMC official ward GIS (67 wards, with corporator/population attributes) was authoritative and used instead.
