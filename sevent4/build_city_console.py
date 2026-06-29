from __future__ import annotations

import argparse
import dataclasses
import html
import json
from pathlib import Path
from typing import Any

from sevent4.adapters.filesystem import FileCityConsoleInputRepository, FileCityConsolePublicSurface
from sevent4.application.city_console import publish_city_console, publish_city_console_from_repository

from .city_dataset import CityDataset
from .layer_manifest import LayerManifest, LayerSpec


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Municipalities Atlas city console.")
    parser.add_argument("--city", required=True, help="Path to city.yaml")
    parser.add_argument("--layers", required=True, help="Path to layer_manifest.json")
    parser.add_argument("--out", required=True, help="Output HTML path")
    args = parser.parse_args()

    out = Path(args.out)
    build_console_from_files(args.city, args.layers, out)
    print(f"wrote {out}")


def build_console_from_files(city_config: str | Path, layer_manifest: str | Path, out: Path) -> None:
    publish_city_console_from_repository(
        FileCityConsoleInputRepository(city_config, layer_manifest),
        FileCityConsolePublicSurface(out),
        _html,
    )


def build_console(city: CityDataset, manifest: LayerManifest, out: Path) -> None:
    publish_city_console(city, manifest, FileCityConsolePublicSurface(out), _html)


# City readiness is graded because "selectable console" is not the same as
# strong finance, walkability, governance, or source confidence.
CITY_READINESS = {
    "ahmedabad": {
        "console_grade": "full",
        "finance_grade": "strong",
        "walkability_grade": "routable",
        "governance_grade": "strong",
        "source_confidence": "mixed_official",
    },
    "bengaluru": {
        "console_grade": "full",
        "finance_grade": "partial",
        "walkability_grade": "approximate",
        "governance_grade": "partial",
        "source_confidence": "mixed_official",
    },
    "chennai": {
        "console_grade": "full",
        "finance_grade": "partial",
        "walkability_grade": "approximate",
        "governance_grade": "partial",
        "source_confidence": "mixed_official",
    },
    "delhi": {
        "console_grade": "full",
        "finance_grade": "special_case_partial",
        "walkability_grade": "approximate",
        "governance_grade": "special_case",
        "source_confidence": "mixed_official",
    },
    "kolkata": {
        "console_grade": "full",
        "finance_grade": "research_only",
        "walkability_grade": "approximate",
        "governance_grade": "partial",
        "source_confidence": "mixed_official",
    },
    "kanpur": {
        # Ward vector is PARTIAL: DataMeet 2018 has 56 of 110 wards (54 missing). Per-ward
        # population (WorldPop) + heat (Landsat) are valid; the layer is NOT a complete city
        # map and the population sum is NOT the city total. Selectable but flagged skeleton.
        "console_grade": "skeleton",
        "wards_grade": "partial_56_of_110",
        "finance_grade": "missing",
        "walkability_grade": "indicative_osm",
        "governance_grade": "partial",
        "source_confidence": "partial_vector_2018",
    },
    "lucknow": {
        "console_grade": "full",
        "wards_grade": "complete_110",
        "finance_grade": "missing",
        "walkability_grade": "indicative_osm",
        "governance_grade": "partial",
        "source_confidence": "datameet_osm_2011",
    },
}
# The cut-complete cities — full open ward layer + ACs/PCs/OSM + a built jurisdiction
# crosswalk, but no finance/strong-provenance yet. Graded here so they are SELECTABLE
# (a navigable console) while staying honest about the gaps.
for _cid in ("mumbai", "pune", "hyderabad", "jaipur", "kochi", "bhubaneswar", "visakhapatnam"):
    CITY_READINESS.setdefault(_cid, {
        "console_grade": "full",
        "finance_grade": "missing",
        "walkability_grade": "indicative_osm",
        "governance_grade": "partial",
        "source_confidence": "datameet_osm_2011",
    })

# Selectable set, derived from a TRACKED in-repo constant (NOT a scan of the gitignored
# data/ tree, which is empty on a clean checkout). Every onboarded console graded in
# CITY_READINESS is selectable — including the deliberately "skeleton" Kanpur; the grades
# above carry the quality signal separately.
READY_CITIES = set(CITY_READINESS)
ABSENT_CITIES = {
    "Gujarat": ["Surat", "Vadodara", "Rajkot"],
    "Karnataka": ["Mysuru", "Hubballi-Dharwad", "Mangaluru"],
    "Tamil Nadu": ["Coimbatore", "Madurai", "Tiruchirappalli"],
    "West Bengal": ["Howrah", "Siliguri", "Durgapur"],
}
ALL_STATES = [
    "Andhra Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi (NCT)", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Odisha", "Punjab", "Rajasthan", "Tamil Nadu", "Telangana",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
]


def _geo_roster(city: CityDataset) -> tuple[dict, list[str]]:
    """Build {state: {ready, cities:[{id?,name,ready}]}} from sibling city.yaml + curated absentees."""
    root = city.layers_dir.parent.parent  # data/cities/
    by_state: dict[str, list[dict]] = {}
    for yml in sorted(root.glob("*/city.yaml")):
        cid = yml.parent.name
        try:
            cd = CityDataset.from_yaml(str(yml))
            st, nm = cd.state, cd.name
        except Exception:
            continue
        readiness = CITY_READINESS.get(cid, {})
        by_state.setdefault(st, []).append({
            "id": cid,
            "name": nm,
            "ready": cid in READY_CITIES,
            "readiness": readiness,
        })
    for st, names in ABSENT_CITIES.items():
        have = {c["name"] for c in by_state.get(st, [])}
        for n in names:
            if n not in have:
                by_state.setdefault(st, []).append({"name": n, "ready": False})
    for cs in by_state.values():
        cs.sort(key=lambda c: (not c["ready"], c["name"]))
    geo = {st: {"ready": any(c["ready"] for c in cs), "cities": cs} for st, cs in by_state.items()}
    states = sorted(set(ALL_STATES) | set(geo))
    return geo, states


def _state_options(city: CityDataset, geo: dict, states: list[str]) -> str:
    opts: list[str] = []
    for st in states:
        ready = geo.get(st, {}).get("ready", False)
        sel = " selected" if st == city.state else ""
        dis = "" if ready else " disabled"
        opts.append(f'<option value="{html.escape(st)}"{sel}{dis}>{html.escape(st)}</option>')
    return "".join(opts)


