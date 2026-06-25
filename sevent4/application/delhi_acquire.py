from __future__ import annotations

from sevent4.domain.delhi_acquire import (
    BOUNDARY_SOURCES,
    OSM_LINE_QUERIES,
    OSM_POINT_QUERIES,
    build_routes_from_shapes,
    build_routes_from_stop_times,
    build_stops,
    merge_layer_entries,
    opencity_manifest,
    opencity_record,
    osm_line_entry,
    osm_lines,
    osm_point_entry,
    osm_points,
    overpass_query,
    skipped_opencity_formats,
    slugify,
    usable_opencity_rows,
)


def acquire_osm_layers(post_fn, write_layer_fn, manifest: dict) -> dict:
    """post_fn(query)->overpass json ; write_layer_fn(fc, layer_id)->feature count.
    Returns per-layer counts; mutates manifest with the present layers."""
    entries, counts = [], {}
    for lid, (body, field, color) in OSM_LINE_QUERIES.items():
        fc = osm_lines(post_fn(overpass_query(body)), field)
        counts[lid] = write_layer_fn(fc, lid)
        if fc["features"]:
            entries.append(osm_line_entry(lid, color))
    for lid, (body, field, color) in OSM_POINT_QUERIES.items():
        fc = osm_points(post_fn(overpass_query(body)), field)
        counts[lid] = write_layer_fn(fc, lid)
        entries.append(osm_point_entry(lid, color))
    merge_layer_entries(manifest, entries)
    return counts


def acquire_opencity(rows: list[dict], fetch_fn, dest_fn, limit: int = 0):
    """fetch_fn(url, dest)->(size, sha) ; dest_fn(ds_slug, filename)->(dest, local_rel).
    Returns (manifest, skipped_formats)."""
    usable = usable_opencity_rows(rows)
    if limit:
        usable = usable[:limit]
    skipped = skipped_opencity_formats(rows)
    records = []
    for i, r in enumerate(usable):
        ds = slugify(r["dataset_name"] or r["dataset_title"], f"ds{i}")
        ext = r["resource_format"].lower()
        fname = slugify(r["resource_name"] or r["resource_id"], f"r{i}") + f".{ext}"
        dest, local_rel = dest_fn(ds, fname)
        try:
            size, sha = fetch_fn(r["resource_url"], dest)
            status = "ok"
        except Exception as e:
            size, sha, status = 0, "", f"error: {type(e).__name__}"
        records.append(opencity_record(r, local_rel, size, sha, status))
    return opencity_manifest(records, skipped), skipped


def acquire_gtfs_layers(tables, write_layer_fn, prefix: str):
    """write_layer_fn(fc, basename)->count. Returns (n_routes, n_stops, method)."""
    n_stops = write_layer_fn(build_stops(tables["stops"]), f"{prefix}_stops")
    if "shapes" in tables and not tables["shapes"].empty:
        routes_fc = build_routes_from_shapes(tables["routes"], tables["trips"], tables["shapes"])
        method = "shapes.txt"
    elif "stop_times" in tables:
        routes_fc = build_routes_from_stop_times(
            tables["routes"], tables["trips"], tables["stops"], tables["stop_times"])
        method = "reconstructed from stop_times"
    else:
        raise ValueError("feed has neither shapes.txt nor stop_times.txt -- cannot build route lines")
    n_routes = write_layer_fn(routes_fc, f"{prefix}_routes")
    return n_routes, n_stops, method


def acquire_boundaries(source, write_layer_fn):
    """source has .acs()/.pcs()/.wards()/.districts(acs) ; write_layer_fn(gdf, name).
    Returns (counts, districts_or_None)."""
    acs = source.acs()
    pcs = source.pcs()
    wards = source.wards()
    districts = source.districts(acs)
    write_layer_fn(acs, "acs")
    write_layer_fn(pcs, "pcs")
    write_layer_fn(wards, "wards")
    if districts is not None:
        write_layer_fn(districts, "districts")
    counts = {"acs": len(acs), "pcs": len(pcs), "wards": len(wards),
              "districts": 0 if districts is None else len(districts)}
    return counts, districts


def boundary_sources() -> dict:
    return BOUNDARY_SOURCES
