# City data contract

Each city lives under `data/cities/<city-id>/`:

```text
data/cities/ahmedabad/
  city.yaml
  source/
  layers/
    layer_manifest.json
    wards.geojson
    acs.geojson
    pcs.geojson
    jurisdiction_crosswalk.json
```

`city.yaml` tells the console builder where the city is and where its data lives:

```yaml
id: ahmedabad
name: Ahmedabad
country: India
state: Gujarat
center: [72.58, 23.03]
bbox: [72.45, 22.90, 72.74, 23.18]
crs_metric: EPSG:32643
layers_dir: data/cities/ahmedabad/layers
source_dir: data/cities/ahmedabad/source
outputs_dir: public/cities/ahmedabad
```

`layer_manifest.json` controls what appears in the console: layer id, display
name, GeoJSON/image file, type, default visibility, popup fields, and styling.

**Minimum useful layers:** `wards.geojson` (ULB ward polygons), `acs.geojson`
(Assembly constituencies), `pcs.geojson` (Parliamentary constituencies),
`jurisdiction_crosswalk.json`, plus service points (schools, health, libraries,
toilets, transit stops…). Join councillor data into `wards.geojson`, and MLA/MP
attribution into `acs.geojson`/`pcs.geojson`, where a public roster exists.

## The crosswalk is not optional

The console is an Indian governance tool first and a map second. For every city,
someone must match the public administration and electoral geographies: State and
district → Parliamentary constituency → Assembly constituency → Block (where
relevant) → ULB ward (or gram panchayat for rural work).

Ahmedabad ships a generated `jurisdiction_crosswalk.json` as the complete
reference case; new forks can start from `data/jurisdiction_crosswalk.stub.json`.
If polygons exist, generate the crosswalk by intersecting wards/GPs with ACs, PCs,
districts and blocks; otherwise curate it manually from official records, one row
per real overlap. **Delhi uses a separate governance adapter** — don't force it
into the plain municipal model.

## Make a new city

1. `cp -r data/cities/ahmedabad data/cities/<your-city>`
2. Edit `city.yaml`: name, center, bbox, CRS, paths.
3. Replace `layers/{wards,acs,pcs}.geojson`.
4. Replace or remove the service layers in `layers/`.
5. Edit `layers/layer_manifest.json` to name the layers you actually have.
6. Build + serve:

```bash
scripts/build-city.sh <your-city>
scripts/serve.sh <your-city>
# output: public/cities/<your-city>/index.html
```

## Python entry points

The shell scripts call these package entry points:

```bash
sevent4-console
sevent4-gtfs-corridors
sevent4-ward-service-access
```

Or run the builder directly:

```bash
python -m sevent4.build_city_console \
  --city data/cities/ahmedabad/city.yaml \
  --layers data/cities/ahmedabad/layers/layer_manifest.json \
  --out public/cities/ahmedabad/index.html
```

See also [Data recipes](data-recipes.md) for rebuilding the Ahmedabad seed from
public sources.
