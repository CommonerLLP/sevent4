from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import asdict
import hashlib
from pathlib import Path
import re
from typing import Any
from urllib.parse import unquote

from sevent4.ports.acquisition import AtlasSourceInventory, OpenDataCatalogueInput, SourceDocument


STRUCTURED_FORMATS = {"CSV", "GEOJSON", "KML", "KMZ", "XLSX", "XLS", "JSON", "SHP", "ZIP"}
# Formats that can actually carry boundary geometry. Tabular formats (CSV/XLS/XLSX)
# are structured but cannot satisfy a slice-by-geometry cut on their own.
GEOMETRY_FORMATS = {"GEOJSON", "KML", "KMZ", "JSON", "SHP", "ZIP"}
OPENCITY_ATLAS_AXES: dict[str, list[str]] = {
    "decides": [
        r"\bward",
        r"councillor",
        r"corporator",
        r"election",
        r"electoral",
        r"voter",
        r"delimitation",
        r"development authority",
        r"\bda\b",
        r"metropolitan",
        r"parastatal",
        r"governance",
        r"council",
        r"municipal council",
        r"mayor",
        r"standing committee",
        r"smart city",
        r"\bspv\b",
        r"jurisdiction",
        r"zone",
        r"administ",
    ],
    "profits": [
        r"land use",
        r"land-use",
        r"\blanduse\b",
        r"\bland\b",
        r"master plan",
        r"\bcdp\b",
        r"\btdr\b",
        r"\bfsi\b",
        r"floor space",
        r"premium",
        r"betterment",
        r"real estate",
        r"property\b(?!.*tax)",
        r"plot",
        r"building perm/?",
        r"layout",
        r"redevelopment",
        r"\bdcr\b",
        r"planning",
        r"survey number",
        r"khata",
    ],
    "pays": [
        r"budget",
        r"finance",
        r"financial",
        r"revenue",
        r"expenditure",
        r"property tax",
        r"\btax\b",
        r"\bcess\b",
        r"user fee",
        r"tariff",
        r"grant",
        r"\bcag\b",
        r"audit",
        r"receipts",
        r"income",
        r"collection",
        r"arrear",
        r"fund",
        r"borrow",
        r"bond",
    ],
    "labours": [
        r"sanitation worker",
        r"conservancy",
        r"safai",
        r"pourakarmika",
        r"contract labour",
        r"contract worker",
        r"\bshg\b",
        r"self help",
        r"\bnulm\b",
        r"welfare",
        r"pension",
        r"manual scaveng",
        r"sewer death",
        r"powrakarmika",
        r"labour",
    ],
    "function": [
        r"water",
        r"sewer",
        r"sewage",
        r"drainage",
        r"solid waste",
        r"\bswm\b",
        r"garbage",
        r"\broad",
        r"transport",
        r"\bbus\b",
        r"metro",
        r"traffic",
        r"mobility",
        r"\bbrts?\b",
        r"health",
        r"hospital",
        r"phc",
        r"clinic",
        r"\bschool",
        r"education",
        r"\bpark",
        r"\bfire\b",
        r"street ?light",
        r"slum",
        r"poverty",
        r"toilet",
        r"public toilet",
        r"\bswd\b",
        r"storm water",
        r"lake",
        r"tree",
        r"environment",
        r"pollution",
        r"air quality",
        r"birth",
        r"death",
        r"\bcrematori",
        r"market",
        r"library",
        r"playground",
    ],
    "base": [
        r"ward boundar",
        r"ward map",
        r"administrative boundar",
        r"admin boundar",
        r"\bboundary",
        r"\bgis\b",
        r"basemap",
        r"base map",
        r"shapefile",
        r"village boundar",
    ],
}
OPENCITY_ATLAS_AXIS_LABELS = {
    "decides": "WHO DECIDES - governance / parastatals / elections / wards",
    "profits": "WHO PROFITS - land / planning / property / rent",
    "pays": "WHO PAYS - budgets / finance / tax / audit",
    "labours": "WHO LABOURS - sanitation / contract / welfare",
    "function": "THE 18 FUNCTIONS - services delivered (or not)",
    "base": "BASE GEOGRAPHY - boundaries / GIS the atlas joins on",
}
OPENCITY_ATLAS_AXIS_PATTERNS = {
    axis: [re.compile(pattern) for pattern in patterns] for axis, patterns in OPENCITY_ATLAS_AXES.items()
}
OPENCITY_CUT_PATTERNS: dict[str, list[str]] = {
    "ward": [r"\bward", r"ward boundar", r"ward map", r"ward delimit"],
    "assembly": [
        r"assembly constituenc",
        r"\bac boundar",
        r"vidhan sabha",
        r"legislative assembly",
        r"\bassembly\b",
        r"\bvidhansabha",
    ],
    "parliament": [r"parliament", r"lok sabha", r"parliamentary constituenc", r"\bpc boundar", r"loksabha"],
}
OPENCITY_CUT_PATTERNS_COMPILED = {
    cut: [re.compile(pattern) for pattern in patterns] for cut, patterns in OPENCITY_CUT_PATTERNS.items()
}
OPENCITY_CUT_LABELS = {"ward": "ward", "assembly": "assembly (AC)", "parliament": "parliament (PC)"}
SHORTLIST_AXES = {"base", "decides", "pays", "function"}
SHORTLIST_TERMS = (
    "budget",
    "ward",
    "boundary",
    "map",
    "statistical handbook",
    "birth",
    "death",
    "transport",
    "bus",
    "metro",
    "vehicle",
    "road",
    "crash",
    "master plan",
    "building bye",
    "air quality",
    "library",
)

