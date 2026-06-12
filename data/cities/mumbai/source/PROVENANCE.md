# Mumbai — Source Data Provenance

City: **Mumbai**, Maharashtra. Districts: Mumbai City + Mumbai Suburban.
Municipal body: MCGM / BMC (Brihanmumbai Municipal Corporation) — 24 administrative wards, 227 electoral wards (prabhags).
Acquisition date: **2026-06**. All geometry CRS: **EPSG:4326 (WGS84 / CRS84)** unless noted.
City bbox sanity window: ~72.7–73.1 E, 18.8–19.3 N. Every saved layer was validated to fall within this window.

| Layer | File | Source | URL | License | Format | Features | CRS | Status | Note |
|-------|------|--------|-----|---------|--------|----------|-----|--------|------|
| Districts | boundaries/districts.geojson | DataMeet maps (Census 2011 districts shapefile) | https://github.com/datameet/maps/tree/master/Districts/Census_2011 | CC-BY 2.5 IN | GeoJSON | 2 | EPSG:4326 | got | Mumbai + Mumbai Suburban; converted from shapefile with stdlib parser. |
| Sub-districts (taluka) | — | DataMeet / OSM / geoBoundaries | — | — | — | 0 | — | missing | No distinct open taluka polygons for Mumbai City/Suburban. OSM admin_level 6/7/8 inside the city return only neighbouring bodies (Thane, Navi Mumbai, Mira-Bhayander, Vasai-Virar); geoBoundaries ADM3 collapses to "Mumbai" + "Mumbai Suburban" (= district level). The 24 BMC admin wards (wards_admin24.geojson) serve as the intra-district subdivision. |
| Assembly constituencies (AC) | boundaries/acs.geojson | DataMeet maps (India_AC, 2008 delimitation) | https://github.com/datameet/maps/tree/master/assembly-constituencies | CC-BY 2.5 IN | GeoJSON | 36 | EPSG:4326 | got | AC 152–187, all 6 Mumbai PCs; converted from shapefile. |
| Parliamentary constituencies (PC) | boundaries/pcs.geojson | DataMeet maps (india_pc_2019_simplified) | https://github.com/datameet/maps/tree/master/parliamentary-constituencies | CC-BY 2.5 IN | GeoJSON | 6 | EPSG:4326 | got | Mumbai North, North-West, North-East, North-Central, South-Central, South. |
| Electoral wards (227) | boundaries/wards.geojson | DataMeet Municipal_Spatial_Data (BMC electoral wards 2017) | https://github.com/datameet/Municipal_Spatial_Data/tree/master/Mumbai | CC-BY 4.0 | GeoJSON | 227 | EPSG:4326 | got | Prabhag-level; carries POPULATION (census), Corporator, Reserve, SC/ST pop. `population_2020` added from WorldPop. |
| Administrative wards (24) | boundaries/wards_admin24.geojson | DataMeet Municipal_Spatial_Data (BMC_Wards) | https://github.com/datameet/Municipal_Spatial_Data/tree/master/Mumbai | CC-BY 4.0 | GeoJSON | 24 | EPSG:4326 | got | The 24 MCGM admin wards (A, B, … R-North etc.). |
| Roads (major) | osm/roads.geojson | OpenStreetMap via Overpass | https://overpass-api.de/api/interpreter | ODbL | GeoJSON | 6844 | EPSG:4326 | got | highway = motorway/trunk/primary/secondary. |
| Rail/metro lines | osm/rail_lines.geojson | OpenStreetMap via Overpass | https://overpass-api.de/api/interpreter | ODbL | GeoJSON | 2329 | EPSG:4326 | got | railway = rail/subway/light_rail/monorail. |
| Rail/metro stations | osm/rail_stations.geojson | OpenStreetMap via Overpass | https://overpass-api.de/api/interpreter | ODbL | GeoJSON | 175 | EPSG:4326 | got | station/halt + subway. |
| Bus stops | osm/bus_stops.geojson | OpenStreetMap via Overpass | https://overpass-api.de/api/interpreter | ODbL | GeoJSON | 2631 | EPSG:4326 | got | highway = bus_stop. |
| Hospitals | osm/hospitals.geojson | OpenStreetMap via Overpass | https://overpass-api.de/api/interpreter | ODbL | GeoJSON | 1213 | EPSG:4326 | got | amenity = hospital (node + way centroid). |
| Schools | osm/schools.geojson | OpenStreetMap via Overpass | https://overpass-api.de/api/interpreter | ODbL | GeoJSON | 702 | EPSG:4326 | got | amenity = school. |
| Libraries | osm/libraries.geojson | OpenStreetMap via Overpass | https://overpass-api.de/api/interpreter | ODbL | GeoJSON | 47 | EPSG:4326 | got | amenity = library. |
| Public toilets | osm/toilets.geojson | OpenStreetMap via Overpass | https://overpass-api.de/api/interpreter | ODbL | GeoJSON | 370 | EPSG:4326 | got | amenity = toilets. |
| Police | osm/police.geojson | OpenStreetMap via Overpass | https://overpass-api.de/api/interpreter | ODbL | GeoJSON | 132 | EPSG:4326 | got | amenity = police. |
| Fire stations | osm/fire.geojson | OpenStreetMap via Overpass | https://overpass-api.de/api/interpreter | ODbL | GeoJSON | 44 | EPSG:4326 | got | amenity = fire_station. |
| Population (WorldPop) | merged onto wards.geojson as `population_2020` | WorldPop Global Project Population (wpgppop 2020) | https://api.worldpop.org/v1/services/stats | CC-BY 4.0 | field on wards | see below | n/a | PENDING | Per-ward zonal sum via WorldPop stats API (POST geojson, poll taskid). MultiPolygon wards split into component polygons and summed (API accepts only Polygons). |

## OSM bbox window used
Overpass queries used S,W,N,E = `18.88, 72.77, 19.30, 73.05`.

## Notes / caveats
- DataMeet district & AC layers were shipped only as ESRI shapefiles; this environment had no GDAL/fiona/pyshp, so a pure-stdlib shapefile+DBF reader was used to convert to GeoJSON (.prj confirmed GCS_WGS_1984).
- AC layer is 2008 delimitation; PC layer is the 2019 simplified set — both are the current open DataMeet releases.
- WorldPop totals are model-based gridded estimates (100 m), not census counts. The wards file also retains the census `POPULATION` attribute from the BMC 2017 dataset for comparison.