def _html(city: CityDataset, manifest: LayerManifest, out_dir: Path | None = None) -> str:
    city_links = _city_extra_links(out_dir)
    finance_url = "finance/" if ("Finance", "finance/index.html") in city_links else None
    canon = _canon_layers(manifest.layers)
    groups = _groups(canon)
    jurisdiction = _jurisdiction_context(city.layers_dir)
    geo, geo_states = _geo_roster(city)
    state_options = _state_options(city, geo, geo_states)
    _wp = city.layers_dir / "wards.geojson"
    # same candidate order as the crosswalk recipe so dropdown labels match the crosswalk keys
    ward_field = _pick_name_field(_wp, ("ward_name", "Name", "name", "ward_no", "WARD_NO")) or "Name"
    ward_options = _feature_options(_wp, ward_field)
    _acp, _pcp = city.layers_dir / "acs.geojson", city.layers_dir / "pcs.geojson"
    ac_field = _pick_name_field(_acp, ("AC_NAME", "ac_name", "ASSEM_CSTNY_NAME", "Name", "name")) if _acp.exists() else None
    pc_field = _pick_name_field(_pcp, ("PC_NAME", "pc_name", "PARLY_CSTNY_NAME", "Name", "name")) if _pcp.exists() else None
    pc_allowed = set(jurisdiction["pcs"]) if jurisdiction["pcs"] else None
    ac_options = _feature_options(_acp, ac_field) if ac_field else ""
    pc_options = _feature_options(_pcp, pc_field, allowed=pc_allowed) if pc_field else ""
    ac_disabled = "" if ac_options else " disabled"
    pc_disabled = "" if pc_options else " disabled"
    ac_label = "Assembly constituency" if ac_options else "Assembly constituency boundary not loaded"
    pc_label = "Parliamentary constituency" if pc_options else "Parliamentary constituency boundary not loaded"
    return f"""<!doctype html>
<html lang="en">
<head>
  <script>(function(){{try{{var t=localStorage.getItem('atlas-theme');if(!t)t=matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';document.documentElement.dataset.theme=t;}}catch(e){{document.documentElement.dataset.theme='dark';}}}})();</script>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="application-name" content="Part IXA: The Municipalities">
  <meta name="theme-color" content="#0a0c10" media="(prefers-color-scheme: dark)">
  <meta name="theme-color" content="#f3f1ea" media="(prefers-color-scheme: light)">
  <title>Part IXA: The Municipalities - {html.escape(city.state)} / {html.escape(city.name)}</title>
  <link rel="icon" type="image/png" href="../../assets/ixa-mark.png?v=stitch-color">
  <link rel="manifest" href="../../site.webmanifest">
  <link rel="stylesheet" href="../../assets/maplibre-gl.css">
  <link rel="stylesheet" href="../../assets/theme.css">
  <link rel="stylesheet" href="../../assets/masthead.css">
  <style>{_css()}</style>
  <script src="../../assets/theme.js" defer></script>
  <script src="../../assets/masthead.js"></script>
</head>
<body>
  <div class="app">
    <aside class="rail">
      <header data-masthead="rail"></header>
      <div class="railjur">
        <div class="jurisdictionbar" aria-label="Current jurisdiction">
          <label><span>State</span><select id="statesel">{state_options}</select></label>
          <label><span>City</span><select id="citysel"></select></label>
        </div>
      </div>
      <div class="scroll">
        <div class="sech">Find layers</div>
        <input id="layerSearch" class="search" type="search" placeholder="Search layers">

        <div class="sech">Layers</div>
        {_toggles(groups)}
        <div class="sech">Read</div>
        <div class="readnote">
          <b>The 74th Amendment</b> is the devolution claim: political and
          financial power should move down from State governments to urban local
          bodies. <b>Article 243W</b> is the map logic: city dysfunction becomes
          visible when responsibility is scattered across jurisdictions,
          representatives, departments, and state-controlled agencies.
          <br><br>
          Ward fill = <b>composite service gap</b>. Use the ward, Assembly
          constituency, and Parliamentary constituency filters above the map.
        </div>
        {_macro_links("../../", city_links)}
      </div>
    </aside>
    <main class="mapwrap"><div id="map"></div>
      <div class="filterbar" aria-label="Geography filters">
        <select id="wardsel" class="fsel"><option value="">Ward</option>{ward_options}</select>
        <select id="acsel" class="fsel{' muted' if ac_disabled else ''}"{ac_disabled}><option value="">{ac_label}</option>{ac_options}</select>
        <select id="pcsel" class="fsel{' muted' if pc_disabled else ''}"{pc_disabled}><option value="">{pc_label}</option>{pc_options}</select>
        <button class="fbtn2" id="resetf" type="button">Default view</button>
        <button class="tbtn" id="theme" type="button" aria-label="Toggle light or dark theme" title="Toggle theme"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3a6.5 6.5 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg></button>
      </div>
      <div class="govpanel" id="govpanel" aria-label="Who governs the selected layer">
        <div id="govbox">
          <div class="sech">Who governs this?</div>
          <div class="govcard" id="govcard">
            <p class="govhint">Turn a layer on to see who actually controls it &mdash; and whether the vote you cast for this city reaches them.</p>
          </div>
        </div>
        <div id="airbox" style="display:none">
          <div class="sech">Who answers for the air?</div>
          <div class="readnote"><span id="airpanel"></span></div>
        </div>
        <div id="heatbox" style="display:none">
          <div class="sech">Whose neighbourhood is the oven?</div>
          <div class="readnote"><span id="heatpanel"></span></div>
        </div>
      </div>
    </main>
  </div>
  <script src="../../assets/maplibre-gl.js"></script>
  <script>
  const city = {json.dumps({"center": city.center, "bbox": city.bbox})};
  const layers = {json.dumps([_layer_json(layer, city) for layer in canon])};
  const jurisdiction = {json.dumps(jurisdiction, ensure_ascii=False)};
  const GEO = {json.dumps(geo, ensure_ascii=False)};
  const CURRENT_STATE = {json.dumps(city.state)};
  const CURRENT_CITY = {json.dumps(city.id)};
  const GOV = {json.dumps(_governance_for_city(city.id, finance_url), ensure_ascii=False)};
  const JURIS_FIELDS = {json.dumps({"ward": ward_field, "ac": ac_field or "ac_name", "pc": pc_field or "pc_name"})};
  {_js()}
  {_air_panel_js()}
  {_heat_panel_js()}
  {_governance_js()}
  </script>
</body>
</html>
"""


def _city_extra_links(out_dir: Path | None) -> tuple[tuple[str, str], ...]:
    if out_dir is None:
        return ()
    links = []
    if (out_dir / "finance" / "index.html").exists():
        links.append(("Finance", "finance/index.html"))
    if (out_dir / "money" / "index.html").exists():
        links.append(("Money", "money/index.html"))
    return tuple(links)


def _macro_links(prefix: str, city_links: tuple[tuple[str, str], ...] = ()) -> str:
    links = (
        ("Home", "index.html"),
        ("Cities", "cities/index.html"),
        ("Why", "why/index.html"),
        ("Findings", "findings/index.html"),
        ("About", "about/index.html"),
    )
    items = "".join(
        f'<a href="{html.escape(prefix + href, quote=True)}">{html.escape(label)}</a>'
        for label, href in links
    )
    items += "".join(
        f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'
        for label, href in city_links
    )
    return f'<nav class="macrotrail" aria-label="Site map">{items}</nav>'


def _air_panel_js() -> str:
    """Sidebar 'Who answers for the air?' card — pairs this city's pollution
    burden (the air_quality layer on the map) with its regulator's vacancy rate,
    read from the published WHY/air roster. Hidden for cities not yet in it."""
    return """
  (function(){
    var box=document.getElementById('airbox'), host=document.getElementById('airpanel');
    if(!box||!host) return;
    fetch('../../why/air/boards.json').then(function(r){return r.json();}).then(function(d){
      var b=(d.boards||[]).find(function(x){return x.city===CURRENT_CITY;});
      if(!b) return;
      if(b.status!=='live'){
        host.innerHTML='<b>'+b.board+'</b> regulates this city\\'s air, but its staffing is <b>not yet on record</b> \\u2014 the RTI that fills it is yours. <a href="../../why/air/index.html">Who answers? &rarr;</a>';
      } else {
        var fin=b.finance_note?(' Yet it is <b>not short of money</b>: it has '+b.finance_note+'.'):'';
        host.innerHTML='<b>'+b.board+'</b> must act on every reading on this map \\u2014 and <b style="color:var(--red)">'+b.vacancy_pct+'% of its posts are vacant</b> ('+b.vacant+' of '+b.sanctioned+').'+fin+' <a href="../../why/air/index.html">Who answers for the air? &rarr;</a>';
      }
      box.style.display='';
    }).catch(function(){});
  })();
"""


def _heat_panel_js() -> str:
    """Sidebar 'Whose neighbourhood is the oven?' card — pairs this city's heat
    layer on the map with its verified urban-heat figures, read from the WHY/heat
    roster. Hidden for cities whose heat figures are not yet primary-verified."""
    return """
  (function(){
    var box=document.getElementById('heatbox'), host=document.getElementById('heatpanel');
    if(!box||!host) return;
    fetch('../../why/heat/cities.json').then(function(r){return r.json();}).then(function(d){
      var h=(d.cities||[]).find(function(x){return x.city===CURRENT_CITY;});
      if(!h||h.status!=='live') return;
      host.innerHTML='This city\\'s land surface hit <b style="color:var(--red)">'+h.lst_peak_c+'\\u00b0C</b> and <b>'+h.heat_stressed_pct+'% of it is persistently heat-stressed</b> \\u2014 green cover fell from '+h.green_cover_then_pct+'% to '+h.green_cover_now_pct+'% in a decade. <a href="../../why/heat/index.html">Whose neighbourhood is the oven? &rarr;</a>';
      box.style.display='';
    }).catch(function(){});
  })();
"""


def _governance_js() -> str:
    """The 'Who governs this?' card. Toggling a layer on pushes it onto a small
    stack and renders that function's governing body, control chip, and verdict;
    toggling off pops it. Exposes window.__govShow(id,on) for the layer handlers."""
    return """
  (function(){
    var card=document.getElementById('govcard');
    if(!card) return;
    var HINT=card.innerHTML, stack=[];
    function esc(s){return String(s).replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
    function labelOf(id){var l=(layers||[]).find(function(x){return x.id===id;});return l?l.label:id;}
    function render(){
      var id=stack[stack.length-1], g=id&&GOV[id];
      if(!g){card.innerHTML=HINT;return;}
      var fin=g.finance?('<a class="govmore" href="'+esc(g.finance)+'">Where the money goes &rarr;</a>'):'';
      card.innerHTML='<span class="govlayer">'+esc(labelOf(id))+'</span>'+
        '<span class="govchip '+g.chipClass+'">'+esc(g.chip)+'</span>'+
        '<div class="govbody">'+g.line+'<span class="govverdict">'+esc(g.verdict)+'</span>'+fin+'</div>';
    }
    window.__govShow=function(id,on){
      if(!GOV[id]) return;
      var i=stack.indexOf(id); if(i>=0) stack.splice(i,1);
      if(on) stack.push(id);
      render();
    };
    // greet with whatever is already switched on (e.g. default wards layer)
    document.querySelectorAll('[data-layer]').forEach(function(cb){
      if(cb.checked && GOV[cb.dataset.layer]) stack.push(cb.dataset.layer);
    });
    render();
  })();
"""


def _layer_json(layer: LayerSpec, city: CityDataset) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": layer.id,
        "label": layer.label,
        "file": layer.file,
        "kind": layer.kind,
        "group": layer.group,
        "default": layer.default,
        "popup": list(layer.popup),
        "paint": layer.paint,
        "outline": layer.outline,
    }
    if layer.kind == "image" and layer.bounds_file:
        bounds = json.loads((city.layers_dir / layer.bounds_file).read_text())
        item["coordinates"] = bounds["corners"]
    if layer.year_field:
        item["yearField"] = layer.year_field
        item["yearValues"] = list(layer.year_values)
        item["defaultYear"] = layer.default_year or (layer.year_values[-1] if layer.year_values else None)
    return item


