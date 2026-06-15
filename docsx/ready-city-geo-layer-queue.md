# Ready-City Geo Layer Acquisition Queue

Status: working acquisition queue for the five selectable cities.

This queue is for finding and acquiring more useful geo layers without weakening
the source discipline in `docsx/source-policy-and-readiness.md`. It covers the
current selectable cities:

- Ahmedabad
- Bengaluru
- Chennai
- Delhi
- Kolkata

## Acquisition Rules

1. Prefer official city, State, Union, CAG/RBI/FC/SFC, census, GTFS, and OpenCity
   mirrors of official sources.
2. Use OSM only as open fallback or context, and label it as OSM.
3. Do not derive stored layers from Google Maps content.
4. Every new layer must record publisher, URL/path, retrieval date, licence if
   available, transformation script, and confidence.
5. Every layer must state what an absence means: real absence, missing mapping,
   unknown, or modelled absence.

## Current Layer Gaps

| City | Strong current surface | Main gap |
|---|---|---|
| Ahmedabad | Ward/AC/PC, transit, heat, libraries, budget series, roads, public-service context | Authoritative replacements for OSM schools/health/toilets/police; AUDA/land-use; walkability quality. |
| Bengaluru | Ward/AC/PC, BBMP works spend, heat, metro/stops, public-service context | GBA/BBMP transition layers, BDA/BWSSB/BESCOM/BMTC jurisdictions, water/sewer/SWM, streetlights, official walkability inputs. |
| Chennai | Ward/AC/PC, zone finance, transit, heat, services | CMWSSB, CMDA/CUMTA, drainage/flood, slums, public toilets, property tax, official roads/sidewalk proxies. |
| Delhi | NCT special model, wards/AC/PC, GTFS bus, OSM metro/rail/roads, heat, AQ, libraries | MCD 2022 ward geometry, MCD/NDMC/DCB finance, DDA/land, MCD zones, walkability quality, full DPL/transit service access. |
| Kolkata | Ward/AC/PC, suburban rail, metro, heat, services | KMC budget/account parsing, KMC drainage, KMDA/KMWSA/KMRC authority layers, air/water, official bus/route data. |

## Ahmedabad

Immediate targets:

- AMC official health facilities, schools, toilets, fire, and police source
  replacements for OSM-derived points.
- AUDA development-plan / land-use / town-planning scheme layers.
- AMC or AMTS stop accessibility, footpath, public toilet, and library service
  hours where public.
- Ward works, contracts, and road registers that can connect budget to place.

Why:

Ahmedabad currently has the strongest finance/source surface. The next step is
not more visual density; it is replacing every OSM-dependent service claim with
a public source of record.

## Bengaluru

Immediate targets from existing OpenCity scoping:

- BDA jurisdiction and boundary: https://data.opencity.in/dataset/bda-jurisdiction-and-boundary
- Greater Bengaluru Authority corporations delimitation 2025: https://data.opencity.in/dataset/greater-bengaluru-authority-corporations-delimitation-2025
- BDA cadastral maps: https://data.opencity.in/dataset/bengaluru-cadastral-maps
- Bengaluru urban revenue maps: https://data.opencity.in/dataset/bengaluru-urban-revenue-maps
- BWSSB sewerage line maps: https://data.opencity.in/dataset/bwssb-sewerage-line-maps-for-bengaluru
- BWSSB boundary maps: https://data.opencity.in/dataset/bwssb-boundary-maps
- BBMP solid waste management data: https://data.opencity.in/dataset/bbmp-solid-waste-management-data
- BMTC bus stops and routes by ward: https://data.opencity.in/dataset/bus-stops-and-routes-map-by-ward
- Bengaluru tree census data: https://data.opencity.in/dataset/bengaluru-tree-census-data
- Bengaluru zone-wise streetlights: https://data.opencity.in/dataset/bengaluru-zone-wise-streetlights
- Traffic police jurisdictions: https://data.opencity.in/dataset/bengaluru-traffic-police-jurisdictions

Why:

Bengaluru is the best city for showing the unelected-city problem: GBA, BBMP,
BDA, BWSSB, BMTC, BMRCL, BESCOM, and police all cut the city differently.

