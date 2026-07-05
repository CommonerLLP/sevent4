from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class IudxRequestResource:
    id: str
    label: str
    item_type: str
    resource_type: str
    required_for_static_gtfs: bool
    priority: int
    group_name: str


def load_access_request_packet(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def iter_request_resources(
    packet: dict[str, Any],
    *,
    static_only: bool = False,
    max_priority: int | None = None,
) -> Iterable[IudxRequestResource]:
    groups = packet.get("request_priority", [])
    for group in groups:
        priority = int(group.get("priority", 0))
        if max_priority is not None and priority > max_priority:
            continue
        group_name = str(group.get("name", "")).strip()
        for resource in group.get("resources", []):
            required_for_static_gtfs = bool(resource.get("required_for_static_gtfs"))
            if static_only and not required_for_static_gtfs:
                continue
            yield IudxRequestResource(
                id=str(resource["id"]),
                label=str(resource.get("label", resource["id"])),
                item_type=str(resource.get("itemType", "resource")),
                resource_type=str(resource.get("resourceType", "")),
                required_for_static_gtfs=required_for_static_gtfs,
                priority=priority,
                group_name=group_name,
            )


def token_request_payload(resource: IudxRequestResource) -> dict[str, str]:
    return {
        "itemId": resource.id,
        "itemType": resource.item_type,
        "role": "consumer",
    }


def classify_token_response(
    resource: IudxRequestResource,
    http_status: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    title = str(payload.get("title", ""))
    detail = str(payload.get("detail", ""))
    token_available = bool(_nested_get(payload, "results", "accessToken"))
    if token_available:
        status = "ok"
    elif "No policy exist" in detail or "APD evaluation failed" in title:
        status = "gated"
    elif http_status in {401, 403}:
        status = "denied"
    else:
        status = "error"

    return {
        "id": resource.id,
        "label": resource.label,
        "group": resource.group_name,
        "priority": resource.priority,
        "resource_type": resource.resource_type,
        "required_for_static_gtfs": resource.required_for_static_gtfs,
        "http_status": http_status,
        "status": status,
        "token_available": token_available,
        "type": payload.get("type"),
        "title": title or None,
        "detail": detail or None,
    }


def summarize_probe_results(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    by_group: dict[str, dict[str, int]] = {}
    for result in results:
        status = str(result.get("status", "unknown"))
        group = str(result.get("group", "unknown"))
        by_status[status] = by_status.get(status, 0) + 1
        group_counts = by_group.setdefault(group, {})
        group_counts[status] = group_counts.get(status, 0) + 1
    return {
        "by_status": by_status,
        "by_group": by_group,
    }


def normalize_probe_payload(
    payload: dict[str, Any],
    *,
    normalized_at: str,
) -> dict[str, Any]:
    normalized = dict(payload)
    results = list(normalized.get("results", []))
    normalized["normalized_at"] = normalized_at
    normalized["resource_count"] = len(results)
    normalized["summary"] = summarize_probe_results(results)
    return normalized


def summarize_post_approval_readiness(
    *,
    post_approval_build: dict[str, Any],
    blocked_groups: Iterable[str],
    gtfs_table_coverage: list[dict[str, Any]],
    gtfs_field_coverage: list[dict[str, Any]],
    bmrcl_export_field_coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    blocked = set(blocked_groups)
    readiness: list[dict[str, Any]] = []
    if "bmtc_static_gtfs" in post_approval_build:
        build = post_approval_build["bmtc_static_gtfs"]
        table_summary = gtfs_table_coverage[0] if gtfs_table_coverage else {}
        missing_tables = list(table_summary.get("missing_required_tables", []))
        missing_files = [f"{table}.json" for table in missing_tables]
        fields_ready = bool(gtfs_field_coverage) and all(
            bool(summary.get("advertised_table_fields_ready")) for summary in gtfs_field_coverage
        )
        catalogue_inputs_ready = bool(table_summary.get("stop_sequence_geometry_ready")) and fields_ready
        access_groups = ["BMTC static GTFS tables"]
        access_gated = any(group in blocked for group in access_groups)
        remaining_gates = []
        if access_gated:
            remaining_gates.append("policy_access")
        if not catalogue_inputs_ready:
            remaining_gates.append("stop_times_or_equivalent_stop_sequence")
        readiness.append(
            {
                "build_key": "bmtc_static_gtfs",
                "feed_id": "bengaluru_bmtc_iudx_full_gtfs",
                "access_groups": access_groups,
                "access_gated": access_gated,
                "catalogue_inputs_ready": catalogue_inputs_ready,
                "missing_input_files_from_catalogue": missing_files,
                "required_input_files": list(build.get("required_input_files", [])),
                "quality_gate": dict(build.get("quality_gate", {})),
                "remaining_gates": remaining_gates,
            }
        )
    if "bmrcl_full_network_schedule" in post_approval_build:
        build = post_approval_build["bmrcl_full_network_schedule"]
        access_groups = ["BMRCL schedule and fare files", "BMRCL network geospatial resources"]
        access_gated = any(group in blocked for group in access_groups)
        missing_files = list(bmrcl_export_field_coverage.get("missing_export_files", []))
        catalogue_inputs_ready = bool(bmrcl_export_field_coverage.get("export_ready_fields"))
        remaining_gates = []
        if access_gated:
            remaining_gates.append("policy_access")
        remaining_gates.append("purple_green_yellow_scheduled_two_stop_trips")
        readiness.append(
            {
                "build_key": "bmrcl_full_network_schedule",
                "feed_id": "bengaluru_bmrcl_iudx_full_network_schedule",
                "access_groups": access_groups,
                "access_gated": access_gated,
                "catalogue_inputs_ready": catalogue_inputs_ready,
                "missing_input_files_from_catalogue": missing_files,
                "required_input_files": list(build.get("required_input_files", [])),
                "quality_gate": dict(build.get("quality_gate", {})),
                "remaining_gates": remaining_gates,
            }
        )
    return readiness


def build_status_packet(
    *,
    request_packet: dict[str, Any],
    probe_payload: dict[str, Any],
    transit_sources: dict[str, Any],
    compiled_at: str,
    catalogue_details: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    resources = list(iter_request_resources(request_packet))
    probe_summary = probe_payload.get("summary") or summarize_probe_results(probe_payload.get("results", []))
    by_group = probe_summary.get("by_group", {})
    blocked_groups = [
        group
        for group in by_group
        if by_group[group].get("gated", 0) or by_group[group].get("denied", 0)
    ]
    gated_feed_ids = [
        str(feed.get("feed_id"))
        for feed in transit_sources.get("feeds", [])
        if feed.get("status") == "gated" and feed.get("feed_id")
    ]
    feeds = list(transit_sources.get("feeds", []))
    sample_coverage_gaps = _sample_coverage_gaps(transit_sources.get("feeds", []))
    catalogue_details = list(catalogue_details)
    gtfs_table_coverage = summarize_static_gtfs_table_coverage(catalogue_details)
    gtfs_field_coverage = summarize_static_gtfs_field_coverage(catalogue_details)
    bmrcl_export_field_coverage = summarize_bmrcl_export_field_coverage(catalogue_details)
    post_approval_build = request_packet.get("post_approval_build", {})
    return {
        "schema": "sevent4.iudx_bengaluru_status.v1",
        "compiled_at": compiled_at,
        "requested_resource_count": len(resources),
        "static_required_resource_count": sum(1 for resource in resources if resource.required_for_static_gtfs),
        "latest_probe": {
            "generated_at": probe_payload.get("generated_at"),
            "normalized_at": probe_payload.get("normalized_at"),
            "resource_count": probe_payload.get("resource_count", len(probe_payload.get("results", []))),
            "summary": probe_summary,
        },
        "blocked_groups": blocked_groups,
        "gated_feed_ids": gated_feed_ids,
        "sample_coverage_gaps": sample_coverage_gaps,
        "bmrcl_operational_line_scope": _bmrcl_operational_line_scope(feeds),
        "catalogue_sample_availability": summarize_catalogue_samples(catalogue_details),
        "gtfs_resource_map": summarize_static_gtfs_resource_map(catalogue_details),
        "gtfs_table_coverage": gtfs_table_coverage,
        "gtfs_field_coverage": gtfs_field_coverage,
        "bmrcl_export_field_coverage": bmrcl_export_field_coverage,
        "success_evidence_after_approval": request_packet.get("success_evidence_after_approval", []),
        "post_approval_build": post_approval_build,
        "post_approval_readiness": summarize_post_approval_readiness(
            post_approval_build=post_approval_build,
            blocked_groups=blocked_groups,
            gtfs_table_coverage=gtfs_table_coverage,
            gtfs_field_coverage=gtfs_field_coverage,
            bmrcl_export_field_coverage=bmrcl_export_field_coverage,
        ),
        "next_action": "submit_iudx_policy_request" if gated_feed_ids or blocked_groups else "retry_layer_build",
    }


def summarize_catalogue_samples(catalogue_details: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for detail in catalogue_details:
        for result in detail.get("results", []):
            if not isinstance(result, dict):
                continue
            dataset = result.get("dataset", {})
            resources = [resource for resource in result.get("resource", []) if isinstance(resource, dict)]
            public_sample_files: list[dict[str, str]] = []
            empty_sample_file_count = 0
            inline_sample_resource_count = 0
            secure_resource_count = 0
            for resource in resources:
                if resource.get("accessPolicy") == "SECURE":
                    secure_resource_count += 1
                if "dataSample" in resource:
                    inline_sample_resource_count += 1
                for sample_file in resource.get("dataSampleFile", []):
                    if not isinstance(sample_file, dict):
                        continue
                    sample_url = str(sample_file.get("hasObject", "")).strip()
                    if sample_url:
                        public_sample_files.append(
                            {
                                "resource_id": str(resource.get("resourceId", "")),
                                "resource_label": str(resource.get("label", "")),
                                "name": str(sample_file.get("name", "")),
                                "url": sample_url,
                            }
                        )
                    else:
                        empty_sample_file_count += 1
            summaries.append(
                {
                    "dataset_id": str(dataset.get("id", "")),
                    "dataset_label": str(dataset.get("label", "")),
                    "resource_count": len(resources),
                    "secure_resource_count": secure_resource_count,
                    "public_sample_file_count": len(public_sample_files),
                    "empty_sample_file_count": empty_sample_file_count,
                    "inline_sample_resource_count": inline_sample_resource_count,
                    "public_sample_files": public_sample_files,
                }
            )
    return summaries


def summarize_static_gtfs_resource_map(catalogue_details: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered_tables = ["agency", "calendar", "routes", "stops", "trips", "stop_times"]
    summaries: list[dict[str, Any]] = []
    for detail in catalogue_details:
        for result in detail.get("results", []):
            if not isinstance(result, dict):
                continue
            dataset = result.get("dataset", {})
            mapped_resources = []
            mapped_tables = set()
            for resource in result.get("resource", []):
                if not isinstance(resource, dict):
                    continue
                table = _gtfs_table_from_label(str(resource.get("label", "")))
                if not table:
                    continue
                mapped_tables.add(table)
                mapped_resources.append(
                    {
                        "gtfs_table": table,
                        "gtfs_filename": f"{table}.txt",
                        "resource_id": str(resource.get("resourceId", "")),
                        "resource_label": str(resource.get("label", "")),
                        "resource_type": str(resource.get("resourceType", "")),
                        "iudx_resource_apis": list(resource.get("iudxResourceAPIs", [])),
                        "access_policy": str(resource.get("accessPolicy", "")),
                    }
                )
            if not mapped_resources:
                continue
            mapped_resources.sort(key=lambda row: ordered_tables.index(row["gtfs_table"]))
            summaries.append(
                {
                    "dataset_id": str(dataset.get("id", "")),
                    "dataset_label": str(dataset.get("label", "")),
                    "resources": mapped_resources,
                    "missing_gtfs_filenames": [
                        f"{table}.txt" for table in ordered_tables if table not in mapped_tables
                    ],
                }
            )
    return summaries


def summarize_static_gtfs_table_coverage(catalogue_details: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    required_tables = ["agency", "calendar", "routes", "stops", "trips", "stop_times"]
    summaries: list[dict[str, Any]] = []
    for detail in catalogue_details:
        for result in detail.get("results", []):
            if not isinstance(result, dict):
                continue
            dataset = result.get("dataset", {})
            resources = [resource for resource in result.get("resource", []) if isinstance(resource, dict)]
            advertised_tables = sorted(
                {
                    table
                    for resource in resources
                    for table in [_gtfs_table_from_label(str(resource.get("label", "")))]
                    if table
                },
                key=required_tables.index,
            )
            if not advertised_tables:
                continue
            missing_tables = [table for table in required_tables if table not in advertised_tables]
            summaries.append(
                {
                    "dataset_id": str(dataset.get("id", "")),
                    "dataset_label": str(dataset.get("label", "")),
                    "required_tables_for_stop_sequence_geometry": required_tables,
                    "advertised_tables": advertised_tables,
                    "missing_required_tables": missing_tables,
                    "stop_sequence_geometry_ready": not missing_tables,
                }
            )
    return summaries


def summarize_static_gtfs_field_coverage(catalogue_details: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    required_fields_by_table = {
        "agency": ["agency_id", "agency_name", "agency_url", "agency_timezone"],
        "calendar": [
            "service_id",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "start_date",
            "end_date",
        ],
        "routes": ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"],
        "stops": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
        "trips": ["route_id", "service_id", "trip_id"],
        "stop_times": ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
    }
    summaries: list[dict[str, Any]] = []
    for detail in catalogue_details:
        for result in detail.get("results", []):
            if not isinstance(result, dict):
                continue
            dataset = result.get("dataset", {})
            resource_fields_by_table: dict[str, set[str]] = {}
            for resource in result.get("resource", []):
                if not isinstance(resource, dict):
                    continue
                table = _gtfs_table_from_label(str(resource.get("label", "")))
                if not table:
                    continue
                data_descriptor = resource.get("dataDescriptor", {})
                if not isinstance(data_descriptor, dict):
                    continue
                fields = {
                    field
                    for field in data_descriptor
                    if not field.startswith("@") and field not in {"type", "dataDescriptorLabel", "description"}
                }
                resource_fields_by_table[table] = fields
            if not resource_fields_by_table:
                continue
            table_summaries = []
            for table, required_fields in required_fields_by_table.items():
                advertised_fields = sorted(resource_fields_by_table.get(table, set()))
                missing_fields = [field for field in required_fields if field not in advertised_fields]
                if advertised_fields or table == "stop_times":
                    table_summaries.append(
                        {
                            "table": table,
                            "required_fields": required_fields,
                            "advertised_fields": advertised_fields,
                            "missing_required_fields": missing_fields,
                        }
                    )
            summaries.append(
                {
                    "dataset_id": str(dataset.get("id", "")),
                    "dataset_label": str(dataset.get("label", "")),
                    "tables": table_summaries,
                    "advertised_table_fields_ready": not any(
                        table_summary["missing_required_fields"] for table_summary in table_summaries
                    ),
                }
            )
    return summaries


def summarize_bmrcl_export_field_coverage(catalogue_details: Iterable[dict[str, Any]]) -> dict[str, Any]:
    required_fields_by_file = {
        "stations.json": ["stop_code", "stop_name", "location"],
        "lines.json": ["route_id", "route_short_name", "route_long_name", "routeStopSequence", "location"],
        "schedule.json": ["stationCode", "arrival_time", "departure_time", "train_id", "route_id"],
    }
    files_by_name: dict[str, dict[str, Any]] = {}
    for detail in catalogue_details:
        for result in detail.get("results", []):
            if not isinstance(result, dict):
                continue
            dataset = result.get("dataset", {})
            for resource in result.get("resource", []):
                if not isinstance(resource, dict):
                    continue
                export_file = _bmrcl_export_file_from_label(str(resource.get("label", "")))
                if not export_file:
                    continue
                advertised_fields = _descriptor_fields(resource.get("dataDescriptor", {}))
                required_fields = required_fields_by_file[export_file]
                files_by_name[export_file] = {
                    "export_file": export_file,
                    "resource_id": str(resource.get("resourceId", "")),
                    "resource_label": str(resource.get("label", "")),
                    "dataset_id": str(dataset.get("id", "")),
                    "dataset_label": str(dataset.get("label", "")),
                    "resource_type": str(resource.get("resourceType", "")),
                    "required_fields": required_fields,
                    "advertised_fields": sorted(advertised_fields),
                    "missing_required_fields": [
                        field for field in required_fields if field not in advertised_fields
                    ],
                }
    ordered_files = list(required_fields_by_file)
    files = [files_by_name[name] for name in ordered_files if name in files_by_name]
    missing_export_files = [name for name in ordered_files if name not in files_by_name]
    return {
        "required_export_files": ordered_files,
        "export_ready_fields": not missing_export_files
        and not any(row["missing_required_fields"] for row in files),
        "files": files,
        "missing_export_files": missing_export_files,
    }


def _bmrcl_export_file_from_label(label: str) -> str | None:
    normalized = label.lower()
    if "metro station locations" in normalized:
        return "stations.json"
    if "metro rail lines" in normalized:
        return "lines.json"
    if "metro rail schedule" in normalized:
        return "schedule.json"
    return None


def _descriptor_fields(data_descriptor: object) -> set[str]:
    if not isinstance(data_descriptor, dict):
        return set()
    return {
        field
        for field in data_descriptor
        if not field.startswith("@") and field not in {"type", "dataDescriptorLabel", "description"}
    }


def _gtfs_table_from_label(label: str) -> str | None:
    normalized = label.lower().replace("-", " ").replace("_", " ")
    if "stop time" in normalized:
        return "stop_times"
    for table in ["agency", "calendar", "routes", "stops", "trips"]:
        singular = table[:-1] if table.endswith("s") else table
        if f"gtfs {table}" in normalized or f"gtfs {singular}" in normalized:
            return table
    return None


def _sample_coverage_gaps(feeds: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for feed in feeds:
        if "sample" not in str(feed.get("status", "")):
            continue
        coverage_scope = feed.get("coverage_scope")
        if not isinstance(coverage_scope, dict):
            continue
        missing_routes = list(coverage_scope.get("missing_operational_route_short_names", []))
        if coverage_scope.get("coverage_complete") is not False or not missing_routes:
            continue
        feed_id = feed.get("feed_id")
        if not feed_id:
            continue
        gaps.append(
            {
                "feed_id": str(feed_id),
                "expected_operational_route_short_names": list(
                    coverage_scope.get("expected_operational_route_short_names", [])
                ),
                "sample_route_short_names": list(coverage_scope.get("sample_route_short_names", [])),
                "missing_operational_route_short_names": missing_routes,
            }
        )
    return gaps


def _bmrcl_operational_line_scope(feeds: Iterable[dict[str, Any]]) -> dict[str, Any]:
    sample_feed: dict[str, Any] | None = None
    full_feed_id = None
    for feed in feeds:
        feed_id = str(feed.get("feed_id", ""))
        if feed_id == "bengaluru_bmrcl_metro_iudx_sample":
            sample_feed = feed
        elif feed_id == "bengaluru_bmrcl_iudx_full_network_schedule":
            full_feed_id = feed_id

    coverage_scope = sample_feed.get("coverage_scope", {}) if sample_feed else {}
    if not isinstance(coverage_scope, dict):
        coverage_scope = {}
    confirmed = list(coverage_scope.get("expected_operational_route_short_names", []))
    sampled = list(coverage_scope.get("sample_route_short_names", []))
    missing = list(coverage_scope.get("missing_operational_route_short_names", []))
    upcoming = list(coverage_scope.get("unverified_or_upcoming_route_short_names", []))
    return {
        "confirmed_operational_route_short_names": confirmed,
        "confirmed_operational_route_count": len(confirmed),
        "public_iudx_sample_route_short_names": sampled,
        "public_iudx_sample_route_count": len(sampled),
        "missing_from_public_iudx_sample": missing,
        "unverified_or_upcoming_route_short_names": upcoming,
        "coverage_complete": coverage_scope.get("coverage_complete"),
        "sample_feed_id": str(sample_feed.get("feed_id", "")) if sample_feed else None,
        "full_feed_id": full_feed_id,
    }


def _nested_get(payload: dict[str, Any], *path: str) -> Any:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value