# Canonical layer panel: one fixed order + label + group + flat colour for every
# shared layer, so the left rail reads identically across all cities. Where a layer's
# paint is data-driven (a MapLibre expression — e.g. ward_heat, service-access wards),
# the colour is left untouched; only a single flat colour key is overridden.
# colour=None means "order/label/group only, keep the layer's own colour".
_CANON: tuple[tuple[str, str, str, str | None], ...] = (
    ("wards", "Wards", "Civic baseline", "#1f6f8b"),
    ("wards_2024", "AMC wards (2024, LGD)", "Civic baseline", None),
    ("districts", "Districts", "Civic baseline", "#c9c2b3"),
    ("villages", "Revenue villages", "Civic baseline", "#8a6f4e"),
    ("landuse", "Land use", "Civic baseline", None),
    ("acs", "Assembly constituencies", "Public jurisdictions", "#5c8af2"),
    ("pcs", "Parliament constituencies", "Public jurisdictions", "#d6a946"),
    ("gba_corporations", "GBA corporations (2025)", "Public jurisdictions", None),
    ("gba_zones", "GBA zones (2025)", "Public jurisdictions", None),
    ("bda_zones", "BDA zones & subdivisions", "Public jurisdictions", None),
    ("bwssb_divisions", "BWSSB divisions", "Public jurisdictions", None),
    ("cmwssb_depots", "CMWSSB depots", "Public jurisdictions", None),
    ("traffic_police_jurisdiction", "Traffic police zones", "Public jurisdictions", None),
    ("roads", "Major roads", "Mobility", "#58606d"),
    ("metro_lines", "Metro lines", "Transit", "#dc4c4c"),
    ("metro", "Metro stations", "Transit", "#dc4c4c"),
    ("rrts", "RRTS (Namo Bharat)", "Transit", "#9b59b6"),
    ("rail", "Suburban rail", "Transit", "#8a8f98"),
    ("suburban_rail", "Suburban rail", "Transit", "#8a8f98"),
    ("corr_amts", "AMTS corridors", "Transit", None),
    ("corr_brts", "BRTS corridors", "Transit", None),
    ("bus_routes", "Bus routes", "Transit", "#e0913a"),
    ("stops", "Bus stops", "Transit", "#9ca3ad"),
    ("libraries", "Libraries", "Public services", "#e0b84d"),
    ("ward_library_exclusion", "Library exclusion", "Public services", None),
    ("schools", "Schools", "Public services", "#1e9f8f"),
    ("health", "Health facilities", "Public services", "#49a35f"),
    ("universities", "Universities", "Public services", None),
    ("police", "Police", "Public services", "#4d76c7"),
    ("fire", "Fire & emergency", "Public services", "#db4c45"),
    ("toilets", "Public toilets", "Public services", "#46c1b4"),
    ("river", "River", "Environment", None),
    ("water", "Water bodies", "Environment", "#3aa0d6"),
    ("drains", "Storm-water drains", "Environment", None),
    ("stormwater_drains", "Storm-water drains", "Environment", None),
    ("flood_hazard", "Flood hazard zones", "Environment", None),
    ("flood_inundation", "Flood inundation depth", "Environment", None),
    ("flood_2015", "2015 flood points", "Environment", None),
    ("sewer_command_area", "Sewerage command areas", "Environment", None),
    ("water_overhead_tanks", "Water overhead tanks", "Environment", None),
    ("bbmp_dry_waste_centres", "Dry-waste centres", "Environment", None),
    ("bbmp_landfills", "Landfills", "Environment", None),
    ("ward_heat", "Ward heat", "Climate", None),
    ("heat30m", "Surface heat (30 m)", "Climate", None),
    ("air_quality", "Air quality (stations)", "Climate", None),
    ("ward_aqi", "Ward air quality", "Climate", None),
    ("ward_workorders", "Ward work-orders", "Finance", None),
    ("ward_workorders_yearly", "Ward work-orders (yearly)", "Finance", None),
    ("ward_analysis", "Ward analysis", "Finance", None),
    ("zone_finance", "Zone finance", "Finance", None),
    ("wards_buses", "Ward bus access", "Civic baseline", None),
)
_CANON_ORDER = {cid: i for i, (cid, *_rest) in enumerate(_CANON)}
_CANON_META = {cid: (label, group, color) for cid, label, group, color in _CANON}


def _canon_layers(layers: tuple[LayerSpec, ...]) -> list[LayerSpec]:
    """Reorder + relabel + recolour layers into the canonical panel (stable for
    unknown ids, which sort to the end keeping their original order)."""
    big = len(_CANON)
    ordered = sorted(
        enumerate(layers), key=lambda iv: (_CANON_ORDER.get(iv[1].id, big), iv[0])
    )
    out: list[LayerSpec] = []
    for _, layer in ordered:
        meta = _CANON_META.get(layer.id)
        if meta:
            label, group, color = meta
            paint = dict(layer.paint)
            if color:
                for key in ("fill-color", "line-color", "circle-color"):
                    if key in paint and not isinstance(paint[key], list):  # keep expressions
                        paint[key] = color
            layer = dataclasses.replace(layer, label=label, group=group, paint=paint)
        out.append(layer)
    return out


def _groups(layers: tuple[LayerSpec, ...]) -> dict[str, list[LayerSpec]]:
    groups: dict[str, list[LayerSpec]] = {}
    for layer in layers:
        groups.setdefault(layer.group, []).append(layer)
    return groups


def _toggles(groups: dict[str, list[LayerSpec]]) -> str:
    """Render the layer panel as collapsible groups, each row carrying a
    geometry-shaped legend swatch so a given layer reads identically in every city."""
    chunks: list[str] = []
    for group, layers in groups.items():
        rows = []
        for layer in layers:
            checked = " checked" if layer.default else ""
            search = f"{group} {layer.label}".lower()
            rows.append(
                f"<label class='tog' data-search='{html.escape(search)}'>"
                f"<input type='checkbox' data-layer='{html.escape(layer.id)}' "
                f"aria-label='Toggle {html.escape(layer.label, quote=True)} layer'{checked}>"
                f"{_legend_swatch(layer)}"
                f"<b>{html.escape(layer.label)}</b>"
                f"{_year_transport(layer)}"
                "</label>"
            )
        on = sum(1 for l in layers if l.default)
        count = f"<span class='lgc'>{on}/{len(layers)}</span>" if on else f"<span class='lgc'>{len(layers)}</span>"
        chunks.append(
            f"<div class='layerGroup'>"
            f"<button type='button' class='lgh' aria-expanded='true'>"
            f"<span class='lgcaret'></span><span class='lgname'>{html.escape(group)}</span>{count}</button>"
            f"<div class='lgb'>{''.join(rows)}</div>"
            f"</div>"
        )
    return "\n".join(chunks)


# A canonical legend swatch keyed on geometry kind, so "Libraries" is the same gold
# dot in every city, "Major roads" the same grey bar, "Wards" the same filled chip.
_SWATCH_SHAPE = {"circle": "sw-dot", "line": "sw-line", "fill": "sw-fill", "image": "sw-img"}


def _legend_swatch(layer: LayerSpec) -> str:
    shape = _SWATCH_SHAPE.get(layer.kind, "sw-fill")
    if _is_graduated(layer.paint):
        # data-driven colour ramp -> show a gradient chip instead of a flat colour
        return f"<span class='sw {shape} sw-grad' aria-hidden='true'></span>"
    color = _legend_color(layer.paint)
    return f"<span class='sw {shape}' style='--swc:{html.escape(color)}' aria-hidden='true'></span>"


def _year_transport(layer: LayerSpec) -> str:
    """Transport control (step back / play-pause / step forward) for a time-series layer,
    driving the same setLayerYear hook the old <select> used."""
    if not layer.year_values:
        return ""
    default = layer.default_year or layer.year_values[-1]
    years = ",".join(str(y) for y in layer.year_values)
    lid = html.escape(layer.id)
    return (
        f"<span class='yearctl' data-year-layer='{lid}' data-years='{years}' "
        f"data-year-field='{html.escape(layer.year_field or '', quote=True)}'>"
        f"<button type='button' class='ybtn' data-yact='back' aria-label='Previous year'>&#9664;</button>"
        f"<button type='button' class='ybtn yplay' data-yact='play' aria-label='Play years'>&#9654;</button>"
        f"<button type='button' class='ybtn' data-yact='fwd' aria-label='Next year'>&#9654;&#9654;</button>"
        f"<span class='ylbl' data-year-label='{lid}'>{default}</span>"
        f"</span>"
    )


def _is_graduated(paint: dict[str, Any]) -> bool:
    return any(isinstance(paint.get(k), list)
               for k in ("circle-color", "line-color", "fill-color"))


def _legend_color(paint: dict[str, Any]) -> str:
    for key in ("circle-color", "line-color", "fill-color"):
        value = paint.get(key)
        if isinstance(value, str):
            return value
    return "#5a86f5"


