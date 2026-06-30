# Attribution & Data Licenses

**The Unelected City** is built almost entirely on data that other people gathered,
digitised, and gave away. This atlas exists because of them. Our thanks — and the
licence obligations we are bound by — are recorded here.

## How licensing is split in this repository

- **Source code** — everything this project authored (the Python recipes, the console
  generator, page templates, HTML/CSS/JS) — is licensed under **AGPL-3.0** (see
  [`LICENSE`](LICENSE)).
- **Data** — the geospatial layers, population, finance, and provenance records — is
  **third-party data, redistributed under each source's own licence**, listed below.
  Nothing here relicenses anyone else's data. Where a source requires share-alike (ODbL,
  CC-BY-SA), the derived layers we ship are kept open under those same terms.

If you reuse a layer from this atlas, you inherit the obligations of its upstream source
(attribution, and share-alike where it applies), not AGPL.

---

## With thanks — the people and institutions whose data this is

### OpenStreetMap contributors — **ODbL 1.0**
Roads, transit stops, metro lines/stations, hospitals, schools, libraries, police,
fire, toilets, and other service points across every city are derived from
**OpenStreetMap** via the Overpass API. © OpenStreetMap contributors, licensed under the
**Open Database License (ODbL) 1.0**. The map layers we publish are a Derivative
Database and remain available under ODbL; the rendered consoles are a Produced Work that
credits OSM. <https://www.openstreetmap.org/copyright>

### DataMeet community — **CC-BY 2.5 IN / CC-BY-SA 2.5 IN / CC-BY 4.0**
Ward, Assembly-constituency, Parliamentary-constituency, district and municipal
boundaries come from the **DataMeet** community — the `datameet/maps`,
`datameet/Municipal_Spatial_Data`, and city-chapter (e.g. Pune) repositories — built by
volunteers digitising official boundaries. Thank you to the DataMeet community and its
chapters. Licensed under the DataMeet community terms (CC-BY 2.5 IN, CC-BY-SA 2.5 IN, or
CC-BY 4.0 depending on the dataset). <https://datameet.org>

### WorldPop, University of Southampton — **CC-BY 4.0**
Per-ward population (`population_2020`) is from the **WorldPop** Global Project Population
Data (`wpgppop`, 2020, 100 m). © WorldPop / University of Southampton, **CC-BY 4.0**.
<https://www.worldpop.org>

### USGS / NASA Landsat, via Microsoft Planetary Computer — Public Domain
The per-city heat layers (`heat30m.png`, `ward_heat.geojson`, and the
`ward_heat_summary.json` the console strips read) are derived from **Landsat
Collection-2 Level-2 surface-temperature** scenes (USGS/NASA), accessed through
the **Microsoft Planetary Computer** STAC. Landsat data is U.S. Government public
domain; thanks to the USGS/NASA Landsat program and the Planetary Computer for
open access. The WHY/heat chapter additionally cites the **Centre for Science and
Environment** (*Making Delhi Heat-Resilient*, 2026) and the **Lancet Countdown on
Health and Climate Change 2025** for city-wide figures — credited inline there.
<https://planetarycomputer.microsoft.com>

### OpenCity Urban Data Portal (Oorvani Foundation) — open / CC-BY / Public Domain
City finance, ward/jurisdiction, and several civic datasets come from the **OpenCity**
Urban Data Portal (`data.opencity.in`). Thank you to OpenCity and the Oorvani Foundation
for assembling and opening Indian urban data. Per-dataset licences (Public Domain /
CC-BY / ODbL) are recorded in each city's source inventory. <https://data.opencity.in>

### Census of India 2011 & the Election Commission of India
District / sub-district population and the constituency geographies underlying the
DataMeet layers derive from the **Census of India 2011** and the **Election Commission
of India** delimitations. Government of India data, used with attribution.

### City & state governments and their bodies
The civic, finance, governance, and roster data is the work of the municipal
corporations, development authorities, transit undertakings, and state departments that
publish it. With thanks to:

- **Ahmedabad** — Ahmedabad Municipal Corporation (AMC), AUDA, AMTS/Janmarg
- **Bengaluru** — BBMP / Greater Bengaluru Authority, BWSSB, BMTC, BMRCL
- **Chennai** — Greater Chennai Corporation, CMWSSB, MTC, CMRL
- **Delhi** — Municipal Corporation of Delhi (MCD), **New Delhi Municipal Council (NDMC)**, DDA, DJB, DTC, DMRC, Govt of NCT of Delhi
- **Hyderabad** — GHMC
- **Bhubaneswar** — Bhubaneswar Municipal Corporation, BDA
- **Jaipur** — Jaipur Municipal Corporation (Heritage & Greater)
- **Kanpur** — Kanpur Municipal Corporation (Nagar Nigam)
- **Kochi** — Cochin Corporation
- **Kolkata** — Kolkata Municipal Corporation, KMDA
- **Lucknow** — Lucknow Municipal Corporation (Nagar Nigam), LDA, UP Metro Rail Corp (UPMRC)
- **Mumbai** — Brihanmumbai Municipal Corporation (MCGM)
- **Pune** — Pune Municipal Corporation, PMRDA
- **Visakhapatnam** — Greater Visakhapatnam Municipal Corporation (GVMC)

and the respective state governments, transit agencies (incl. published **GTFS** feeds),
and Pollution Control Boards / Committees.

### Government of India — Parliament & central agencies
- **Ministry of Environment, Forest & Climate Change / Rajya Sabha** — pollution-control-board
  staffing figures from parliamentary answers (e.g. Unstarred Q. 3096, 2025; Q. 57, 2023),
  obtained from the official record (sansad / `rsdoc.nic.in`).
- **Central Pollution Control Board (CPCB)** and the State Pollution Control Boards / PCCs.

### Research & open repositories
- **Centre for Policy Research (CPR)** — *The State of India's Pollution Control Boards*
  (cited as secondary research, with thanks).
- **GADM** — sub-district boundaries (free for academic/non-commercial use, attribution).
- Open community shapefile repositories: **datta07/INDIAN-SHAPEFILES**,
  **geohacker/india**, **geohacker/kerala** (Census-2011-derived, openly redistributed).
- **AirAtlas** (compiled CPCB station data; credit Sarvesh Tewari).

### Scholarship
The Findings essays draw on the writings of **B.R. Ambedkar** (*Writings and Speeches*,
Vasant Moon ed.) and the secondary literature cited inline on each page.

---

*If you are a data source listed here and would like your attribution corrected or
amended, please open an issue. Per-layer provenance (source URL, retrieval date, feature
counts, licence) is recorded in each city's `PROVENANCE.md` and `sources.json`.*
