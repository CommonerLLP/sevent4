# Pune — Source Data Provenance

City: Pune, Maharashtra. District: Pune. Municipal body: PMC (Pune Municipal Corporation); parastatal PMRDA.
City bbox used for OSM: S 18.40, W 73.70, N 18.65, E 74.00. Acquisition date: 2026-06.
All GeoJSON outputs are EPSG:4326 (CRS84 / lon-lat). Every layer below was downloaded from a real URL and validated (feature count, geometry type, CRS, bbox over Pune).

## Boundaries

| Layer | File | Source | URL | License | Format | Features | CRS | Date | Status / Note |
|---|---|---|---|---|---|---|---|---|---|
| Districts | boundaries/districts.geojson | DataMeet maps (Census 2011 districts) | https://raw.githubusercontent.com/datameet/maps/master/docs/data/geojson/dists11.geojson | CC-BY 2.5 IN | GeoJSON | 1 | EPSG:4326 | 2026-06 | GOT. Filtered to DISTRICT=Pune, ST_NM=Maharashtra. bbox 73.32–75.16 E, 17.89–19.39 N (covers full Pune district incl. city). |
| Sub-districts (taluks) | boundaries/subdistricts.geojson | datta07/INDIAN-SHAPEFILES (Census 2011 subdistricts, MH) | https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/STATES/MAHARASHTRA/MAHARASHTRA_SUBDISTRICTS.geojson | Open (Census 2011 derivative) | GeoJSON | 14 | EPSG:4326 | 2026-06 | GOT. Filtered dtname=Pune → 14 taluks (Junnar, Ambegaon, Shirur, Khed, Mawal, Mulshi, Haveli, Pune City, Daund, Purandhar, Velhe, Bhor, Baramati, Indapur). DataMeet maps has no taluk layer; used this mirror of Census 2011 LGD subdistricts. |
| Assembly Constituencies | boundaries/acs.geojson | DataMeet maps (India_AC shapefile, pre-delimitation set) | https://raw.githubusercontent.com/datameet/maps/master/assembly-constituencies/India_AC.shp | CC-BY 2.5 IN | Shapefile → GeoJSON | 21 | EPSG:4326 | 2026-06 | GOT. Converted via pyshp. Filtered ST_NAME=MAHARASHTRA, DIST_NAME=PUNE → 21 ACs (AC 195–215). |
| Parliamentary Constituencies | boundaries/pcs.geojson | DataMeet maps (india_pc_2019 simplified) | https://raw.githubusercontent.com/datameet/maps/master/parliamentary-constituencies/india_pc_2019_simplified.geojson | CC-BY 2.5 IN | GeoJSON | 4 | EPSG:4326 | 2026-06 | GOT. 4 PCs covering Pune-district ACs: Pune, Baramati, Maval, Shirur (PC names derived from the Pune-district AC→PC mapping). |
| PMC Wards (Prabhags) | boundaries/wards.geojson | DataMeet Pune chapter (Pune_wards, electoral) | https://raw.githubusercontent.com/datameet/Pune_wards/master/GeoData/pune-electoral-wards.geojson | CC-BY-SA 2.5 IN | GeoJSON | 76 | EPSG:4326 | 2026-06 | GOT (PARTIAL on vintage — see note). 76 electoral prabhags (2012 delimitation), traced from PMC prabhag-rachna PDFs by SeerMaps. bbox 73.75–73.96 E, 18.43–18.62 N (PMC city core). Carries `population_2020` from WorldPop. |

### Ward note (the "~166 wards post-2017" question)
The task referenced ~166 wards post-2017-merger. "166" is the **corporator** count, not a polygon set. The 2017 PMC election used 41 multi-member panels (prabhags), each electing ~4 corporators (~162–166 seats). No openly-available 4326 GeoJSON of the 2017/2022 prabhags exists; OpenCity (data.opencity.in/dataset/pune-wards-info) carries only KML (2017 = 41, 2022 = 58, 2012 = 76, 2025 = 41). The most granular, clean, ward-level **boundary GeoJSON** openly available is the DataMeet 76-prabhag (2012) set, used here as wards.geojson. PMC's own GIS portal (gis.pmc.gov.in) does not expose an open download.

## OSM Geolayers (Overpass API, city bbox)

Endpoint: https://overpass-api.de/api/interpreter (POST). License: ODbL (OpenStreetMap). CRS EPSG:4326. Date 2026-06. All STATUS=GOT.

| Layer | File | Query (amenity/tag) | Features | Geom types |
|---|---|---|---|---|
| Roads | osm/roads.geojson | highway = motorway…residential/unclassified | 47865 | LineString |
| Pune Metro | osm/metro.geojson | railway=subway / construction=subway / route=subway / subway stations | 251 | LineString, Point |
| Bus stops (PMPML) | osm/bus_stops.geojson | highway=bus_stop, public_transport=platform[bus] | 618 | Point |
| Hospitals | osm/hospitals.geojson | amenity=hospital | 713 | Point, Polygon |
| Schools | osm/schools.geojson | amenity=school | 327 | Point, Polygon |
| Libraries | osm/libraries.geojson | amenity=library | 90 | Point, Polygon |
| Toilets | osm/toilets.geojson | amenity=toilets | 73 | Point, Polygon |
| Police | osm/police.geojson | amenity=police | 65 | Point, Polygon |
| Fire | osm/fire.geojson | amenity=fire_station | 22 | Point, Polygon |

OSM bbox checks: all layers fall within/around 73.66–74.04 E, 18.36–18.68 N (roads slightly overshoot the query box where ways cross the boundary — expected). Metro station names verified as real Pune Metro (Range Hills, Garware College, Hadapsar, Civil Court, etc.).

## Population

WorldPop wpgppop (Global Project Population, 100m, year 2020). API: https://api.worldpop.org/v1/services/stats (POST) + task polling at /v1/tasks/<taskid>. Computed per ward and written to wards.geojson property `population_2020`. See ward note for vintage caveat (2012 prabhag polygons). Totals reported in run summary.

## MISSING / not openly available
- 2017/2022 prabhag (41/58-panel) boundaries as GeoJSON — only KML on OpenCity; not converted (out of stdlib-clean scope, vintage uncertain post-delimitation litigation). PMC GIS portal has no open download.
- PMRDA jurisdiction boundary — no open authoritative GeoJSON located.
