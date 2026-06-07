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


def _html(city: CityDataset, manifest: LayerManifest) -> str:
    groups = _groups(manifest.layers)
    ward_options = _feature_options(city.layers_dir / "wards.geojson", "Name")
    ac_options = _feature_options(city.layers_dir / "acs.geojson", "ac_name") if (city.layers_dir / "acs.geojson").exists() else ""
    pc_options = _feature_options(city.layers_dir / "pcs.geojson", "pc_name") if (city.layers_dir / "pcs.geojson").exists() else ""
    ac_disabled = "" if ac_options else " disabled"
    pc_disabled = "" if pc_options else " disabled"
    ac_label = "AC" if ac_options else "AC boundary not loaded"
    pc_label = "PC" if pc_options else "PC boundary not loaded"
    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(city.name)} City Intelligence - SevenT4</title>
  <link rel="stylesheet" href="../../assets/maplibre-gl.css">
  <style>{_css()}</style>
</head>
<body>
  <div class="app">
    <aside class="rail">
      <div class="mast">
        <div>
          <div class="amendment">Seventy-fourth Amendment</div>
          <h1>{html.escape(city.name)}</h1>
        </div>
      </div>
      <div class="scroll">
        <div class="sech">Find layers</div>
        <input id="layerSearch" class="search" type="search" placeholder="Search layers">

        <div class="sech">Focus geography</div>
        <select id="wardsel" class="fsel"><option value="">Ward</option>{ward_options}</select>
        <select id="councillorsel" class="fsel muted" disabled><option>Councillor data not loaded</option></select>
        <select id="acsel" class="fsel{' muted' if ac_disabled else ''}"{ac_disabled}><option value="">{ac_label}</option>{ac_options}</select>
        <select id="pcsel" class="fsel{' muted' if pc_disabled else ''}"{pc_disabled}><option value="">{pc_label}</option>{pc_options}</select>
        <button class="fbtn2" id="resetf" type="button">Reset view</button>

        <div class="sech">Layers</div>
        {_toggles(groups)}
        <div class="sech">Read</div>
        <div style="font-size:12px;color:var(--mut);line-height:1.6">
          Ward fill = <b>composite service gap</b>. Select a ward, AC, or PC to
          spotlight the responsible public geography. <b>Click any feature</b>
          for details.</div>
      </div>
      <div class="foot">
        SevenT4 · GPU/WebGL · offline · public jurisdictions
      </div>
    </aside>
    <div class="mapwrap"><div id="map"></div>
      <div class="tbar"><button class="tbtn" id="theme" type="button" aria-label="Toggle light or dark theme">◐ DAY/NIGHT</button></div>
    </div>
  </div>
  <script src="../../assets/maplibre-gl.js"></script>
  <script>
  const city = {json.dumps({"center": city.center, "bbox": city.bbox})};
  const layers = {json.dumps([_layer_json(layer, city) for layer in manifest.layers])};
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


def _feature_options(path: Path, label_key: str) -> str:
    data = json.loads(path.read_text())
    rows = []
    for feature in sorted(data["features"], key=lambda item: str(item["properties"].get(label_key, ""))):
        label = str(feature["properties"].get(label_key, "")).strip()
        if not label:
            continue
        bounds = json.dumps(_bbox(feature["geometry"]))
        rings = json.dumps(_rings(feature["geometry"]))
        safe = html.escape(label, quote=True)
        rows.append(f"<option value='{safe}' data-b='{bounds}' data-g='{rings}'>{safe}</option>")
    return "".join(rows)


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
        return [[round(float(x), 4), round(float(y), 4)] for x, y in ring]

    if geom["type"] == "Polygon":
        return [rounded(geom["coordinates"][0])]
    if geom["type"] == "MultiPolygon":
        return [rounded(poly[0]) for poly in geom["coordinates"]]
    return []