# ── Educational layer: "Who governs this?" ───────────────────────────────────
# Toggling a layer surfaces the body that actually controls that function, and
# whether it sits under the elected city (your vote reaches it) or a parastatal /
# State agency outside municipal control. This is the atlas thesis — the unelected
# city — made interactive: water in Bengaluru is a State board, in Ahmedabad it is
# the corporation, and the same map layer says exactly that in each city.
#
# Each function template carries a control type and a control-NEUTRAL fact (so it
# stays true whoever runs it); the chip + verdict clause carry the elected/unelected
# judgement. {body} is filled from _CITY_BODIES per city. Lines are authored prose,
# not data — kept honest and short.
_GOV_TEMPLATES: dict[str, dict[str, str]] = {
    "elected": dict(control="city", bodyKey="corp", finance="1",
        line="These are the wards of {body} — the one authority on this map you elect directly. Article 243W says it should run the city; the other layers test how much of that it truly holds."),
    "ward_money": dict(control="city", bodyKey="corp", finance="1",
        line="{body} raises and spends this, ward by ward. It is elected — but most of what a city can spend is tied by the State tier above it."),
    "water": dict(control="parastatal", bodyKey="water",
        line="Piped water and sewerage here are run by {body}."),
    "planning": dict(control="parastatal", bodyKey="planning",
        line="Land use and the master plan are set by {body}, a State development authority whose lines override the elected corporation's wards."),
    "transit_bus": dict(control="parastatal", bodyKey="transit",
        line="City bus service here is run by {body}."),
    "metro": dict(control="parastatal", bodyKey="metro",
        line="The metro is built and run by {body} — a standalone rail company answerable to neither the Mayor nor your councillor."),
    "police": dict(control="state", bodyKey="police",
        line="Policing here is {body}'s. Law and order is not a municipal function; the police answer up to the government above the city, never to the Mayor."),
    "fire": dict(control="state", body="the State fire & emergency service",
        line="Fire & emergency response is run by {body}. The 12th Schedule lists it, but the State staffs and funds it."),
    "libraries": dict(control="state", body="the State library directorate",
        line="Public libraries fall to {body}. The city carries no statutory duty to fund or run a single one — which is how a ward ends up with none."),
    "education": dict(control="shared", body="the State education department",
        line="Most schooling here is {body}'s; the corporation runs, at best, some primary schools. Split mandate, blurred accountability."),
    "health": dict(control="shared", body="the State health department",
        line="Hospitals and primary health are largely {body}'s; the city runs only a thin layer of clinics."),
    "roads": dict(control="shared", body="three different agencies",
        line="These roads are split between the corporation, the State PWD and national highways — {body} you cannot hold to one account."),
    "solid_waste": dict(control="city", bodyKey="corp", finance="1",
        line="Waste collection and disposal is a core 12th-Schedule duty {body} actually holds — one of the few services your vote reaches."),
    "sanitation": dict(control="city", bodyKey="corp", finance="1",
        line="Public toilets and street sanitation are {body}'s own duty — a core 12th-Schedule service your vote reaches."),
    "stormwater": dict(control="shared", bodyKey="corp",
        line="Local drains are {body}'s — but storm-water and flooding spill into the State irrigation / water-resources department, so when your lane floods, responsibility falls between the two."),
    "river": dict(control="state", body="the State water-resources department",
        line="Rivers and major water bodies belong to {body}, not the city — even as the city drinks from them or floods."),
    "environment_air": dict(control="parastatal", bodyKey="pcb",
        line="Air and pollution are policed by {body}, a State board — see 'Who answers for the air?' below."),
    "rail": dict(control="union", body="Indian Railways",
        line="Suburban rail is {body}, a Union undertaking; the city it carries has no seat in how it runs."),
    "assembly": dict(control="state", body="the State Legislative Assembly",
        line="Assembly constituencies elect the State government — the tier that holds most of the money and powers the 74th Amendment was meant to send down."),
    "parliament": dict(control="union", body="Parliament",
        line="Parliamentary constituencies elect the Union government, which writes the terms the city's self-rule lives under."),
    "revenue": dict(control="state", body="the State revenue administration",
        line="Districts and revenue villages are {body}'s units — older than, and overlapping, the municipal map."),
    "reference": dict(control="reference", body="",
        line="A derived or reference layer, not an authority's own record. Read it as context, not as a line of accountability."),
}

# layer id -> function template key
_GOV_LAYER: dict[str, str] = {
    "wards": "elected", "wards_2024": "elected", "wards_buses": "elected",
    "ward_library_exclusion": "elected", "gba_corporations": "elected", "gba_zones": "elected",
    "ward_workorders": "ward_money", "ward_workorders_yearly": "ward_money",
    "ward_analysis": "ward_money", "zone_finance": "ward_money",
    "water": "water", "water_overhead_tanks": "water", "bwssb_divisions": "water",
    "cmwssb_depots": "water", "sewer_command_area": "water",
    "landuse": "planning", "bda_zones": "planning",
    "bus_routes": "transit_bus", "stops": "transit_bus", "corr_amts": "transit_bus", "corr_brts": "transit_bus",
    "metro": "metro", "metro_lines": "metro", "rrts": "metro",
    "rail": "rail", "suburban_rail": "rail",
    "police": "police", "traffic_police_jurisdiction": "police",
    "fire": "fire",
    "libraries": "libraries", "schools": "education", "universities": "education", "health": "health",
    "roads": "roads",
    "toilets": "sanitation",
    "drains": "stormwater", "stormwater_drains": "stormwater",
    "flood_hazard": "stormwater", "flood_inundation": "stormwater", "flood_2015": "stormwater",
    "bbmp_dry_waste_centres": "solid_waste", "bbmp_landfills": "solid_waste",
    "river": "river",
    "air_quality": "environment_air", "ward_aqi": "environment_air",
    "acs": "assembly", "pcs": "parliament",
    "districts": "revenue", "villages": "revenue",
    "heat30m": "reference", "ward_heat": "reference",
}

# city -> function bodyKey -> the actual authority's name
_CITY_BODIES: dict[str, dict[str, str]] = {
    "ahmedabad": dict(corp="the Ahmedabad Municipal Corporation", water="the AMC Water Supply department",
        planning="AUDA", transit="AMTS / Janmarg, run by the AMC", metro="the Gujarat Metro Rail Corp",
        police="the Ahmedabad City Police", pcb="the Gujarat Pollution Control Board"),
    "bengaluru": dict(corp="the Greater Bengaluru / BBMP corporations", water="the BWSSB",
        planning="the BDA", transit="the BMTC", metro="the BMRCL",
        police="the Bengaluru City Police", pcb="the Karnataka State Pollution Control Board"),
    "chennai": dict(corp="the Greater Chennai Corporation", water="CMWSSB (Metrowater)",
        planning="the CMDA", transit="the MTC", metro="the CMRL",
        police="the Greater Chennai Police", pcb="the Tamil Nadu Pollution Control Board"),
    "delhi": dict(corp="the Municipal Corporation of Delhi", water="the Delhi Jal Board",
        planning="the DDA", transit="the DTC", metro="the DMRC",
        police="the Delhi Police (under the Union Home Ministry)", pcb="the Delhi Pollution Control Committee"),
    "kolkata": dict(corp="the Kolkata Municipal Corporation", water="the KMC water-supply wing",
        planning="the KMDA", transit="the WBTC", metro="the Metro Railway (Indian Railways)",
        police="the Kolkata Police", pcb="the West Bengal Pollution Control Board"),
    # Kanpur is a partial skeleton; only the bodyKeys its present layers use are named
    # (corp/police/transit). The other layers render from State-level template defaults.
    "kanpur": dict(corp="the Kanpur Municipal Corporation (Kanpur Nagar Nigam)",
        transit="Kanpur City Transport Services Ltd",
        police="the Kanpur Police Commissionerate"),
    "lucknow": dict(corp="the Lucknow Municipal Corporation (Lucknow Nagar Nigam)",
        water="Jal Sansthan / UP Jal Nigam", planning="the LDA (Lucknow Development Authority)",
        transit="Lucknow City Transport Services Ltd", metro="the UP Metro Rail Corp (Lucknow Metro)",
        police="the Lucknow Police Commissionerate", pcb="the UP Pollution Control Board"),
}

# Where a city breaks the national pattern, override the control verdict.
# Ahmedabad/Kolkata run their own water (elected control); Delhi police is Union;
# Kolkata's metro is Indian Railways; AMC runs its own buses.
_CITY_CONTROL: dict[str, dict[str, str]] = {
    "ahmedabad": {"water": "city", "transit_bus": "city"},
    "kolkata": {"water": "city", "metro": "union"},
    "delhi": {"police": "union"},
}

_GOV_VERDICT: dict[str, str] = {
    "city": "Your vote reaches it.",
    "parastatal": "No councillor you elect controls it.",
    "state": "It answers to the State, not the city.",
    "union": "It answers to the Union, not the city.",
    "shared": "Split mandate — no single body to hold to account.",
    "grace": "You elected who pays — but no law requires them to. It can be starved away, and a ward with none has no claim.",
    "reference": "Context, not a line of accountability.",
}

_GOV_CHIP: dict[str, tuple[str, str]] = {
    "city": ("Elected city", "gc-city"),
    "parastatal": ("Parastatal", "gc-para"),
    "state": ("State govt", "gc-state"),
    "union": ("Union govt", "gc-union"),
    "shared": ("Split mandate", "gc-split"),
    "grace": ("By grace, not right", "gc-grace"),
    "reference": ("Reference", "gc-ref"),
}

# Where a city's lived reality breaks the national function template entirely, override
# the whole card. Ahmedabad libraries are the case: a State subject the 74th Amendment
# never devolved, yet funded ~96% by the elected AMC out of discretion, not duty — so
# neither "State runs it" nor "you elect them" is true. (The "Gujarat has no Public
# Libraries Act" point is kept OUT of the rendered line pending a primary-source cite.)
_CITY_FUNCTION_OVERRIDE: dict[str, dict[str, dict[str, str]]] = {
    "ahmedabad": {
        "libraries": {
            "control": "grace",
            "line": ("Ahmedabad's public libraries are funded almost entirely by "
                     "<b>the AMC</b> — its grant covers ~96% of the M.J. Library network. "
                     "Yet libraries are a State subject the 74th Amendment never placed in "
                     "the 12th Schedule, so the city runs them by choice, not by legal duty."),
        },
    },
}


