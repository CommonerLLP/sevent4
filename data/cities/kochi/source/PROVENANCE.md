# PROVENANCE — Kochi (SevenT4 Civic Atlas)

City: **Kochi** | State: Kerala | District: Ernakulam
Municipal body: Kochi Municipal Corporation (officially 74 divisions/wards)
Atlas role: **Devolution control group** — Kerala is the People's Plan / strong fiscal-devolution counter-example.
bbox (target): ~76.20–76.40 E, 9.88–10.05 N
Acquisition date: **2026-06** | CRS: EPSG:4326 (WGS84 / CRS84) for all layers unless noted.

---

## Boundaries

### districts.geojson
- Source: DataMeet `maps` (Census 2011 district boundaries), filtered to Ernakulam.
- URL: https://raw.githubusercontent.com/datameet/maps/master/docs/data/geojson/dists11.geojson
- License: Open / CC-BY (DataMeet community data, derived from Census of India 2011).
- Format: GeoJSON | Count: 1 (Ernakulam) | Geometry: Polygon | CRS: EPSG:4326
- bbox: [76.168, 9.789, 76.840, 10.302]
- STATUS: **OK** — covers Kochi.

### subdistricts.geojson
- Source: geohacker/kerala taluk boundaries, filtered to DISTRICT=Ernakulam. (DataMeet maps has no taluk layer; the `divisions/kerala.topo.json` is only 3 broad regional divisions, not taluks — not usable.)
- URL: https://raw.githubusercontent.com/geohacker/kerala/master/geojsons/taluk.geojson
- License: Open community data (Kerala admin boundaries).
- Format: GeoJSON | Count: 7 taluks (Aluva, Kanayannur, Kochi, Kothamangalam, Kunnathunad, Muvattupuzha, Paravur) | Geometry: Polygon | CRS: EPSG:4326
- bbox: [76.167, 9.790, 76.839, 10.303]
- STATUS: **OK** — covers Kochi (Kochi + Kanayannur taluks contain the corporation).

### acs.geojson  (Assembly Constituencies)
- Source: DataMeet `maps` AC layer, filtered to DIST_NAME=Ernakulam.
- URL: https://raw.githubusercontent.com/datameet/maps/master/docs/data/geojson/ac.geojson
- License: Open / CC-BY (DataMeet).
- Format: GeoJSON | Count: 14 ACs (Aluva, Angamaly, Ernakulam, Kalamassery, Kochi, Kothamangalam, Kunnathunad(SC), Muvattupuzha, Paravur, Perumbavoor, Piravom, Thrikkakara, Thripunithura, Vypeen) | Geometry: Polygon | CRS: EPSG:4326
- bbox: [76.167, 9.789, 76.840, 10.303]
- STATUS: **OK** — Kochi/Ernakulam/Thrikkakara/Thripunithura cover the corporation.

### pcs.geojson  (Parliamentary Constituencies)
- Source: DataMeet `maps` PC 2019 simplified, filtered to Kerala PCs covering Kochi (Ernakulam + Chalakudy).
- URL: https://raw.githubusercontent.com/datameet/maps/master/parliamentary-constituencies/india_pc_2019_simplified.geojson
- License: Open / CC-BY (DataMeet).
- Format: GeoJSON | Count: 2 (Ernakulam PC — contains Kochi city; Chalakudy PC — northern Ernakulam) | Geometry: MultiPolygon | CRS: EPSG:4326
- bbox: [76.110, 9.789, 76.901, 10.436]
- STATUS: **OK** — Ernakulam PC is Kochi's parliamentary seat.

### wards.geojson  (Kochi Corporation divisions/wards)
- Source: DataMeet `Municipal_Spatial_Data` — Kochi ward polygons (KCH_wards). Delivered as newline-delimited GeoJSON; reassembled into a FeatureCollection.
- URL: https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Kochi/KCH_wards.geojson
- License: Open community data (DataMeet Municipal Spatial Data).
- Format: GeoJSON | Count: 77 features (71 carry Ward_No 1–71 + Ward_Name; 6 features have empty properties — likely water/island/sliver polygons) | Geometry: Polygon | CRS: EPSG:4326
- Properties: fid, Area, Ward_Name, Ward_No, Shape_Leng, Shape_Area, population_2020 (added)
- bbox: [76.2374, 9.8934, 76.3400, 10.0498] — squarely over Kochi corporation.
- NOTE: Official Kochi Corporation currently has **74 divisions**; this open dataset reflects an older/alternate delineation (71 numbered + 6 unattributed = 77 polygons). No authoritative open 74-division ward file was found openly (KSDI `opensdi.kerala.gov.in` hosts LSGD_Boundary_2021 behind a GeoNode viewer/login, not a direct open GeoJSON download). This is the best openly downloadable real ward geometry; geometry NOT fabricated.
- STATUS: **OK (with caveat on division count — 77 vs official 74)**.

### corporation_boundary.geojson  (bonus)
- Source: DataMeet `Municipal_Spatial_Data` — Kochi corporation outer boundary.
- URL: https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Kochi/KCH_Corporation_Boundary.geojson
- License: Open community data (DataMeet).
- Format: GeoJSON | Count: 1 | Geometry: Polygon | CRS: EPSG:4326 | bbox: [76.2374, 9.8897, 76.3400, 10.0498]
- STATUS: **OK**.