def _css() -> str:
    return """
:root{color-scheme:dark;--bg:#0a0c10;--panel:#13161d;--panel2:#171b23;--ink:#ece9e2;--mut:#8b929f;--line:#262c38;--hair:#1b1f28;--blue:#5a86f5;--red:#f0303d;--gold:#edc233;--r:4px;--serif:Georgia,"Iowan Old Style","Times New Roman",serif;--mono:ui-monospace,Menlo,"SF Mono",Consolas,monospace;--sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
[data-theme=light]{color-scheme:light;--bg:#f3f1ea;--panel:#fff;--panel2:#f6f3ea;--ink:#16181d;--mut:#586071;--line:#d7d1c2;--hair:#e7e2d6;--blue:#22409A;--red:#c8102e;--gold:#9a7b14}
*{box-sizing:border-box;margin:0}html,body{height:100%}body{font:400 15px/1.5 var(--sans);color:var(--ink);background:var(--bg);overflow:hidden}.app{display:grid;grid-template-columns:300px 1fr;height:100vh}.rail{background:var(--panel2);border-right:1px solid var(--line);display:flex;flex-direction:column;min-height:0}.rail .mast{display:flex;align-items:center;gap:12px;padding:16px;border-bottom:1px solid var(--line)}.rail .mast .mk{height:34px;width:auto}.rail .mast .amendment{font-family:var(--serif);font-weight:700;font-size:15px;line-height:1.05;color:var(--ink);letter-spacing:0}.rail .mast h1{font-family:var(--serif);font-size:18px;line-height:1.05;margin-top:4px;color:var(--mut);font-weight:400}.rail .scroll{overflow:auto;flex:1;padding:10px 12px}.sech{font:700 11px/1 var(--mono);letter-spacing:.14em;color:var(--mut);text-transform:uppercase;margin:14px 0 6px}.search,.fsel{width:100%;margin-bottom:7px;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:var(--r);padding:9px 10px;font:600 12px var(--mono)}.search::placeholder{color:var(--mut)}.fsel{cursor:pointer}.fsel.muted{color:var(--mut);cursor:not-allowed}.fbtn2{width:100%;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:var(--r);padding:8px;font:600 11px var(--mono);cursor:pointer;letter-spacing:.06em}.fbtn2:hover{border-color:var(--blue);color:var(--blue)}.tog{display:block;padding:6px 4px;border-bottom:1px solid var(--hair);cursor:pointer;font-size:13px}.tog input{vertical-align:-1px;margin-right:7px;accent-color:var(--blue)}.tog .sw{display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:0;margin-right:6px;border:1px solid rgba(255,255,255,.18)}.tog b{font-weight:600}.tog.is-hidden{display:none}.rail .foot{padding:10px 14px;border-top:1px solid var(--line);font:600 11px/1.5 var(--mono);color:var(--mut)}.mapwrap{position:relative;height:100vh}#map{height:100vh}.maplibregl-popup-content{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:6px;font:600 12px/1.5 var(--mono);padding:10px 12px;max-width:300px}.maplibregl-popup-content b{color:var(--ink)}.maplibregl-popup-tip{display:none}.maplibregl-popup-content .k{color:var(--mut)}.tbar{position:absolute;top:12px;right:12px;display:flex;gap:8px}.tbtn{background:var(--panel);border:1px solid var(--line);color:var(--ink);border-radius:var(--r);padding:8px 12px;font:600 12px/1 var(--mono);cursor:pointer}.tbtn:hover{border-color:var(--blue);color:var(--blue)}
@media(max-width:760px){.app{grid-template-columns:1fr;grid-template-rows:auto 1fr}.rail{max-height:42vh}#map,.mapwrap{height:58vh}}
"""