INVENTORY_FIELDS = [
    "dataset_name",
    "dataset_title",
    "opencity_url",
    "organization",
    "groups",
    "tags",
    "metadata_modified",
    "axis_labels",
    "shortlist",
    "resource_id",
    "resource_name",
    "resource_format",
    "resource_url",
    "resource_size_bytes",
    "resource_last_modified",
    "resource_mimetype",
    "download_status",
    "local_path",
    "sha256",
    "notes",
]


def opencity_atlas_axis_labels(dataset: dict[str, Any]) -> set[str]:
    haystack = _opencity_scope_haystack(dataset)
    return {
        axis
        for axis, patterns in OPENCITY_ATLAS_AXIS_PATTERNS.items()
        if any(pattern.search(haystack) for pattern in patterns)
    }


def opencity_cut_hits(dataset: dict[str, Any]) -> dict[str, bool]:
    haystack = " ".join(
        [
            str(dataset.get("title") or ""),
            " ".join(str(tag) for tag in dataset.get("tags", [])),
            str(dataset.get("name") or ""),
            str(dataset.get("notes") or ""),
        ]
    ).lower()
    has_geometry = any(
        str(resource.get("format", "")).upper() in GEOMETRY_FORMATS
        for resource in dataset.get("resources", [])
    )
    return {
        cut: bool(has_geometry and any(pattern.search(haystack) for pattern in patterns))
        for cut, patterns in OPENCITY_CUT_PATTERNS_COMPILED.items()
    }


def opencity_resource_formats(dataset: dict[str, Any]) -> str:
    formats = sorted(
        {
            str(resource.get("format", "")).upper()
            for resource in dataset.get("resources", [])
            if resource.get("format")
        }
    )
    return ",".join(formats) or "-"


def opencity_has_structured_resource(dataset: dict[str, Any]) -> bool:
    return any(
        str(resource.get("format", "")).upper() in STRUCTURED_FORMATS
        for resource in dataset.get("resources", [])
    )