def _governance_for_city(city_id: str, finance_url: str | None = None) -> dict[str, dict[str, str]]:
    """Resolve the per-layer governance card for one city: control verdict, chip,
    and the body-filled fact line. Returns {layer_id: {...}} for the JS to render.
    finance_url, when the city has a budget page, is attached to the corporation's
    own money-axis layers so 'who governs this' flows into 'where the money goes'."""
    bodies = _CITY_BODIES.get(city_id, {})
    out: dict[str, dict[str, str]] = {}
    for lid, tkey in _GOV_LAYER.items():
        tpl = _GOV_TEMPLATES[tkey]
        control = _CITY_CONTROL.get(city_id, {}).get(tkey, tpl["control"])
        body = bodies.get(tpl["bodyKey"], "") if tpl.get("bodyKey") else tpl.get("body", "")
        filled = "<b>" + html.escape(body) + "</b>" if body else "this body"
        line = tpl["line"].replace("{body}", filled)
        chip_label, chip_class = _GOV_CHIP[control]
        card = {
            "control": control,
            "chip": chip_label,
            "chipClass": chip_class,
            "verdict": _GOV_VERDICT[control],
            "line": line,
        }
        ov = _CITY_FUNCTION_OVERRIDE.get(city_id, {}).get(lid)
        if ov:
            if "control" in ov:
                control = ov["control"]
                chip_label, chip_class = _GOV_CHIP[control]
                card.update(control=control, chip=chip_label, chipClass=chip_class,
                            verdict=ov.get("verdict", _GOV_VERDICT[control]))
            if "line" in ov:
                card["line"] = ov["line"]
        if finance_url and tpl.get("finance"):
            card["finance"] = finance_url
        out[lid] = card
    return out


def _pick_name_field(path: Path, candidates: tuple[str, ...]) -> str | None:
    """First candidate property that exists AND is populated (handles KGIS layers where the
    lowercase `ac_name`/`pc_name` are null but `AC_NAME`/`PARLY_CSTNY_NAME` carry the value)."""
    feats = json.loads(path.read_text()).get("features", [])
    if not feats:
        return None
    bad = {None, "", "None", "nan"}
    ci: dict[str, str] = {}
    for k in feats[0].get("properties", {}):
        ci.setdefault(k.lower(), k)
    for cand in candidates:
        col = cand if cand in feats[0].get("properties", {}) else ci.get(cand.lower())
        if col and any(f.get("properties", {}).get(col) not in bad for f in feats):
            return col
    return None


def _feature_options(
    path: Path,
    label_key: str,
    extra_keys: tuple[str, ...] = (),
    allowed: set[str] | None = None,
) -> str:
    data = json.loads(path.read_text())
    rows = []
    for feature in sorted(data["features"], key=lambda item: str(item["properties"].get(label_key, ""))):
        props = feature["properties"]
        label = str(props.get(label_key, "")).strip()
        if not label or label in ("None", "nan"):
            continue
        if allowed is not None and label not in allowed:
            continue
        bounds = json.dumps(_bbox(feature["geometry"]))
        rings = json.dumps(_rings(feature["geometry"]))
        safe = html.escape(label, quote=True)
        extra_attrs = []
        for key in extra_keys:
            value = str(props.get(key, "")).strip()
            if value:
                attr = key.replace("_", "-")
                extra_attrs.append(f"data-{html.escape(attr)}='{html.escape(value, quote=True)}'")
        attrs = " ".join(extra_attrs)
        if attrs:
            attrs = " " + attrs
        rows.append(f"<option value='{safe}' data-b='{bounds}' data-g='{rings}'{attrs}>{safe}</option>")
    return "".join(rows)


def _jurisdiction_context(layers_dir: Path) -> dict[str, Any]:
    path = layers_dir / "jurisdiction_crosswalk.json"
    empty = {"wards": {}, "acs": {}, "pcs": {}, "records": []}
    if not path.exists():
        return empty
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("records", [])
    index: dict[str, dict[str, dict[str, set[str]]]] = {"wards": {}, "acs": {}, "pcs": {}}
    for row in records:
        ward = str(row.get("ward_name", "")).strip()
        ac = str(row.get("ac_name", "")).strip()
        pc = str(row.get("pc_name", "")).strip()
        district = str(row.get("district_name", "")).strip()
        if not ward or not ac or not pc:
            continue
        _add_index(index["wards"], ward, "acs", ac)
        _add_index(index["wards"], ward, "pcs", pc)
        _add_index(index["wards"], ward, "districts", district)
        _add_index(index["acs"], ac, "wards", ward)
        _add_index(index["acs"], ac, "pcs", pc)
        _add_index(index["acs"], ac, "districts", district)
        _add_index(index["pcs"], pc, "wards", ward)
        _add_index(index["pcs"], pc, "acs", ac)
        _add_index(index["pcs"], pc, "districts", district)
    return {
        "records": records,
        "wards": _freeze_index(index["wards"]),
        "acs": _freeze_index(index["acs"]),
        "pcs": _freeze_index(index["pcs"]),
    }


def _add_index(index: dict[str, dict[str, set[str]]], item: str, key: str, value: str) -> None:
    if not value:
        return
    index.setdefault(item, {}).setdefault(key, set()).add(value)


def _freeze_index(index: dict[str, dict[str, set[str]]]) -> dict[str, dict[str, list[str]]]:
    return {item: {key: sorted(values) for key, values in data.items()} for item, data in sorted(index.items())}


def _bbox(geom: dict[str, Any]) -> list[float]:
    xs: list[float] = []
    ys: list[float] = []

    def walk(coords: Any) -> None:
        if coords and isinstance(coords[0], int | float):
            xs.append(float(coords[0]))
            ys.append(float(coords[1]))
        else:
            for item in coords:
                walk(item)

    walk(geom["coordinates"])
    return [min(xs), min(ys), max(xs), max(ys)]


def _rings(geom: dict[str, Any]) -> list[list[list[float]]]:
    def rounded(ring: list[list[float]]) -> list[list[float]]:
        return [[round(float(x), 4), round(float(y), 4)] for x, y, *_ in ring]

    if geom["type"] == "Polygon":
        return [rounded(geom["coordinates"][0])]
    if geom["type"] == "MultiPolygon":
        return [rounded(poly[0]) for poly in geom["coordinates"]]
    return []