def _js() -> str:
    return r"""
  const savedTheme = localStorage.getItem("sevent4-theme") || "dark";
  document.documentElement.dataset.theme = savedTheme;

  const map = new maplibregl.Map({
    container: "map",
    style: {version: 8, sources: {}, layers: [{id: "bg", type: "background", paint: {"background-color": themeBg(savedTheme)}}]},
    center: city.center,
    zoom: 9.7,
    attributionControl: false
  });
  map.addControl(new maplibregl.NavigationControl({showCompass: false}), "top-left");

  map.on("load", () => {
    layers.forEach(addLayer);
    addFocusLayers();
    const bounds = [[city.bbox[0], city.bbox[1]], [city.bbox[2], city.bbox[3]]];
    map.fitBounds(bounds, {padding: 28, duration: 0});
  });

  document.getElementById("theme").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("sevent4-theme", next);
    if (map.getLayer("bg")) map.setPaintProperty("bg", "background-color", themeBg(next));
    if (map.getLayer("focusmask")) map.setPaintProperty("focusmask", "fill-color", themeBg(next));
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

  document.getElementById("wardsel").addEventListener("change", (event) => focusWard(event.target));
  document.getElementById("acsel").addEventListener("change", (event) => focusJurisdiction(event.target, "acs_hi", "ac_name", ["wardsel", "pcsel"]));
  document.getElementById("pcsel").addEventListener("change", (event) => focusJurisdiction(event.target, "pcs_hi", "pc_name", ["wardsel", "acsel"]));
  document.getElementById("resetf").addEventListener("click", resetFocus);

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
      map.on("mouseleave", layer.id, () => { map.getCanvas().style.cursor = ""; });
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

  function focusWard(sel) {
    focusJurisdiction(sel, "wards_hi", "Name", ["acsel", "pcsel"]);
  }

  function focusJurisdiction(sel, highlightLayer, property, others) {
    const option = sel.options[sel.selectedIndex];
    if (!option.value) return resetFocus();
    others.forEach((id) => {
      const other = document.getElementById(id);
      if (other && !other.disabled) other.value = "";
    });
    ["wards_hi", "acs_hi", "pcs_hi"].forEach((layerId) => {
      if (map.getLayer(layerId)) {
        const prop = layerId === "wards_hi" ? "Name" : (layerId === "acs_hi" ? "ac_name" : "pc_name");
        map.setFilter(layerId, ["==", prop, "__none__"]);
      }
    });
    if (map.getLayer(highlightLayer)) map.setFilter(highlightLayer, ["==", property, option.value]);
    setMask(option.dataset.g ? JSON.parse(option.dataset.g) : null);
    if (option.dataset.b) {
      const b = JSON.parse(option.dataset.b);
      map.fitBounds([[b[0], b[1]], [b[2], b[3]]], {padding: 42, duration: 600});
    }
  }

  function resetFocus() {
    ["wardsel", "acsel", "pcsel"].forEach((id) => {
      const el = document.getElementById(id);
      if (el && !el.disabled) el.value = "";
    });
    if (map.getLayer("wards_hi")) map.setFilter("wards_hi", ["==", "Name", "__none__"]);
    if (map.getLayer("acs_hi")) map.setFilter("acs_hi", ["==", "ac_name", "__none__"]);
    if (map.getLayer("pcs_hi")) map.setFilter("pcs_hi", ["==", "pc_name", "__none__"]);
    setMask(null);
    map.fitBounds([[city.bbox[0], city.bbox[1]], [city.bbox[2], city.bbox[3]]], {padding: 28, duration: 500});
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
    let title = props.Name || props.name || layer.label;
    let rows = layer.popup.map((key) => {
      const value = props[key] ?? "";
      if (value === "") return "";
      return `<div><span class="k">${escapeHtml(key.replace(/_/g, " "))}:</span> ${escapeHtml(clip(String(value), 72))}</div>`;
    }).join("");
    new maplibregl.Popup()
      .setLngLat(event.lngLat)
      .setHTML(`<b>${escapeHtml(title)}</b>${rows}`)
      .addTo(map);
  }

  function themeBg(theme) {
    return theme === "dark" ? "#0a0c10" : "#f3f1ea";
  }

  function clip(value, n) {
    return value.length > n ? `${value.slice(0, n - 1)}...` : value;
  }

  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[ch]));
  }
"""


if __name__ == "__main__":
    main()
