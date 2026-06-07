# SevenT4

SevenT4 (`sevent4`) is a city-layer intelligence toolkit for civic groups.
It starts with Ahmedabad and is structured so the same console can be adapted
for Kolkata, Chennai, Bengaluru, other large Indian cities, and eventually all
urban local bodies.

The core idea is simple: keep public jurisdiction boundaries, transit, public
services, land use, heat exposure, and municipal finance in a reusable data
contract, then render a local-first city console from that contract.

## Current Seed

- Ahmedabad city configuration in `data/cities/ahmedabad/city.yaml`
- Ahmedabad source data in `data/cities/ahmedabad/source/`
- Ahmedabad processed layers in `data/cities/ahmedabad/layers/`
- Public jurisdiction layers for ward, AC, and PC selection
- Vendored MapLibre assets in `public/assets/`
- Python package code in `sevent4/`

## Deliberately Absent

This seed does not include private operational datasets, campaign dossiers,
private brand assets, or organiser workflows.

It does include public jurisdiction geography and representative attribution.
Ward, councillor, MLA, and MP accountability is part of the civic toolkit: if a
road, drainage, heat, transit, or service issue falls inside a ward, AC, or PC,
the console should help residents see which public office is responsible.

## Build The Ahmedabad Console

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m sevent4.build_city_console \
  --city data/cities/ahmedabad/city.yaml \
  --layers data/cities/ahmedabad/layers/layer_manifest.json \
  --out public/cities/ahmedabad/index.html
```

Then serve the repo root and open `public/cities/ahmedabad/index.html`.

## Data Contract

Each city gets:

- `city.yaml`: identity, center, bbox, CRS, source paths, output paths
- `layers/layer_manifest.json`: layer ids, files, display labels, paint, popup fields
- `source/`: original source files
- `layers/`: processed layers used by the console

Minimum jurisdiction layers:

- `layers/wards.geojson`: ULB ward polygons; should include a display field such as `Name`
- `layers/acs.geojson`: assembly constituency polygons; should include `ac_name`, `representative`, `office`, `party`, and `pc_name` when available
- `layers/pcs.geojson`: parliamentary constituency polygons; should include `pc_name`, `representative`, `office`, and `party` when available
- ward councillor data: should be joined into `wards.geojson` when a full public ward roster is available

Keep private operational interpretation out of the base layer contract. Public
jurisdiction and elected-representative attribution belongs in the default
city intelligence toolkit.