def _css() -> str:
    return """
/* colour tokens (palette + light/dark logic) come from the linked theme.css */
:where(a,button,input,select,[tabindex]):focus-visible{outline:3px solid var(--gold);outline-offset:3px}.macrotrail{display:grid;gap:7px;grid-template-columns:1fr 1fr;margin:14px 0 0}.macrotrail a{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);color:var(--mut);font:800 10px/1 var(--mono);letter-spacing:.1em;padding:9px 10px;text-align:center;text-decoration:none;text-transform:uppercase}.macrotrail a:hover,.macrotrail a:focus-visible{border-color:var(--blue);color:var(--blue)}
*{box-sizing:border-box;margin:0}html,body{height:100%}body{font:400 15px/1.5 var(--sans);color:var(--ink);background:var(--bg);overflow:hidden}.app{display:grid;grid-template-columns:300px 1fr;height:100vh}.rail{background:var(--panel2);border-right:1px solid var(--line);display:flex;flex-direction:column;min-height:0}.rail .mast{background:var(--panel2);border-bottom:1px solid var(--ink);padding:13px 14px 14px}.rail .mast:before{background:var(--ink);content:"";display:block;height:1px;margin-bottom:9px}.brandmark{color:var(--ink);font-family:var(--serif);font-size:27px;font-weight:800;letter-spacing:0;line-height:1}.brandline{border-bottom:1px solid var(--line);color:var(--mut);font:700 9px/1 var(--mono);letter-spacing:.16em;margin:6px 0 10px;padding-bottom:8px;text-transform:uppercase}.jurisdictionbar{display:grid;grid-template-columns:1fr 1fr;gap:8px}.jurisdictionbar label{display:block;min-width:0}.jurisdictionbar label span{color:var(--mut);display:block;font:700 9px/1 var(--mono);letter-spacing:.14em;margin:0 0 5px;text-transform:uppercase}.jurisdictionbar select{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);color:var(--ink);font:700 12px/1 var(--mono);height:44px;padding:0 8px;width:100%}.basis{color:var(--mut);font:700 9px/1.4 var(--mono);letter-spacing:.08em;margin-top:9px;text-transform:uppercase}.rail .scroll{overflow:auto;flex:1;padding:10px 12px}.sech{font:700 11px/1 var(--mono);letter-spacing:.14em;color:var(--mut);text-transform:uppercase;margin:14px 0 6px}.readnote{border-left:2px solid var(--gold);color:var(--mut);font-size:12px;line-height:1.55;padding-left:9px}.readnote b{color:var(--ink)}.search,.fsel{width:100%;min-height:44px;margin-bottom:7px;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:var(--r);padding:9px 10px;font:600 12px var(--mono)}.search::placeholder{color:var(--mut)}.fsel{cursor:pointer}.fsel.muted{color:var(--mut);cursor:not-allowed}.fbtn2{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:var(--r);min-height:44px;padding:8px 12px;font:700 11px var(--mono);cursor:pointer;letter-spacing:.06em}.fbtn2:hover,.tbtn:hover{border-color:var(--blue);color:var(--blue)}.tog{align-items:center;display:flex;flex-wrap:wrap;min-height:44px;padding:6px 4px;border-bottom:1px solid var(--hair);cursor:pointer;font-size:13px}.tog input{vertical-align:-1px;margin-right:7px;accent-color:var(--blue)}.tog .sw{display:inline-block;vertical-align:0;margin-right:6px;background:var(--swc,#5a86f5)}.tog .sw-fill{width:11px;height:11px;border-radius:2px;border:1px solid rgba(255,255,255,.18)}.tog .sw-dot{width:10px;height:10px;border-radius:50%;border:1px solid rgba(255,255,255,.25)}.tog .sw-line{width:14px;height:3px;border-radius:2px;vertical-align:3px}.tog .sw-img{width:11px;height:11px;border-radius:2px;border:1px solid rgba(255,255,255,.18)}.tog .sw-grad{background:linear-gradient(90deg,#2c7a55,#d7b33f,#9f2d2d)}.tog b{font-weight:600}.tog.is-hidden{display:none}.layerGroup{margin:1px 0 3px}.lgh{align-items:center;background:none;border:0;color:var(--mut);cursor:pointer;display:flex;font:700 10px/1 var(--mono);gap:6px;letter-spacing:.13em;min-height:44px;padding:7px 2px;text-transform:uppercase;width:100%}.lgh:hover{color:var(--ink)}.lgname{flex:1;text-align:left}.lgc{color:var(--mut);font:700 9px/1 var(--mono)}.lgcaret{border-bottom:3px solid transparent;border-left:4px solid currentColor;border-top:3px solid transparent;height:0;transform:rotate(90deg);transition:transform .12s;width:0}.layerGroup.collapsed .lgcaret{transform:rotate(0)}.layerGroup.collapsed .lgb{display:none}.lgb{padding-left:2px}.yearctl{align-items:center;display:flex;flex-basis:100%;gap:4px;margin:6px 0 2px 25px}.ybtn{background:var(--panel);border:1px solid var(--line);border-radius:3px;color:var(--ink);cursor:pointer;font:700 9px var(--mono);height:44px;min-width:44px;padding:0 4px}.ybtn:hover,.ybtn.is-playing{border-color:var(--blue);color:var(--blue)}.ylbl{color:var(--ink);font:700 11px var(--mono);min-width:34px;text-align:center}.rail .foot{padding:10px 14px;border-top:1px solid var(--line);font:600 11px/1.5 var(--mono);color:var(--mut)}.mapwrap{position:relative;height:100vh}#map{height:100vh}.filterbar{position:absolute;z-index:2;top:12px;left:12px;right:12px;display:grid;grid-template-columns:minmax(160px,1fr) minmax(150px,1fr) minmax(150px,1fr) auto 44px;gap:8px;align-items:start}.filterbar .fsel,.filterbar .fbtn2,.filterbar .tbtn{height:44px;margin:0;box-shadow:0 2px 10px rgba(0,0,0,.16)}.filterbar .fbtn2{min-width:116px;white-space:nowrap}.tbtn{align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:var(--r);color:var(--ink);cursor:pointer;display:grid;justify-content:center;padding:0;width:44px}.tbtn svg{display:block;fill:none;height:17px;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:2.2;width:17px}.maplibregl-ctrl-group button{height:44px;width:44px}.default-view-ctrl button{color:#333}.default-view-ctrl .default-view-icon{display:grid;height:100%;place-items:center;width:100%}.default-view-ctrl svg{display:block;height:18px;width:18px;fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:2.2}.maplibregl-popup-content{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:6px;font:600 12px/1.5 var(--mono);padding:10px 12px;max-width:320px}.maplibregl-popup-content b{color:var(--ink)}.maplibregl-popup-tip{display:none}.maplibregl-popup-content .k{color:var(--mut)}.hovpop .maplibregl-popup-content{padding:6px 9px;border-left-color:var(--gold);max-width:240px}.hovt .hk{display:block;color:var(--mut);font:700 8px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;margin-bottom:3px}.hovt .hmore{display:block;color:var(--gold);font:700 9px/1 var(--mono);margin-top:3px}.pgrp{margin-bottom:9px}.pgrp:last-child{margin-bottom:0}.pgl{display:block;color:var(--mut);font:700 8px/1 var(--mono);letter-spacing:.13em;text-transform:uppercase;border-bottom:1px solid var(--hair);padding-bottom:3px;margin-bottom:5px}.pf{margin-bottom:6px}.pf:last-child{margin-bottom:0}.pf b{display:block}.pmore{color:var(--gold);font:700 10px var(--mono)}
.brandrow{align-items:center;display:flex;gap:12px;margin-bottom:12px;min-width:0}.ixamark{display:block;flex:0 0 auto;height:58px;width:58px}.wordmark{display:block;min-width:0;white-space:normal}.wordmark span{color:var(--ink);display:block;font-family:var(--serif);font-size:17px;font-weight:700;letter-spacing:0;line-height:1.02}.wordmark b{color:var(--mut);display:block;font:800 8px/1 var(--mono);letter-spacing:.12em;margin-top:5px;text-transform:uppercase}.sitenav{display:grid;gap:7px;grid-template-columns:1fr 1fr;margin:0 0 14px}.sitenav a{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);color:var(--mut);font:800 10px/1 var(--mono);letter-spacing:.12em;padding:9px 10px;text-align:center;text-decoration:none;text-transform:uppercase}.sitenav a.is-active{background:var(--ink);border-color:var(--ink);color:var(--bg)}.sitenav a:not(.is-active):hover{border-color:var(--blue);color:var(--blue)}.basis{text-transform:none}
.brandmark{font-size:21px}
.govpanel{position:absolute;z-index:3;top:62px;right:12px;width:300px;max-width:38vw;max-height:calc(100vh - 84px);overflow-y:auto;background:var(--panel2);border:1px solid var(--line);border-radius:8px;box-shadow:0 4px 18px rgba(0,0,0,.22);padding:2px 12px 12px}.govpanel .sech:first-child{margin-top:9px}#govbox{margin-top:4px}.govcard{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:6px;padding:9px 11px}.govhint{color:var(--mut);font-size:12px;line-height:1.5}.govlayer{display:block;color:var(--mut);font:700 8px/1 var(--mono);letter-spacing:.13em;text-transform:uppercase;margin-bottom:6px}.govchip{display:inline-block;color:#fff;font:700 8px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;padding:3px 6px;border-radius:3px;margin-bottom:7px}.gc-city{background:#2c7a55}.gc-para{background:var(--red)}.gc-state{background:#b07d18}.gc-union{background:var(--blue)}.gc-split{background:#7a6a1e}.gc-grace{background:#a9601f}.gc-ref{background:var(--mut)}.govbody{color:var(--mut);font-size:12px;line-height:1.55}.govbody b{color:var(--ink)}.govverdict{display:block;margin-top:7px;color:var(--ink);font:700 11px/1.4 var(--mono)}.govmore{display:inline-block;margin-top:8px;color:var(--gold);font:700 11px/1 var(--mono);text-decoration:none}.govmore:hover{color:var(--blue)}
@media(max-width:980px){.filterbar{top:54px;right:12px;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.filterbar .fbtn2{min-width:0}.govpanel{top:auto;bottom:10px;left:12px;right:12px;width:auto;max-width:none;max-height:42vh}}@media(max-width:760px){.app{grid-template-columns:1fr;grid-template-rows:auto 1fr}.rail{max-height:34vh}.filterbar{top:10px;left:10px;right:10px;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.filterbar #pcsel{grid-column:1/-1}.filterbar .fsel,.filterbar .fbtn2{height:44px;font-size:11px;padding:8px;min-width:0}#map,.mapwrap{height:66vh}.govpanel{top:auto;bottom:10px;left:10px;right:10px;width:auto;max-width:none;max-height:38vh}}
"""