## Chennai

Immediate targets from existing OpenCity scoping:

- CMWSSB administrative boundaries: https://data.opencity.in/dataset/cmwssb-administrative-boundaries
- Chennai Urban Metropolitan Transport Authority boundary: https://data.opencity.in/dataset/chennai-urban-metropolitan-transport-authority-boundary
- Chennai stormwater drain maps: https://data.opencity.in/dataset/chennai-stormwater-drain-swd-maps
- Chennai sewage pumping network: https://data.opencity.in/dataset/chennai-sewage-pumping-network
- Chennai sewerage collection system: https://data.opencity.in/dataset/chennai-sewerage-collection-system
- Chennai flooding data: https://data.opencity.in/dataset/chennai-flooding-data
- Chennai water distribution stations: https://data.opencity.in/dataset/chennai-water-distribution-stations
- Chennai police jurisdictions: https://data.opencity.in/dataset/chennai-police-jurisdictions
- Chennai slums: https://data.opencity.in/dataset/chennai-slums
- Chennai road centerline map: https://data.opencity.in/dataset/chennai-road-centerline-map
- Chennai public toilets: https://data.opencity.in/dataset/chennai-public-toilets
- Chennai parks: https://data.opencity.in/dataset/chennai-parks
- Chennai property tax collections: https://data.opencity.in/dataset/chennai-property-tax-collections

Why:

Chennai is the best ready city for teaching that floods, drains, water, sewage,
roads, and planning are not one municipal surface.

## Delhi

Immediate targets:

- MCD 2022 250-ward geometry if an official/open source appears.
- MCD zones and departments.
- NDMC boundary, facilities, budget/account material.
- Delhi Cantonment Board boundary and finance material.
- DDA land/use/planning layers.
- GNCTD department layers that overlap MCD functions.
- Full DPL fixed branches, mobile points, bus/metro access, and service hours.
- MCD/NDMC finance layers from budget PDFs and accounts.

Existing in repo:

- DTC/cluster GTFS bus stops and routes.
- OSM Metro/rail/RRTS/roads as open transit context.
- Air quality and heat surfaces.

Why:

Delhi should teach capital-city exception logic: elected NCT, Union control,
MCD, NDMC, DCB, DDA, police, and NCR institutions.

## Kolkata

Immediate targets from existing OpenCity scoping:

- Kolkata wards information: https://data.opencity.in/dataset/kolkata-wards-information
- West Bengal election boundaries maps: https://data.opencity.in/dataset/west-bengal-election-boundaries-maps
- Kolkata municipal corporation offices: https://data.opencity.in/dataset/kolkata-municipal-corporation-offices
- Kolkata public service centres: https://data.opencity.in/dataset/kolkata-public-service-centres
- Kolkata drainage maps: https://data.opencity.in/dataset/kolkata-drainage-maps
- KMC budget statement: https://data.opencity.in/dataset/kmc-budget-statement
- Kolkata health services: https://data.opencity.in/dataset/kolkata-health-services
- Kolkata schools: https://data.opencity.in/dataset/kolkata-schools
- Kolkata hourly air quality reports: https://data.opencity.in/dataset/kolkata-hourly-air-quality-reports
- Kolkata water bodies census data: https://data.opencity.in/dataset/kolkata-water-bodies-census-data
- Kolkata markets: https://data.opencity.in/dataset/kolkata-markets

Why:

Kolkata is useful for old-corporation/old-infrastructure teaching: KMC, KMDA,
Kolkata Police, rail/metro, markets, drainage, and State-mediated finance.

## Next Build Order

1. Ahmedabad authoritative service replacements.
2. Bengaluru authority and utility jurisdiction layers.
3. Chennai water/sewer/flood/planning layers.
4. Delhi finance and capital-body surfaces.
5. Kolkata KMC budget/drainage/service authority layers.

Each acquisition should land with tests or at least deterministic validation:

- file exists;
- feature count is nonzero;
- CRS is WGS84 or transformed to WGS84;
- required join fields exist;
- source metadata exists;
- confidence and absence semantics are explicit.
