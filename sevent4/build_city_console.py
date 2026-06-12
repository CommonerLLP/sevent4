from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path
from typing import Any

from .city_dataset import CityDataset
from .layer_manifest import LayerManifest, LayerSpec


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a SevenT4 city console.")
    parser.add_argument("--city", required=True, help="Path to city.yaml")
    parser.add_argument("--layers", required=True, help="Path to layer_manifest.json")
    parser.add_argument("--out", required=True, help="Output HTML path")
    args = parser.parse_args()

    city = CityDataset.from_yaml(args.city)
    manifest = LayerManifest.from_json(args.layers, city)
    out = Path(args.out)
    build_console(city, manifest, out)
    print(f"wrote {out}")


def build_console(city: CityDataset, manifest: LayerManifest, out: Path) -> None:
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    layer_out = out.parent / "layers"
    layer_out.mkdir(parents=True, exist_ok=True)
    _copy_layers(city, manifest, layer_out)
    out.write_text(_html(city, manifest), encoding="utf-8")


def _copy_layers(city: CityDataset, manifest: LayerManifest, layer_out: Path) -> None:
    for layer in manifest.layers:
        shutil.copy2(city.layers_dir / layer.file, layer_out / layer.file)
        if layer.bounds_file:
            shutil.copy2(city.layers_dir / layer.bounds_file, layer_out / layer.bounds_file)
    for sidecar in ("jurisdiction_crosswalk.json",):
        path = city.layers_dir / sidecar
        if path.exists():
            shutil.copy2(path, layer_out / sidecar)


# Cities with a full, deep build (spine + finance/heat/etc.) are SELECTABLE;
# everything else (scaffold consoles + absent major cities) shows GREYED ("coming").
READY_CITIES = {"ahmedabad", "bengaluru", "chennai", "kolkata"}
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
        by_state.setdefault(st, []).append({"id": cid, "name": nm, "ready": cid in READY_CITIES})
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


def _html(city: CityDataset, manifest: LayerManifest) -> str:
    groups = _groups(manifest.layers)
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
    ac_options = _feature_options(_acp, ac_field) if ac_field else ""
    pc_options = _feature_options(_pcp, pc_field) if pc_field else ""
    ac_disabled = "" if ac_options else " disabled"
    pc_disabled = "" if pc_options else " disabled"
    ac_label = "Assembly constituency" if ac_options else "Assembly constituency boundary not loaded"
    pc_label = "Parliamentary constituency" if pc_options else "Parliamentary constituency boundary not loaded"
    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="application-name" content="Part IXA: The Municipalities">
  <meta name="theme-color" content="#f3f1ea">
  <title>Part IXA: The Municipalities - {html.escape(city.state)} / {html.escape(city.name)}</title>
  <link rel="icon" type="image/png" href="../../assets/ixa-mark.png?v=stitch-color">
  <link rel="manifest" href="../../site.webmanifest">
  <link rel="stylesheet" href="../../assets/maplibre-gl.css">
  <style>{_css()}</style>
</head>
<body>
  <div class="app">
    <aside class="rail">
      <div class="mast">
        <div>
          <div class="brandrow">
            <img class="ixamark" src="../../assets/ixa-mark.png?v=stitch-color" alt="" aria-hidden="true">
            <div class="wordmark" aria-label="The Municipalities Accountability Atlas"><span>The Municipalities</span><b>Accountability Atlas</b></div>
          </div>
          <nav class="sitenav" aria-label="Site">
            <a class="is-active" href="./">Atlas</a>
            <a href="../../about/">About</a>
          </nav>
          <div class="jurisdictionbar" aria-label="Current jurisdiction">
            <label><span>State</span><select id="statesel">{state_options}</select></label>
            <label><span>City</span><select id="citysel"></select></label>
          </div>
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
      </div>
    </aside>
    <div class="mapwrap"><div id="map"></div>
      <div class="filterbar" aria-label="Geography filters">
        <select id="wardsel" class="fsel"><option value="">Ward</option>{ward_options}</select>
        <select id="acsel" class="fsel{' muted' if ac_disabled else ''}"{ac_disabled}><option value="">{ac_label}</option>{ac_options}</select>
        <select id="pcsel" class="fsel{' muted' if pc_disabled else ''}"{pc_disabled}><option value="">{pc_label}</option>{pc_options}</select>
        <button class="fbtn2" id="resetf" type="button">Default view</button>
        <button class="tbtn" id="theme" type="button" aria-label="Toggle light or dark theme" title="Toggle theme"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3a6.5 6.5 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg></button>
      </div>
    </div>
  </div>
  <script src="../../assets/maplibre-gl.js"></script>
  <script>
  const city = {json.dumps({"center": city.center, "bbox": city.bbox})};
  const layers = {json.dumps([_layer_json(layer, city) for layer in manifest.layers])};
  const jurisdiction = {json.dumps(jurisdiction, ensure_ascii=False)};
  const GEO = {json.dumps(geo, ensure_ascii=False)};
  const CURRENT_STATE = {json.dumps(city.state)};
  const CURRENT_CITY = {json.dumps(city.id)};
  {_js()}
  </script>
