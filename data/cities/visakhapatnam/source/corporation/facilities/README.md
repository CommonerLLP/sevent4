# GVMC Official Facility Lists — Status

This folder is for official facility lists (libraries / schools / health) from GVMC or
AP open data. As of June 2026, structured machine-readable facility datasets for GVMC
are largely **not openly published**. What was found:

## 1. Wards Map (OpenCity, open data) — AVAILABLE
- **Dataset:** Visakhapatnam Wards Map 2024 (98 wards)
- **Page:** https://data.opencity.in/dataset/visakhapatnam-wards-map-2024
- **Publisher:** OpenCity.in (source: livingatlas.esri.in; author: Vaidyanathan R)
- **License:** Public Domain / Open Definition compliant
- **KML:** https://data.opencity.in/dataset/3b3266a0-b88f-4f38-9372-6b5997bbf01a/resource/24a12e3c-d694-455c-a495-63cec30a6530/download/20877dde-2de3-4b0f-9211-329731541ec6.kml
- **PDF:** https://data.opencity.in/dataset/3b3266a0-b88f-4f38-9372-6b5997bbf01a/resource/6a976732-4b6d-480e-9e7e-2f3992c76e4d/download/c6e13f5c-9906-4de9-8246-4e232fd3056a.pdf
- Note: this is a boundary/geometry dataset, NOT a facility (school/library/health) list.
  It belongs more naturally with /boundaries but is mirrored here as the only open GVMC
  spatial dataset located.

## 2. Health — descriptive only, NO structured list
- GVMC Health page: https://www.gvmc.gov.in/wss/static_content/Health.jsp
  (retrieved via Wayback; site TLS reset directly). Content is narrative prose centred on
  King George Hospital (est. 1845, 1200+ beds). No enumerated list of GVMC Urban Health
  Centres / dispensaries with addresses is published on that page.

## 3. Schools / Libraries — NOT FOUND as open data
- GVMC site has an "Education" department section and an "Elected Wing / Departments /
  Public Health / UCD" menu, but these are served by the dynamic gvmc.gov.in app whose
  HTTPS endpoint reset all connections from this environment (103.44.14.220 / 122.15.26.145).
- No CKAN/AP-open-data dataset of GVMC schools or municipal libraries was located.
  data.opencity.in has Visakhapatnam content but only the wards map above as a clean dataset.

## What's missing / next steps
- Crawl gvmc.gov.in (Departments > Education, Public Health, UCD; Citizens Charter; Reports)
  from an India-routed connection — the TLS reset here is environmental, not a dead site
  (a March 2026 Wayback snapshot exists and renders).
- AP open-data portals (apsdma, CFMS, AP State data) for GVMC school/health rosters.
