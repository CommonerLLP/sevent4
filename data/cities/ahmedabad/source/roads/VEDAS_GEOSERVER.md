# VEDAS / ISRO-SAC GeoServer — Ahmedabad geospatial layers

**Discovered 2026-06-10** by tracing the AUDA "Ahmedabad City GIS" viewer
(`vedas.sac.gov.in/vstatic_1/auda_development/`) → its `refLayers.js` → the
backing GeoServer. This is **government geospatial data (ISRO/SAC), usable and
redistributable with attribution** under India's liberalised geospatial policy
— unlike Google/Mappls (the viewer also references a MapMyIndia tile key, which
we do NOT use for that reason).

## Endpoint

```
WMS GetCapabilities:
https://vedas.sac.gov.in/geoserver/vedas_spatial/wms?service=WMS&version=1.3.0&request=GetCapabilities
```

- **WMS works** (GetMap renders PNG; GetFeatureInfo responds).
- **WFS is LOCKED** (404 on /ows, /wfs, GetFeature) — so the **vector + attribute
  tables (incl. road names) cannot be bulk-exported**. We can render layers as
  image overlays and click-query points, but not pull the geometry as GeoJSON.
- Requires a browser User-Agent header.

## Layers that matter for the road work (workspace `vedas_spatial:`)

| Layer | Use |
|---|---|
| `ahm_roads_2013` | Ahmedabad road network — the official road geometry (raster overlay only, WFS locked). On the resurfacing map as the "Official road network" toggle. |
| `ahmedabad_amc_boundary` | AMC municipal boundary |
| `ahm_rail_network` | rail |
| `ahm_drainage`, `ahm_canal`, `ahm_water_bodies`, `ahmedabad_channel_network` | the ~940 km drainage vs 2,500 km road story (built-to-flood) |
| `ahm_builtup_2001…2025`, `ahm_new_development_*`, `ahm_urbarea_*` | 24-yr built-up growth time series (Harvey secondary-circuit / land-uplift axis) |
| `ahm_building_footprint`, `ahm_buildings`, `ahm_building_orientation` | building footprints |
| `ahm_urban_flood_risk_zones`, `ahm_hot_cold_spots_em_2013_2023` | flood-risk + heat (the heat layer already built) |
| `ahmedabad_corona_oct1965_*` | 1965 CORONA spy-sat imagery — historical baseline |
| `ahm_irs*`, `ahm_k3a_*`, `ahmedabad_liss3/4_raster`, `Ahmedabad_DSM`, `ahm_dtm` | multi-date satellite + elevation |

Full 68-layer Ahmedabad catalog: `vedas_ahmedabad_layers.txt`.

## What this does and does not solve for the road-contractor map

- **Solves:** a legitimate, govt-sourced **visual road network** under the
  resurfacing-recurrence choropleth (no more OSM-only). Also unlocks the
  drainage-vs-road and built-up-growth layers for the wider atlas.
- **Does NOT solve:** joining each register stretch to its exact road line.
  That needs the road layer's **attribute table (names/IDs)**, which WFS would
  give but is locked here — and even then the register speaks in society
  landmarks, so the authoritative full join still lives in **AMC's own road
  GIS** (the system that generates these registers). VEDAS gets us the picture,
  not the per-stretch join.

## Reuse note
This GeoServer is an org-level asset for the whole sevent4 atlas (built-up
growth, drainage, flood, heat, footprints — all 12 cities may have analogues).
Worth a generic VEDAS WMS adapter if more cities turn out to be covered.