---

## OSM layers (osm/*.geojson)
- Source: OpenStreetMap via Overpass API (overpass-api.de / overpass.kumi.systems mirror).
- Query bbox (S,W,N,E): 9.86, 76.18, 10.07, 76.42 (Kochi city + small margin).
- License: **ODbL** (OpenStreetMap contributors).
- Format: GeoJSON | CRS: EPSG:4326 | Date: 2026-06.
- All bboxes confirmed over Kochi.

| Layer | File | Count | Geometry | Status |
|-------|------|------:|----------|--------|
| Roads | roads.geojson | 21070 | LineString | OK |
| Metro/rail lines | metro_rail.geojson | 153 | LineString | OK (Kochi Metro Blue Line + Phase II confirmed) |
| Metro/rail stations | metro_stations.geojson | 34 | Point | OK |
| Water Metro / ferry | water_metro.geojson | 126 | Point/Polygon | OK |
| Bus stops/stations | bus_stops.geojson | 1819 | Point | OK |
| Hospitals/clinics | hospitals.geojson | 375 | Point/Polygon | OK |
| Schools/colleges | schools.geojson | 617 | Point/Polygon | OK |
| Libraries | libraries.geojson | 134 | Point/Polygon | OK |
| Toilets | toilets.geojson | 65 | Point/Polygon | OK |
| Police | police.geojson | 53 | Point/Polygon | OK |
| Fire stations | fire.geojson | 10 | Point/Polygon | OK |

Note: "water_metro" is OSM ferry_terminal/ferry tagging; explicit Kochi Water Metro terminal coverage in OSM is partial — count includes general ferry terminals in the bbox.

---

## Population (WorldPop)
- Source: WorldPop Global per-country population 2020 (`wpgppop`) via WorldPop Stats API.
- Endpoint: POST https://api.worldpop.org/v1/services/stats (dataset=wpgppop, year=2020, geojson=<ward geom, 5dp>); polled https://api.worldpop.org/v1/tasks/<taskid> until finished; read data.total_population.
- License: CC-BY 4.0 (WorldPop, University of Southampton).
- Written to: wards.geojson property `population_2020` (per ward; `null` where not yet computed).
- Date: 2026-06.
- STATUS: **PARTIAL — upstream WorldPop API degraded at acquisition time.** The `/v1/services/stats` submit endpoint returned read-timeouts (45–90s, no response) and intermittent malformed/HTML error payloads throughout the acquisition window (2026-06-08/09), making the full 77-ward sweep infeasible in-session. Pipeline VERIFIED working end-to-end (submit -> taskid -> poll -> finished -> total_population): ward No 2 (feature idx 0) returned **population_2020 = 5175.6**, a plausible value for a dense central-Kochi division. All remaining wards carry `population_2020: null` pending API recovery. A resumable, stdlib-only sidecar-checkpoint script was left to backfill opportunistically. NO population values fabricated. Re-run to complete once WorldPop stabilizes.

---

## Kerala devolution / fiscal-devolution context (control-group rationale)
Kerala = the DEVOLUTION COUNTER-EXAMPLE. Context links captured (not geodata):
- People's Planning in Kerala (1996 People's Plan Campaign; ~35–40% of state plan funds devolved to local governments): https://en.wikipedia.org/wiki/People%27s_Planning_in_Kerala
- Local government in Kerala (3-tier panchayat raj, Grama Sabhas): https://en.wikipedia.org/wiki/Local_government_in_Kerala
- Kerala State Planning Board — Working Group Report on Decentralised Planning Process: https://spb.kerala.gov.in/sites/default/files/inline-files/Working%20Group%20Report%20on%20Decentralised%20Planning%20Process.pdf
- Kerala People's Campaign for Decentralized Planning (Participedia case): https://participedia.net/case/35
- Kerala Panchayati Raj Planning & Budgeting (Participedia method): https://participedia.net/method/5415
- Participatory Development Plan: Kerala (SDG16+): https://www.sdg16.plus/policies/participatory-development-plan-kerala-india/

### Kerala open spatial data portals (strong-open-data state; for future authoritative ward/LSG boundaries)
- KSDI OpenSDI GeoNode: https://opensdi.kerala.gov.in/  (layer `geonode:LSGD_Boundary_2021` — authoritative LSG/ward boundaries; behind GeoNode viewer, no confirmed direct open GeoJSON download as of 2026-06)
- Kerala GeoPortal (KSDI): http://www.ksdi.kerala.gov.in/ksdi/index.html
- EITD / KSITM KSDI program: https://eitd.kerala.gov.in/en/kerala-state-spatial-data-infrastructure/

---

## MISSING / caveats
- **Authoritative 74-division ward file: MISSING (open).** Official Kochi Corporation = 74 divisions; only an older 77-polygon (71 numbered) DataMeet set is openly downloadable. KSDI LSGD_Boundary_2021 exists but is not exposed as a direct open GeoJSON download (GeoNode viewer/registration). Used real DataMeet geometry; flagged the count discrepancy rather than substituting.
- Subdistricts/taluks sourced from geohacker/kerala (DataMeet maps lacks a taluk layer).
- OSM "water_metro" relies on generic ferry tagging; dedicated Kochi Water Metro station coverage in OSM is partial.