def _js() -> str:
    return r"""
  // Theme is resolved pre-paint in <head> and toggled by the shared theme.js;
  // the map reads its colours from the same CSS custom properties (themeBg /
  // themeInk) so the palette is never duplicated in JS.
  let hoverPopup = null;

  function DefaultViewControl() {}
  DefaultViewControl.prototype.onAdd = function(mapInstance) {
    this.map = mapInstance;
    this.container = document.createElement("div");
    this.container.className = "maplibregl-ctrl maplibregl-ctrl-group default-view-ctrl";
    const button = document.createElement("button");
    button.type = "button";
    button.title = "Default view";
    button.setAttribute("aria-label", "Default view");
    button.innerHTML = '<span class="default-view-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10.5V20h13v-9.5"/><path d="M9.5 20v-6h5v6"/></svg></span>';
    button.addEventListener("click", () => fitDefaultView(400));
    this.container.appendChild(button);
    return this.container;
  };
  DefaultViewControl.prototype.onRemove = function() {
    this.container.parentNode.removeChild(this.container);
    this.map = undefined;
  };

  const map = new maplibregl.Map({
    container: "map",
    style: {version: 8, sources: {}, layers: [{id: "bg", type: "background", paint: {"background-color": themeBg()}}]},
    center: city.center,
    zoom: 9.7,
    attributionControl: false
  });
  window.__atlasMap = map;
  map.addControl(new maplibregl.NavigationControl({showCompass: false}), "bottom-right");
  map.addControl(new DefaultViewControl(), "bottom-right");

  map.on("load", () => {
    layers.forEach(addLayer);
    addFocusLayers();
    wireInteractions();
    fitDefaultView(0);
  });

  // theme.js owns the #theme button, persistence and the data-theme flip; we
  // only recolour the map's own layers once the new palette is in effect.
  document.addEventListener("atlas:themechange", () => {
    if (map.getLayer("bg")) map.setPaintProperty("bg", "background-color", themeBg());
    if (map.getLayer("focusmask")) map.setPaintProperty("focusmask", "fill-color", themeBg());
    layers.forEach((layer) => {
      const outlineId = `${layer.id}_ln`;
      if (map.getLayer(outlineId)) map.setPaintProperty(outlineId, "line-color", themeInk());
    });
  });
  function fillCities(state) {
    const sel = document.getElementById("citysel");
    sel.innerHTML = "";
    (((GEO[state] || {}).cities) || []).forEach((c) => {
      const o = document.createElement("option");
      o.textContent = c.ready ? c.name : c.name + " — soon";
      o.value = c.id || c.name;
      if (c.ready) {
        o.dataset.url = (c.id === CURRENT_CITY) ? "./index.html" : "../" + c.id + "/index.html";
        if (c.id === CURRENT_CITY) o.selected = true;
      } else {
        o.disabled = true;
      }
      sel.appendChild(o);
    });
  }
  fillCities(CURRENT_STATE);
  document.getElementById("statesel").addEventListener("change", (event) => {
    const first = (((GEO[event.target.value] || {}).cities) || []).find((c) => c.ready);
    if (first && first.id !== CURRENT_CITY) window.location.href = "../" + first.id + "/index.html";
  });
  document.getElementById("citysel").addEventListener("change", (event) => {
    const option = event.target.options[event.target.selectedIndex];
    const url = option && option.dataset.url;
    if (url && url !== "./index.html") window.location.href = url;
  });

  document.querySelectorAll("[data-layer]").forEach((input) => {
    input.addEventListener("change", () => {
      setLayerVisibility(input.dataset.layer, input.checked);
      if (window.__govShow) window.__govShow(input.dataset.layer, input.checked);
    });
  });
  // collapsible layer groups (keeps the panel from reading as a flat laundry list)
  document.querySelectorAll(".lgh").forEach((h) => {
    h.addEventListener("click", () => {
      const g = h.closest(".layerGroup");
      const open = !g.classList.toggle("collapsed");
      h.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });

  // time-series transport: step back / play-pause / step forward through year_values
  document.querySelectorAll(".yearctl").forEach((ctl) => {
    const id = ctl.dataset.yearLayer;
    const years = ctl.dataset.years.split(",").map(Number);
    const lbl = ctl.querySelector(".ylbl");
    const playBtn = ctl.querySelector(".yplay");
    let idx = Math.max(0, years.indexOf(Number(lbl.textContent)));
    let timer = null;
    const show = (i) => {
      idx = (i + years.length) % years.length;
      lbl.textContent = years[idx];
      setLayerYear(id, years[idx]);
      const cb = document.querySelector('[data-layer="' + id + '"]');
      if (cb && !cb.checked) {
        cb.checked = true; setLayerVisibility(id, true);
        if (window.__govShow) window.__govShow(id, true);
      }
    };
    const stop = () => {
      if (timer) { clearInterval(timer); timer = null; }
      playBtn.classList.remove("is-playing");
      playBtn.innerHTML = "▶";
    };
    const play = () => {
      if (timer) { stop(); return; }
      playBtn.classList.add("is-playing");
      playBtn.innerHTML = "⏸";
      timer = setInterval(() => show(idx >= years.length - 1 ? 0 : idx + 1), 900);
    };
    ctl.querySelectorAll(".ybtn").forEach((b) => {
      b.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const act = b.dataset.yact;
        if (act === "back") { stop(); show(idx - 1); }
        else if (act === "fwd") { stop(); show(idx + 1); }
        else { play(); }
      });
    });
  });

  document.getElementById("layerSearch").addEventListener("input", (event) => {
    const q = event.target.value.trim().toLowerCase();
    document.querySelectorAll(".tog").forEach((row) => {
      row.classList.toggle("is-hidden", q && !row.dataset.search.includes(q));
    });
    document.querySelectorAll(".layerGroup").forEach((group) => {
      const shown = group.querySelectorAll(".tog:not(.is-hidden)").length;
      group.classList.toggle("is-hidden", shown === 0);
    });
  });

  document.getElementById("wardsel").addEventListener("change", () => {
    applyJurisdictionFilters();
    updateMapFocus();
  });
  document.getElementById("acsel").addEventListener("change", () => {
    const ac = document.getElementById("acsel").value;
    const pcsel = document.getElementById("pcsel");
    if (ac && !pcsel.value) {
      const pcs = (jurisdiction.acs[ac] && jurisdiction.acs[ac].pcs) || [];
      if (pcs.length === 1) pcsel.value = pcs[0];
    }
    document.getElementById("wardsel").value = "";
    applyJurisdictionFilters();
    updateMapFocus();
  });
  document.getElementById("pcsel").addEventListener("change", () => {
    document.getElementById("wardsel").value = "";
    applyJurisdictionFilters();
    updateMapFocus();
  });
  document.getElementById("resetf").addEventListener("click", resetFocus);
  applyJurisdictionFilters();

  function addLayer(layer) {
    const visibility = layer.default ? "visible" : "none";
    if (layer.kind === "image") {
      map.addSource(layer.id, {type: "image", url: `layers/${layer.file}`, coordinates: layer.coordinates});
      map.addLayer({id: layer.id, type: "raster", source: layer.id, layout: {visibility}, paint: layer.paint});
      return;
    }

    map.addSource(layer.id, {type: "geojson", data: `layers/${layer.file}`});
    map.addLayer({id: layer.id, type: layer.kind, source: layer.id, layout: {visibility}, paint: layer.paint});
    if (layer.outline && layer.kind === "fill") {
      map.addLayer({id: `${layer.id}_ln`, type: "line", source: layer.id, layout: {visibility}, paint: {"line-color": themeInk(), "line-opacity": 0.28, "line-width": 0.7}});
    }
    if (layer.yearField) setLayerYear(layer.id, layer.defaultYear || layer.yearValues[layer.yearValues.length - 1]);
    // interaction is wired once, map-wide (wireInteractions) — not per layer — so
    // overlapping features across layers resolve into one consolidated popup.
  }

  const LMETA = {};
  layers.forEach((l) => { LMETA[l.id] = l; });

  function interactiveLayerIds() {
    return layers
      .filter((l) => l.popup && l.popup.length && l.kind !== "image")
      .map((l) => l.id)
      .filter((id) => map.getLayer(id) && map.getLayoutProperty(id, "visibility") !== "none");
  }

  let clickPopup = null;

  function wireInteractions() {
    // HOVER → brief tooltip for the topmost feature under the cursor (any layer)
    map.on("mousemove", (event) => {
      const ids = interactiveLayerIds();
      const feats = ids.length ? map.queryRenderedFeatures(event.point, {layers: ids}) : [];
      if (!feats.length) {
        map.getCanvas().style.cursor = "";
        if (hoverPopup) { hoverPopup.remove(); hoverPopup = null; }
        return;
      }
      map.getCanvas().style.cursor = "pointer";
      if (!hoverPopup) hoverPopup = new maplibregl.Popup({closeButton: false, closeOnClick: false, className: "hovpop", offset: 10});
      hoverPopup.setLngLat(event.lngLat).setHTML(briefHtml(feats)).addTo(map);
    });
    // CLICK → consolidated detail for EVERY feature under the cursor, grouped by layer
    map.on("click", (event) => {
      const ids = interactiveLayerIds();
      const feats = ids.length ? map.queryRenderedFeatures(event.point, {layers: ids}) : [];
      if (!feats.length) return;
      if (hoverPopup) { hoverPopup.remove(); hoverPopup = null; }
      if (clickPopup) clickPopup.remove();
      clickPopup = new maplibregl.Popup({maxWidth: "340px"}).setLngLat(event.lngLat).setHTML(detailHtml(feats)).addTo(map);
    });
  }

  function addFocusLayers() {
    map.addSource("focusmask", {type: "geojson", data: {type: "FeatureCollection", features: []}});
    map.addLayer({id: "focusmask", type: "fill", source: "focusmask", paint: {"fill-color": themeBg(), "fill-opacity": 0.88}});
    map.addLayer({id: "wards_hi", type: "line", source: "wards", paint: {"line-color": "#edc233", "line-width": 3}, filter: ["==", JURIS_FIELDS.ward, "__none__"]});
    if (map.getSource("acs")) map.addLayer({id: "acs_hi", type: "line", source: "acs", paint: {"line-color": "#edc233", "line-width": 3.4}, filter: ["==", JURIS_FIELDS.ac, "__none__"]});
    if (map.getSource("pcs")) map.addLayer({id: "pcs_hi", type: "line", source: "pcs", paint: {"line-color": "#edc233", "line-width": 3.8}, filter: ["==", JURIS_FIELDS.pc, "__none__"]});
  }

  function setLayerVisibility(id, on) {
    const visibility = on ? "visible" : "none";
    [id, `${id}_ln`].forEach((layerId) => {
      if (map.getLayer(layerId)) map.setLayoutProperty(layerId, "visibility", visibility);
    });
  }

  function setLayerYear(id, year) {
    const layer = layers.find((item) => item.id === id);
    if (!layer || !layer.yearField || !year) return;
    const filter = ["==", layer.yearField, Number(year)];
    [id, `${id}_ln`].forEach((layerId) => {
      if (map.getLayer(layerId)) map.setFilter(layerId, filter);
    });
  }

  function applyJurisdictionFilters() {
    const pcsel = document.getElementById("pcsel");
    const acsel = document.getElementById("acsel");
    const wardsel = document.getElementById("wardsel");
    const hasCrosswalk = Object.keys(jurisdiction.acs || {}).length > 0;
    let allowedAcs = hasCrosswalk ? makeSet(Object.keys(jurisdiction.acs)) : null;
    let allowedWards = hasCrosswalk ? makeSet(Object.keys(jurisdiction.wards || {})) : null;

    if (pcsel.value && jurisdiction.pcs[pcsel.value]) {
      allowedAcs = intersectSets(allowedAcs, makeSet(jurisdiction.pcs[pcsel.value].acs));
      allowedWards = intersectSets(allowedWards, makeSet(jurisdiction.pcs[pcsel.value].wards));
    }
    setOptionAvailability(acsel, allowedAcs);

    if (acsel.value && jurisdiction.acs[acsel.value]) {
      const acWards = makeSet(jurisdiction.acs[acsel.value].wards);
      allowedWards = intersectSets(allowedWards, acWards);
    }
    setOptionAvailability(wardsel, allowedWards);
  }

  function setOptionAvailability(sel, allowed) {
    Array.from(sel.options).forEach((option, index) => {
      if (index === 0) {
        option.hidden = false;
        option.disabled = false;
        return;
      }
      const available = !allowed || allowed.has(option.value);
      option.hidden = !available;
      option.disabled = !available;
    });
    if (sel.value && allowed && !allowed.has(sel.value)) sel.value = "";
  }

  function updateMapFocus() {
    const pcOption = currentOption("pcsel");
    const acOption = currentOption("acsel");
    const wardOption = currentOption("wardsel");
    if (map.getLayer("wards_hi")) map.setFilter("wards_hi", ["==", JURIS_FIELDS.ward, "__none__"]);
    if (map.getLayer("acs_hi")) map.setFilter("acs_hi", ["==", JURIS_FIELDS.ac, "__none__"]);
    if (map.getLayer("pcs_hi")) map.setFilter("pcs_hi", ["==", JURIS_FIELDS.pc, "__none__"]);

    // highlight the selected jurisdiction AND every AC / ward nested inside it
    let acSet = [], wardSet = [];
    const pcVal = pcOption ? pcOption.value : null;
    if (wardOption) {
      wardSet = [wardOption.value];
      acSet = acOption ? [acOption.value] : [];
    } else if (acOption) {
      acSet = [acOption.value];
      wardSet = ((jurisdiction.acs[acOption.value] || {}).wards) || [];
    } else if (pcOption) {
      const info = jurisdiction.pcs[pcOption.value] || {};
      acSet = info.acs || [];
      wardSet = info.wards || [];
    }
    if (pcVal && map.getLayer("pcs_hi")) map.setFilter("pcs_hi", ["==", JURIS_FIELDS.pc, pcVal]);
    if (acSet.length && map.getLayer("acs_hi")) map.setFilter("acs_hi", ["in", JURIS_FIELDS.ac].concat(acSet));
    if (wardSet.length && map.getLayer("wards_hi")) map.setFilter("wards_hi", ["in", JURIS_FIELDS.ward].concat(wardSet));

    const focusOption = wardOption || acOption || pcOption;
    if (!focusOption) {
      setMask(null);
      fitDefaultView(500);
      return;
    }
    setMask(focusOption.dataset.g ? JSON.parse(focusOption.dataset.g) : null);
    if (focusOption.dataset.b) {
      const b = JSON.parse(focusOption.dataset.b);
      map.fitBounds([[b[0], b[1]], [b[2], b[3]]], {padding: 42, duration: 600});
    }
  }

  function resetFocus() {
    ["wardsel", "acsel", "pcsel"].forEach((id) => {
      const el = document.getElementById(id);
      if (el && !el.disabled) el.value = "";
    });
    setOptionAvailability(document.getElementById("wardsel"), null);
    setOptionAvailability(document.getElementById("acsel"), null);
    if (map.getLayer("wards_hi")) map.setFilter("wards_hi", ["==", JURIS_FIELDS.ward, "__none__"]);
    if (map.getLayer("acs_hi")) map.setFilter("acs_hi", ["==", JURIS_FIELDS.ac, "__none__"]);
    if (map.getLayer("pcs_hi")) map.setFilter("pcs_hi", ["==", JURIS_FIELDS.pc, "__none__"]);
    setMask(null);
    fitDefaultView(500);
  }

  function fitDefaultView(duration) {
    map.fitBounds([[city.bbox[0], city.bbox[1]], [city.bbox[2], city.bbox[3]]], {
      padding: defaultViewPadding(),
      duration
    });
  }

  function defaultViewPadding() {
    return window.matchMedia("(max-width: 760px)").matches
      ? {top: 92, right: 18, bottom: 18, left: 18}
      : {top: 68, right: 24, bottom: 24, left: 24};
  }

  function setMask(rings) {
    if (!map.getSource("focusmask")) return;
    const world = [[68, 18], [78, 18], [78, 26], [68, 26], [68, 18]];
    map.getSource("focusmask").setData((rings && rings.length)
      ? {type: "Feature", geometry: {type: "Polygon", coordinates: [world].concat(rings)}}
      : {type: "FeatureCollection", features: []});
  }

  function featureTitle(meta, props) {
    return props.Name || props.name || (meta ? meta.label : "");
  }

  // HOVER: one compact line — the layer it belongs to + the feature name, plus a
  // count when several features sit under the cursor.
  function briefHtml(feats) {
    const f = feats[0];
    const meta = LMETA[f.layer.id] || {label: f.layer.id};
    const extra = feats.length > 1 ? `<span class="hmore">+${feats.length - 1} more here</span>` : "";
    return `<div class="hovt"><span class="hk">${escapeHtml(meta.label)}</span>` +
           `<b>${escapeHtml(clip(String(featureTitle(meta, f.properties || {})), 60))}</b>${extra}</div>`;
  }

  // CLICK: every feature under the cursor, grouped by layer (in panel order),
  // de-duplicated, with the full field detail. One popup, not a stack.
  function detailHtml(feats) {
    const byLayer = {};
    feats.forEach((f) => { (byLayer[f.layer.id] = byLayer[f.layer.id] || []).push(f); });
    const order = layers.map((l) => l.id).filter((id) => byLayer[id]);
    let html = "", shown = 0;
    const CAP = 10;
    for (const id of order) {
      const meta = LMETA[id];
      let section = "", seen = {};
      for (const f of byLayer[id]) {
        const props = f.properties || {};
        const title = String(featureTitle(meta, props));
        if (seen[title]) continue;
        seen[title] = 1;
        if (shown >= CAP) { section += `<div class="pmore">…and more</div>`; break; }
        shown += 1;
        section += featureDetail(meta, props, title);
      }
      if (section) html += `<div class="pgrp"><span class="pgl">${escapeHtml(meta.label)}</span>${section}</div>`;
      if (shown >= CAP) break;
    }
    return html;
  }

  function featureDetail(meta, props, title) {
    const rows = (meta.popup || []).map((key) => {
      const value = props[key] ?? "";
      if (value === "" || key === "Name") return "";
      const limit = key.startsWith("councillors") ? 180 : 96;
      return `<div><span class="k">${escapeHtml(labelFor(key))}:</span> ${escapeHtml(clip(String(value), limit))}</div>`;
    }).join("");
    return `<div class="pf"><b>${escapeHtml(title)}</b>${rows}</div>`;
  }

  // Map layer colours read straight from the active CSS palette (theme.css), so
  // there is no second copy of the hex values here and a theme switch needs only
  // re-reading these custom properties.
  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function themeBg() {
    return cssVar("--bg");
  }

  function themeInk() {
    return cssVar("--ink");
  }

  function clip(value, n) {
    return value.length > n ? `${value.slice(0, n - 1)}...` : value;
  }

  function currentOption(id) {
    const sel = document.getElementById(id);
    if (!sel || !sel.value) return null;
    return sel.options[sel.selectedIndex];
  }

  function makeSet(values) {
    return new Set((values || []).filter(Boolean));
  }

  function intersectSets(left, right) {
    if (!left) return right;
    if (!right) return left;
    return new Set([...left].filter((value) => right.has(value)));
  }

  function labelFor(key) {
    const labels = {
      councillor_count: "Ward councillors",
      councillor_phones: "Councillor contacts",
      councillor_roster_status: "Councillor roster",
      councillors_en: "Councillors",
      councillors_gu: "Councillors Gujarati",
      councillor_parties: "Parties",
      service_priority: "Service priority",
      service_access: "Service access",
      exclusion_index: "Library exclusion index",
      nearest_library_km: "Nearest library (km)",
      double_locked: "Double-locked ward",
      gtfs_stops: "Transit stops",
      mean_lst_c: "Mean surface heat",
      max_lst_c: "Max surface heat",
      pc_name: "Parliamentary constituency",
      ac_name: "Assembly constituency"
    };
    return labels[key] || key.replace(/_/g, " ");
  }

  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[ch]));
  }
"""


if __name__ == "__main__":
    main()