def build_opencity_atlas_scope_markdown(
    datasets: list[dict[str, Any]],
    *,
    cities: list[str],
    generator_path: str,
) -> tuple[str, dict[str, int]]:
    lines: list[str] = [
        "# OpenCity -> sevent4 atlas - scoping map (74th Amendment)\n",
        "_What in `data.opencity.in` can improve the atlas. Scoping only - nothing downloaded. "
        f"Generated by `{generator_path}`. "
        "Each dataset is multi-labelled against the four-axis machine + the 18 functions; "
        "a dataset can appear under several axes._\n",
        "\n**Credit line for anything ingested:** every dataset below is published on "
        "OpenCity (`data.opencity.in`) by the listed publisher org; on ingestion we cite "
        "_publisher -> OpenCity -> sevent4 (processed)_ and link the dataset URL.\n",
        "\n_\u2605 = has at least one structured (CSV/GeoJSON/KML/XLSX/JSON) resource - "
        "directly atlas-feedable; unstarred = PDF/scan only._\n",
    ]
    axis_totals: dict[str, int] = {}

    for city in cities:
        city_datasets = [dataset for dataset in datasets if city in (dataset.get("groups") or [])]
        by_axis: dict[str, list[dict[str, Any]]] = {axis: [] for axis in OPENCITY_ATLAS_AXES}
        atlas_relevant = 0
        for dataset in city_datasets:
            hits = opencity_atlas_axis_labels(dataset)
            if hits:
                atlas_relevant += 1
            for axis in hits:
                by_axis[axis].append(dataset)
                axis_totals[axis] = axis_totals.get(axis, 0) + 1

        lines.append(
            f"\n---\n\n## {city.title()}  \u00b7  {len(city_datasets)} datasets  "
            f"\u00b7  {atlas_relevant} atlas-relevant\n"
        )
        summary = "  ".join(f"{axis}:{len(by_axis[axis])}" for axis in OPENCITY_ATLAS_AXES if by_axis[axis])
        lines.append(f"_axis coverage:_ {summary}\n")

        cut_sets: dict[str, list[dict[str, Any]]] = {cut: [] for cut in OPENCITY_CUT_PATTERNS}
        for dataset in city_datasets:
            for cut, ok in opencity_cut_hits(dataset).items():
                if ok:
                    cut_sets[cut].append(dataset)
        verdict = "  ".join(
            f"{OPENCITY_CUT_LABELS[cut]}: {'OK '+str(len(cut_sets[cut])) if cut_sets[cut] else 'none'}"
            for cut in OPENCITY_CUT_PATTERNS
        )
        lines.append(f"\n### CUT GEOMETRY (slice-by) - {verdict}\n")
        for cut in OPENCITY_CUT_PATTERNS:
            if cut_sets[cut]:
                for dataset in cut_sets[cut]:
                    lines.append(
                        f"- _{OPENCITY_CUT_LABELS[cut]}_: **{dataset['title']}** - "
                        f"{dataset.get('organization') or '-'} \u00b7 "
                        f"[{opencity_resource_formats(dataset)}] \u00b7 {dataset.get('url', '')}"
                    )
            else:
                lines.append(
                    f"- _{OPENCITY_CUT_LABELS[cut]}_: **no boundary geometry on OpenCity** - "
                    "source elsewhere (ECI maps / DataMeet / Census / state SEC)."
                )

        for axis in OPENCITY_ATLAS_AXES:
            items = by_axis.get(axis) or []
            if not items:
                continue
            lines.append(f"\n### {OPENCITY_ATLAS_AXIS_LABELS[axis]}  ({len(items)})\n")
            items.sort(
                key=lambda dataset: (
                    not opencity_has_structured_resource(dataset),
                    -int(dataset.get("num_resources") or 0),
                )
            )
            for dataset in items:
                star = "\u2605" if opencity_has_structured_resource(dataset) else " "
                lines.append(
                    f"- {star} **{dataset.get('title', '')}** - {dataset.get('organization') or '-'} \u00b7 "
                    f"{dataset.get('num_resources', 0)} res [{opencity_resource_formats(dataset)}] \u00b7 "
                    f"{dataset.get('url', '')}"
                )

        unmatched = [dataset for dataset in city_datasets if not opencity_atlas_axis_labels(dataset)]
        if unmatched:
            lines.append(f"\n### (unclassified \u2014 {len(unmatched)}; frame may be missing a keyword)\n")
            for dataset in unmatched[:40]:
                lines.append(
                    f"-   {dataset.get('title', '')} - {dataset.get('organization') or '-'} \u00b7 "
                    f"{opencity_resource_formats(dataset)} \u00b7 {dataset.get('url', '')}"
                )
            if len(unmatched) > 40:
                lines.append(f"- _...and {len(unmatched) - 40} more_")

    return "\n".join(lines) + "\n", axis_totals