</body>
</html>
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
    return item


def _groups(layers: tuple[LayerSpec, ...]) -> dict[str, list[LayerSpec]]:
    groups: dict[str, list[LayerSpec]] = {}
    for layer in layers:
        groups.setdefault(layer.group, []).append(layer)
    return groups


def _toggles(groups: dict[str, list[LayerSpec]]) -> str:
    chunks: list[str] = []
    for group, layers in groups.items():
        for layer in layers:
            checked = " checked" if layer.default else ""
            color = _legend_color(layer.paint)
            search = f"{group} {layer.label}".lower()
            chunks.append(
                f"<label class='tog' data-search='{html.escape(search)}'>"
                f"<input type='checkbox' data-layer='{html.escape(layer.id)}'{checked}>"
                f"<span class='sw' style='background:{html.escape(color)}'></span>"
                f"<b>{html.escape(layer.label)}</b>"
                "</label>"
            )
    return "\n".join(chunks)


def _legend_color(paint: dict[str, Any]) -> str:
    for key in ("circle-color", "line-color", "fill-color"):
        value = paint.get(key)
        if isinstance(value, str):
            return value
    return "#5a86f5"


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


def _feature_options(path: Path, label_key: str, extra_keys: tuple[str, ...] = ()) -> str:
    data = json.loads(path.read_text())
    rows = []
    for feature in sorted(data["features"], key=lambda item: str(item["properties"].get(label_key, ""))):
        props = feature["properties"]
        label = str(props.get(label_key, "")).strip()
        if not label or label in ("None", "nan"):
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
:root{color-scheme:dark;--bg:#0a0c10;--panel:#13161d;--panel2:#171b23;--ink:#ece9e2;--mut:#8b929f;--line:#262c38;--hair:#1b1f28;--blue:#5a86f5;--red:#f0303d;--gold:#edc233;--r:4px;--serif:Georgia,"Iowan Old Style","Times New Roman",serif;--mono:ui-monospace,Menlo,"SF Mono",Consolas,monospace;--sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
[data-theme=light]{color-scheme:light;--bg:#f3f1ea;--panel:#fff;--panel2:#f6f3ea;--ink:#16181d;--mut:#586071;--line:#d7d1c2;--hair:#e7e2d6;--blue:#22409A;--red:#c8102e;--gold:#9a7b14}
*{box-sizing:border-box;margin:0}html,body{height:100%}body{font:400 15px/1.5 var(--sans);color:var(--ink);background:var(--bg);overflow:hidden}.app{display:grid;grid-template-columns:300px 1fr;height:100vh}.rail{background:var(--panel2);border-right:1px solid var(--line);display:flex;flex-direction:column;min-height:0}.rail .mast{background:var(--panel2);border-bottom:1px solid var(--ink);padding:13px 14px 14px}.rail .mast:before{background:var(--ink);content:"";display:block;height:1px;margin-bottom:9px}.brandmark{color:var(--ink);font-family:var(--serif);font-size:27px;font-weight:800;letter-spacing:0;line-height:1}.brandline{border-bottom:1px solid var(--line);color:var(--mut);font:700 9px/1 var(--mono);letter-spacing:.16em;margin:6px 0 10px;padding-bottom:8px;text-transform:uppercase}.jurisdictionbar{display:grid;grid-template-columns:1fr 1fr;gap:8px}.jurisdictionbar label{display:block;min-width:0}.jurisdictionbar label span{color:var(--mut);display:block;font:700 9px/1 var(--mono);letter-spacing:.14em;margin:0 0 5px;text-transform:uppercase}.jurisdictionbar select{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);color:var(--ink);font:700 12px/1 var(--mono);height:34px;padding:0 8px;width:100%}.basis{color:var(--mut);font:700 9px/1.4 var(--mono);letter-spacing:.08em;margin-top:9px;text-transform:uppercase}.rail .scroll{overflow:auto;flex:1;padding:10px 12px}.sech{font:700 11px/1 var(--mono);letter-spacing:.14em;color:var(--mut);text-transform:uppercase;margin:14px 0 6px}.readnote{border-left:2px solid var(--gold);color:var(--mut);font-size:12px;line-height:1.55;padding-left:9px}.readnote b{color:var(--ink)}.search,.fsel{width:100%;margin-bottom:7px;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:var(--r);padding:9px 10px;font:600 12px var(--mono)}.search::placeholder{color:var(--mut)}.fsel{cursor:pointer}.fsel.muted{color:var(--mut);cursor:not-allowed}.fbtn2{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:var(--r);padding:8px 12px;font:700 11px var(--mono);cursor:pointer;letter-spacing:.06em}.fbtn2:hover,.tbtn:hover{border-color:var(--blue);color:var(--blue)}.tog{display:block;padding:6px 4px;border-bottom:1px solid var(--hair);cursor:pointer;font-size:13px}.tog input{vertical-align:-1px;margin-right:7px;accent-color:var(--blue)}.tog .sw{display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:0;margin-right:6px;border:1px solid rgba(255,255,255,.18)}.tog b{font-weight:600}.tog.is-hidden{display:none}.rail .foot{padding:10px 14px;border-top:1px solid var(--line);font:600 11px/1.5 var(--mono);color:var(--mut)}.mapwrap{position:relative;height:100vh}#map{height:100vh}.filterbar{position:absolute;z-index:2;top:12px;left:12px;right:12px;display:grid;grid-template-columns:minmax(160px,1fr) minmax(150px,1fr) minmax(150px,1fr) auto 38px;gap:8px;align-items:start}.filterbar .fsel,.filterbar .fbtn2,.filterbar .tbtn{height:38px;margin:0;box-shadow:0 2px 10px rgba(0,0,0,.16)}.filterbar .fbtn2{min-width:116px;white-space:nowrap}.tbtn{align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:var(--r);color:var(--ink);cursor:pointer;display:grid;justify-content:center;padding:0;width:38px}.tbtn svg{display:block;fill:none;height:17px;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:2.2;width:17px}.default-view-ctrl button{color:#333}.default-view-ctrl .default-view-icon{display:grid;height:100%;place-items:center;width:100%}.default-view-ctrl svg{display:block;height:18px;width:18px;fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:2.2}.maplibregl-popup-content{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:6px;font:600 12px/1.5 var(--mono);padding:10px 12px;max-width:320px}.maplibregl-popup-content b{color:var(--ink)}.maplibregl-popup-tip{display:none}.maplibregl-popup-content .k{color:var(--mut)}
.brandrow{align-items:center;display:flex;gap:12px;margin-bottom:12px;min-width:0}.ixamark{display:block;flex:0 0 auto;height:58px;width:58px}.wordmark{display:block;min-width:0;white-space:normal}.wordmark span{color:var(--ink);display:block;font-family:var(--serif);font-size:17px;font-weight:700;letter-spacing:0;line-height:1.02}.wordmark b{color:var(--mut);display:block;font:800 8px/1 var(--mono);letter-spacing:.12em;margin-top:5px;text-transform:uppercase}.sitenav{display:grid;gap:7px;grid-template-columns:1fr 1fr;margin:0 0 14px}.sitenav a{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);color:var(--mut);font:800 10px/1 var(--mono);letter-spacing:.12em;padding:9px 10px;text-align:center;text-decoration:none;text-transform:uppercase}.sitenav a.is-active{background:var(--ink);border-color:var(--ink);color:var(--bg)}.sitenav a:not(.is-active):hover{border-color:var(--blue);color:var(--blue)}.basis{text-transform:none}
.brandmark{font-size:21px}
@media(max-width:980px){.filterbar{top:54px;right:12px;grid-template-columns:1fr 1fr}.filterbar .fbtn2{min-width:0}}@media(max-width:760px){.app{grid-template-columns:1fr;grid-template-rows:auto 1fr}.rail{max-height:34vh}.filterbar{top:10px;left:10px;right:10px;grid-template-columns:1fr 1fr}.filterbar .fsel,.filterbar .fbtn2{height:36px;font-size:11px;padding:8px}#map,.mapwrap{height:66vh}}
"""


def _js() -> str:
    return r"""
  const savedTheme = localStorage.getItem("sevent4-theme") || "dark";
  document.documentElement.dataset.theme = savedTheme;
  let hoverPopup = null;

  const map = new maplibregl.Map({
    container: "map",
    style: {version: 8, sources: {}, layers: [{id: "bg", type: "background", paint: {"background-color": themeBg(savedTheme)}}]},
    center: city.center,
    zoom: 9.7,
    attributionControl: false
  });
  map.addControl(new maplibregl.NavigationControl({showCompass: false}), "bottom-right");
  map.addControl(new DefaultViewControl(), "bottom-right");

  map.on("load", () => {
    layers.forEach(addLayer);
    addFocusLayers();
    fitDefaultView(0);
  });

  document.getElementById("theme").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("sevent4-theme", next);
    if (map.getLayer("bg")) map.setPaintProperty("bg", "background-color", themeBg(next));
    if (map.getLayer("focusmask")) map.setPaintProperty("focusmask", "fill-color", themeBg(next));
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
    input.addEventListener("change", () => setLayerVisibility(input.dataset.layer, input.checked));
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
      map.addLayer({id: `${layer.id}_ln`, type: "line", source: layer.id, layout: {visibility}, paint: {"line-color": "var(--ink)", "line-opacity": 0.28, "line-width": 0.7}});
    }
    if (layer.popup.length) {
      map.on("click", layer.id, (event) => showPopup(layer, event));
      map.on("mouseenter", layer.id, () => { map.getCanvas().style.cursor = "pointer"; });
      if (layer.id === "wards") {
        map.on("mousemove", layer.id, (event) => showHoverPopup(layer, event));
      }
      map.on("mouseleave", layer.id, () => {
        map.getCanvas().style.cursor = "";
        if (layer.id === "wards" && hoverPopup) {
          hoverPopup.remove();
          hoverPopup = null;
        }
      });
    }
  }

  function addFocusLayers() {
    map.addSource("focusmask", {type: "geojson", data: {type: "FeatureCollection", features: []}});
    map.addLayer({id: "focusmask", type: "fill", source: "focusmask", paint: {"fill-color": themeBg(document.documentElement.dataset.theme), "fill-opacity": 0.88}});
    map.addLayer({id: "wards_hi", type: "line", source: "wards", paint: {"line-color": "#edc233", "line-width": 3}, filter: ["==", "Name", "__none__"]});
    if (map.getSource("acs")) map.addLayer({id: "acs_hi", type: "line", source: "acs", paint: {"line-color": "#edc233", "line-width": 3.4}, filter: ["==", "ac_name", "__none__"]});
    if (map.getSource("pcs")) map.addLayer({id: "pcs_hi", type: "line", source: "pcs", paint: {"line-color": "#edc233", "line-width": 3.8}, filter: ["==", "pc_name", "__none__"]});
  }

  function setLayerVisibility(id, on) {
    const visibility = on ? "visible" : "none";
    [id, `${id}_ln`].forEach((layerId) => {
      if (map.getLayer(layerId)) map.setLayoutProperty(layerId, "visibility", visibility);
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
    ["wards_hi", "acs_hi", "pcs_hi"].forEach((layerId) => {
      if (map.getLayer(layerId)) {
        const prop = layerId === "wards_hi" ? "Name" : (layerId === "acs_hi" ? "ac_name" : "pc_name");
        map.setFilter(layerId, ["==", prop, "__none__"]);
      }
    });
    if (pcOption && map.getLayer("pcs_hi")) map.setFilter("pcs_hi", ["==", "pc_name", pcOption.value]);
    if (acOption && map.getLayer("acs_hi")) map.setFilter("acs_hi", ["==", "ac_name", acOption.value]);
    if (wardOption && map.getLayer("wards_hi")) map.setFilter("wards_hi", ["==", "Name", wardOption.value]);

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
    if (map.getLayer("wards_hi")) map.setFilter("wards_hi", ["==", "Name", "__none__"]);
    if (map.getLayer("acs_hi")) map.setFilter("acs_hi", ["==", "ac_name", "__none__"]);
    if (map.getLayer("pcs_hi")) map.setFilter("pcs_hi", ["==", "pc_name", "__none__"]);
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

  function showPopup(layer, event) {
    const props = event.features[0].properties || {};
    new maplibregl.Popup()
      .setLngLat(event.lngLat)
      .setHTML(popupHtml(layer, props))
      .addTo(map);
  }

  function showHoverPopup(layer, event) {
    const props = event.features[0].properties || {};
    if (!hoverPopup) hoverPopup = new maplibregl.Popup({closeButton: false, closeOnClick: false});
    hoverPopup.setLngLat(event.lngLat).setHTML(popupHtml(layer, props)).addTo(map);
  }

  function popupHtml(layer, props) {
    const title = props.Name || props.name || layer.label;
    const rows = layer.popup.map((key) => {
      const value = props[key] ?? "";
      if (value === "" || key === "Name") return "";
      const limit = key.startsWith("councillors") ? 180 : 96;
      return `<div><span class="k">${escapeHtml(labelFor(key))}:</span> ${escapeHtml(clip(String(value), limit))}</div>`;
    }).join("");
    return `<b>${escapeHtml(title)}</b>${rows}`;
  }

  function themeBg(theme) {
    return theme === "dark" ? "#0a0c10" : "#f3f1ea";
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
      gtfs_stops: "Transit stops",
      mean_lst_c: "Mean surface heat",
      max_lst_c: "Max surface heat",
      pc_name: "Parliamentary constituency",
      ac_name: "Assembly constituency"
    };
    return labels[key] || key.replace(/_/g, " ");
  }

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

  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[ch]));
  }
"""


if __name__ == "__main__":
    main()