def _opencity_scope_haystack(dataset: dict[str, Any]) -> str:
    return " ".join(
        [
            str(dataset.get("title") or ""),
            " ".join(str(tag) for tag in dataset.get("tags", [])),
            str(dataset.get("notes") or ""),
            str(dataset.get("organization") or ""),
            str(dataset.get("name") or ""),
        ]
    ).lower()


def city_catalogue_candidate(dataset: dict[str, Any], city: str) -> bool:
    city_key = city.lower()
    groups = [str(group).lower() for group in dataset.get("groups", [])]
    if city_key in groups:
        return True
    if groups:
        return False
    haystack = f"{dataset.get('name', '')} {dataset.get('title', '')}".lower()
    return city_key in haystack


def classify_dataset(dataset: dict[str, Any], classify: Callable[[dict[str, Any]], Iterable[str]]) -> list[str]:
    return sorted(classify(dataset))


def shortlist_dataset(dataset: dict[str, Any]) -> bool:
    axes = set(dataset.get("axis_labels") or [])
    title = f"{dataset.get('title', '')} {dataset.get('name', '')}".lower()
    has_structured = any(
        str(resource.get("format", "")).upper() in STRUCTURED_FORMATS for resource in dataset.get("resources", [])
    )
    if axes & {"base", "decides", "pays"}:
        return True
    if has_structured and axes & SHORTLIST_AXES:
        return True
    return any(term in title for term in SHORTLIST_TERMS)


def enrich_catalogue_datasets(
    datasets: list[dict[str, Any]],
    classify: Callable[[dict[str, Any]], Iterable[str]],
) -> list[dict[str, Any]]:
    enriched = []
    for dataset in datasets:
        row = dict(dataset)
        row["axis_labels"] = classify_dataset(dataset, classify)
        row["shortlist"] = shortlist_dataset(row)
        enriched.append(row)
    return sorted(enriched, key=lambda item: (not item["shortlist"], item.get("title") or item.get("name") or ""))


def flatten_catalogue_inventory_rows(datasets: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for dataset in datasets:
        resources = dataset.get("resources") or [{}]
        for resource in resources:
            rows.append(
                {
                    "dataset_name": str(dataset.get("name") or ""),
                    "dataset_title": str(dataset.get("title") or ""),
                    "opencity_url": str(dataset.get("url") or ""),
                    "organization": str(dataset.get("organization") or ""),
                    "groups": ";".join(str(group) for group in dataset.get("groups", [])),
                    "tags": ";".join(str(tag) for tag in dataset.get("tags", [])),
                    "metadata_modified": str(dataset.get("metadata_modified") or ""),
                    "axis_labels": ";".join(dataset.get("axis_labels") or []),
                    "shortlist": "1" if dataset.get("shortlist") else "0",
                    "resource_id": str(resource.get("id") or ""),
                    "resource_name": str(resource.get("name") or ""),
                    "resource_format": str(resource.get("format") or ""),
                    "resource_url": str(resource.get("url") or ""),
                    "resource_size_bytes": str(resource.get("size_bytes") or ""),
                    "resource_last_modified": str(resource.get("last_modified") or ""),
                    "resource_mimetype": str(resource.get("mimetype") or ""),
                    "download_status": "not_downloaded",
                    "local_path": "",
                    "sha256": "",
                    "notes": "OpenCity catalogue inventory row; resource not promoted into city source tree yet.",
                }
            )
    return rows


def build_atlas_source_inventory(
    catalogue: OpenDataCatalogueInput,
    city: str,
    classify: Callable[[dict[str, Any]], Iterable[str]],
    inventory_filename: str,
    shortlist_filename: str,
) -> AtlasSourceInventory:
    datasets = enrich_catalogue_datasets(
        [dataset for dataset in catalogue.datasets if city_catalogue_candidate(dataset, city)],
        classify,
    )
    inventory_rows = flatten_catalogue_inventory_rows(datasets)
    shortlist_rows = [row for row in inventory_rows if row["shortlist"] == "1"]
    return AtlasSourceInventory(
        inventory_rows=inventory_rows,
        shortlist_rows=shortlist_rows,
        manifest={
            "source_catalogue": catalogue.source_catalogue,
            "dataset_count": len(datasets),
            "resource_row_count": len(inventory_rows),
            "shortlist_resource_row_count": len(shortlist_rows),
            "outputs": {
                "inventory_csv": inventory_filename,
                "shortlist_csv": shortlist_filename,
            },
            "notes": (
                "Inventory only. Resource downloads/promotions must preserve publisher, OpenCity URL, "
                "resource URL, checksum, rights text where available, and atlas-axis labels."
            ),
        },
    )


def build_document_manifest(
    documents: list[SourceDocument],
    *,
    generated_at: str,
    scope: str,
    sources: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "scope": scope,
        "sources": sources,
        "documents": [asdict(document) for document in documents],
    }


def build_runlog_record(
    documents: list[SourceDocument],
    *,
    tool: str,
    scope: str,
    started_at: str,
    ended_at: str,
    sources: dict[str, Any],
) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for document in documents:
        statuses[document.status] = statuses.get(document.status, 0) + 1
    return {
        "run_id": hashlib.sha256(f"{started_at}:{scope}:{len(documents)}".encode()).hexdigest()[:16],
        "tool": tool,
        "scope": scope,
        "started_at": started_at,
        "ended_at": ended_at,
        "documents": len(documents),
        "statuses": statuses,
        "sources": sources,
    }


STAFFING_FIELDS = [
    "year",
    "source_url",
    "archive_pdf_path",
    "total_posts_sanctioned",
    "total_posts_filled",
    "total_posts_vacant",
    "professional_posts_sanctioned",
    "ministerial_posts_sanctioned",
    "professional_posts_filled",
    "ministerial_posts_filled",
    "professional_posts_vacant",
    "ministerial_posts_vacant",
    "vacancy_rate_pct",
    "extraction_status",
    "notes",
]


def google_drive_download_url(url: str) -> str:
    match = re.search(r"drive\.google\.com/file/d/([^/]+)/", url)
    if not match:
        return url
    return f"https://drive.google.com/uc?export=download&id={match.group(1)}"


def text_needs_ocr(text: str, *, min_chars: int = 2000) -> bool:
    alpha_num = re.findall(r"[A-Za-z0-9]", text)
    return len(alpha_num) < min_chars


def parse_dpl_staffing_text(year: str, text: str) -> dict[str, str]:
    collapsed = " ".join(text.replace("\xa0", " ").split())
    row = empty_staffing_row(year)

    table_match = re.search(
        r"Total Posts Sanctioned\s*:\s*(\d+)\s+Filled\s*up(?:\s+Post)?\s*:\s*(\d+)\s+Vacant\s*Post\s*:\s*(\d+)(.{0,260})",
        collapsed,
        flags=re.I,
    )
    if table_match:
        sanctioned, filled, vacant, tail = table_match.groups()
        row.update(
            {
                "total_posts_sanctioned": sanctioned,
                "total_posts_filled": filled,
                "total_posts_vacant": vacant,
                "vacancy_rate_pct": vacancy_rate(sanctioned, vacant),
                "extraction_status": "observed_total_only",
                "notes": "Annual report staffing table parsed from text.",
            }
        )
        numbers = re.findall(r"\b\d+\b", tail)
        if len(numbers) >= 6:
            row.update(
                {
                    "professional_posts_sanctioned": numbers[0],
                    "ministerial_posts_sanctioned": numbers[1],
                    "professional_posts_filled": numbers[2],
                    "ministerial_posts_filled": numbers[3],
                    "professional_posts_vacant": numbers[4],
                    "ministerial_posts_vacant": numbers[5],
                    "extraction_status": "observed_split",
                }
            )
        elif len(numbers) >= 2:
            row.update(
                {
                    "professional_posts_sanctioned": numbers[0],
                    "ministerial_posts_sanctioned": numbers[1],
                }
            )
        return row

    prose_match = re.search(
        r"sanctioned staff strength of\s+(\d+)\s+comprising of\s+(\d+)\s+professionals?\s+and\s+(\d+)\s+Non-Professionals?,\s+out of which\s+(\d+)\s+posts?\s+are\s+lying\s+vacant",
        collapsed,
        flags=re.I,
    )
    if prose_match:
        sanctioned, professional, ministerial, vacant = prose_match.groups()
        filled = str(int(sanctioned) - int(vacant))
        row.update(
            {
                "total_posts_sanctioned": sanctioned,
                "total_posts_filled": filled,
                "total_posts_vacant": vacant,
                "professional_posts_sanctioned": professional,
                "ministerial_posts_sanctioned": ministerial,
                "vacancy_rate_pct": vacancy_rate(sanctioned, vacant),
                "extraction_status": "observed_total_only",
                "notes": "Annual report prose staffing paragraph parsed from text.",
            }
        )
        return row

    row["extraction_status"] = "not_found"
    row["notes"] = "No comparable staffing table found in extracted text; OCR/manual review may be required."
    return row


def empty_staffing_row(year: str) -> dict[str, str]:
    return {field: "" for field in STAFFING_FIELDS} | {"year": year}


def vacancy_rate(sanctioned: str, vacant: str) -> str:
    return f"{int(vacant) / int(sanctioned) * 100:.1f}"


DPL_TERMS = (
    "delhi public library",
    "delhi library board",
)
DPL_CONTEXT_TERMS = (
    "dpl",
    "staff",
    "vacanc",
    "recruit",
    "post",
    "mobile",
    "branch",
    "modern",
    "digital",
    "grant",
    "ministry of culture",
    "raja rammohun",
    "rrrlf",
    "national mission on libraries",
)


def parliament_probe_filter(title: str, query: str) -> bool:
    haystack = f"{title or ''} {query or ''}".lower()
    if any(term in haystack for term in DPL_TERMS):
        return True
    return "delhi" in haystack and any(term in haystack for term in DPL_CONTEXT_TERMS)


def parse_session_range(value: str) -> list[int]:
    out: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = [int(x.strip()) for x in part.split("-", 1)]
            out.extend(range(start, end + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


def classify_mj_library_pdf(
    context: str,
    url: str,
    year: str,
    proactive_context: bool = False,
) -> str:
    filename = Path(unquote(url)).name.lower()
    if "annual_report" in filename:
        return "rti_annual_report"
    if "fee" in filename:
        return "fees"
    if filename.startswith("admissionform") or filename == "mj-membership-and-gaurantor-form.pdf":
        return "forms"
    if "listappofficer" in filename or "listpio" in filename:
        return "rti_officers"
    if filename in {
        "rightofinformationact2005.pdf",
        "rtiact2005gujarati.pdf",
        "gad.pdf",
        "rulesorder.pdf",
        "rulesorderguj.pdf",
        "goggazzateeng.pdf",
        "rtirulegujarati.pdf",
    }:
        return "rules_orders"
    if filename == "list_of_ccc.pdf":
        return "civic_centres"
    haystack = f"{context} {url}".lower()
    if proactive_context and year:
        return "proactive_disclosure"
    if "annual_report" in haystack or "annual report" in haystack:
        return "rti_annual_report"
    if "fee" in haystack:
        return "fees"
    if "form" in haystack:
        return "forms"
    if "rule" in haystack or "gazette" in haystack or "notification" in haystack:
        return "rules_orders"
    if "p.i.o" in haystack or "pio" in haystack or "applet officer" in haystack:
        return "rti_officers"
    return "other"


def mj_library_year_from_text(text: str) -> str | None:
    match = re.search(r"(20\d{2})\s*[-_]\s*(20\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)[-2:]}"
    match = re.search(r"(20\d{2})\s*[-_]\s*(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    match = re.search(r"(?<!\d)(20\d{2})(\d{2})(?!\d)", text)
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        if end == (start + 1) % 100:
            return f"{start}-{match.group(2)}"
    match = re.search(
        r"\b(2015|2016|2017|2018|2019|2020|2021|2022|2023|2024|2025)\s*[-_]\s*(16|17|18|19|20|21|22|23|24|25|26)\b",
        text,
    )
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None


def mj_library_proactive_disclosure_year(prefix: str) -> str | None:
    years = re.findall(r"PRO\s+ACTIVE\s+DISCLOSURE\s+(20\d{2})\s*[-_]\s*(\d{2})", prefix, flags=re.I)
    if not years:
        return None
    start, end = years[-1]
    return f"{start}-{end}"
