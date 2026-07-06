"""Build a Sankey-style public-finance flow page.

Usage:
    python3 -m sevent4.finance.build_finance_flow \
        --city data/cities/bengaluru/city.yaml \
        --out public/cities/bengaluru/finance/index.html
"""
from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from pathlib import Path

from sevent4.adapters.finance_filesystem import FileFinanceFlowInputRepository, HtmlFileWriter
from sevent4.application.finance import publish_finance_flow
from sevent4.ports.finance import FinanceCity


GROUP_CLASSES = {
    "receipts": "band-receipts",
    "payments": "band-payments",
    "payment_head": "band-payment-head",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Sankey-style public-finance flow page.")
    parser.add_argument("--city", required=True, help="Path to city.yaml")
    parser.add_argument("--out", required=True, help="Output HTML path")
    parser.add_argument("--raw-dir", default=None, help="Directory of GBA budget-table XLSX files")
    args = parser.parse_args()
    build_finance_flow_from_files(args.city, args.out, args.raw_dir)
    print(f"wrote {args.out}")


def build_finance_flow_from_files(city_config: str, out: str | Path, raw_dir: str | Path | None = None) -> None:
    publish_finance_flow(
        FileFinanceFlowInputRepository(city_config, raw_dir),
        HtmlFileWriter(out),
        render_html,
    )


def render_html(
    city: FinanceCity,
    title: str,
    subtitle: str,
    links: list[dict],
    notes: list[str],
    flow_years: list[dict] | None = None,
    default_year: str | None = None,
) -> str:
    has_years = bool(flow_years)
    content = _yearly_flow_content(flow_years or [], default_year) if has_years else _single_flow_content(links, notes)
    return f"""<!doctype html>
<html lang="en">
<head>
  <script>(function(){{try{{var t=localStorage.getItem('atlas-theme');if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}}})();</script>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} - {html.escape(city.name)}</title>
  <link rel="icon" type="image/png" href="../../../assets/ixa-mark.png">
  <link rel="stylesheet" href="../../../assets/theme.css">
  <link rel="stylesheet" href="../../../assets/masthead.css">
  <style>{_css()}</style>
  <script src="../../../assets/masthead.js"></script>
  <script src="../../../assets/theme.js" defer></script>
</head>
<body>
  <header data-masthead="bar"></header>
  <main class="wrap">
    <nav class="crumb"><a href="../">&larr; Atlas</a> <span>/</span> <b>Finance</b></nav>
    <h1>{html.escape(title)}</h1>
    <p class="lede">{html.escape(subtitle)}</p>
    {content}
  </main>
  {_flow_script(flow_years or [], default_year) if has_years else ""}
</body>
</html>
"""


def _single_flow_content(links: list[dict], notes: list[str]) -> str:
    return f"""
    <div class="viz-scroll">{_sankey_svg(links)}</div>
    <section class="panel">
      <h2>Flow Table</h2>
      {_flow_table(links)}
    </section>
    <section class="panel">
      <h2>Handling Notes</h2>
      <ul class="notes">{''.join(f'<li>{html.escape(note)}</li>' for note in notes)}</ul>
    </section>
"""


def _yearly_flow_content(flow_years: list[dict], default_year: str | None) -> str:
    if not flow_years:
        return _single_flow_content([], ["No source-backed year flows parsed yet."])
    year = default_year or flow_years[-1]["year"]
    buttons = "".join(
        f'<button type="button" class="year-btn{" active" if flow["year"] == year else ""}" '
        f'data-year="{html.escape(flow["year"])}" aria-pressed="{str(flow["year"] == year).lower()}">'
        f'<span>{html.escape(flow["year"])}</span><small>{html.escape(flow.get("status", ""))}</small></button>'
        for flow in flow_years
    )
    panels = "".join(_year_panel(flow, flow["year"] == year) for flow in flow_years)
    return f"""
    <section class="flow-controls" aria-label="Budget year">
      <div class="control-label">Budget year</div>
      <div class="year-switcher">{buttons}</div>
    </section>
    <p class="status-note">Years without clean Budget Estimate flow rows are omitted rather than interpolated; partial years have fewer source-backed heads.</p>
    <div id="flow-panels">{panels}</div>
"""


def _year_panel(flow: dict, active: bool) -> str:
    notes = flow.get("notes", [])
    rows = flow.get("rows", [])
    return f"""
    <section class="year-panel{" active" if active else ""}" data-year-panel="{html.escape(flow["year"])}">
      <h2>{html.escape(flow["year"])} <span>{html.escape(flow.get("status", ""))}</span></h2>
      <div class="viz-scroll">{_sankey_svg(flow.get("links", []))}</div>
      <section class="panel">
        <h3>Flow Table</h3>
        {_flow_table(flow.get("links", []))}
      </section>
      <section class="panel">
        <h3>Source Rows</h3>
        {_source_rows_table(rows)}
      </section>
      <section class="panel">
        <h3>Handling Notes</h3>
        <ul class="notes">{''.join(f'<li>{html.escape(str(note))}</li>' for note in notes)}</ul>
      </section>
    </section>
"""


def _sankey_svg(links: list[dict]) -> str:
    if not links:
        return '<svg class="sankey" role="img" viewBox="0 0 900 180"><text x="24" y="80">No finance flows parsed yet.</text></svg>'
    width, height = 980, 560
    columns = _columns(links)
    layout = _node_layout(columns, links, height)
    bottom = max(box["y"] + box["h"] for label, box in layout.items() if label != "_scale")
    height = max(height, int(bottom + 28))
    parts = [f'<svg class="sankey" role="img" aria-label="Public finance Sankey chart" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet">']
    parts.append('<text class="caption" x="30" y="28">Corporation</text>')
    parts.append('<text class="caption" x="420" y="28">Budget view</text>')
    parts.append('<text class="caption" x="700" y="28">Largest payment heads</text>')
    source_offsets = defaultdict(float)
    target_offsets = defaultdict(float)
    for link in links:
        source = layout[link["source"]]
        target = layout[link["target"]]
        amount = max(float(link["amount_cr"]), 0.1)
        thickness = max(2.5, amount * layout["_scale"])
        sy = source["y"] + source_offsets[link["source"]] + thickness / 2
        ty = target["y"] + target_offsets[link["target"]] + thickness / 2
        source_offsets[link["source"]] += thickness
        target_offsets[link["target"]] += thickness
        band_class = GROUP_CLASSES.get(link.get("group"), "band-other")
        parts.append(_path(source["x"] + source["w"], sy, target["x"], ty, thickness, band_class))
    for label, box in layout.items():
        if label == "_scale":
            continue
        parts.append(f'<rect class="node" x="{box["x"]:.1f}" y="{box["y"]:.1f}" width="{box["w"]:.1f}" height="{box["h"]:.1f}" rx="4"/>')
        parts.append(f'<text class="node-label" x="{box["x"] + 8:.1f}" y="{box["y"] + 18:.1f}">{html.escape(_short_label(label))}</text>')
        parts.append(f'<text class="node-value" x="{box["x"] + 8:.1f}" y="{box["y"] + 34:.1f}">Rs. {_fmt(box["value"])} cr</text>')
    parts.append("</svg>")
    return "".join(parts)


def _columns(links: list[dict]) -> list[list[str]]:
    sources = {link["source"] for link in links}
    targets = {link["target"] for link in links}
    middle_set = sources & targets
    middle_set.update(label for label in ("Receipts", "Payments") if label in targets or label in sources)
    left = sorted(sources - targets - middle_set)
    middle = [label for label in ("Receipts", "Payments") if label in middle_set]
    middle.extend(sorted(middle_set - set(middle)))
    right = sorted(targets - middle_set)
    return [left, middle, right]


def _node_layout(columns: list[list[str]], links: list[dict], height: int) -> dict:
    incoming = defaultdict(float)
    outgoing = defaultdict(float)
    for link in links:
        amount = float(link["amount_cr"])
        outgoing[link["source"]] += amount
        incoming[link["target"]] += amount
    values = defaultdict(float)
    for label in set(incoming) | set(outgoing):
        values[label] = max(incoming[label], outgoing[label])
    max_column_total = max(sum(values[label] for label in column) for column in columns if column)
    scale = min(0.07, 360 / max(max_column_total, 1))
    x_positions = [34, 420, 700]
    layout: dict = {"_scale": scale}
    for col_index, column in enumerate(columns):
        y = 56
        for label in column:
            h = max(42, values[label] * scale)
            layout[label] = {"x": x_positions[col_index], "y": y, "w": 210, "h": h, "value": values[label]}
            y += h + 14
    return layout


def _path(x1: float, y1: float, x2: float, y2: float, thickness: float, band_class: str) -> str:
    mx = (x1 + x2) / 2
    return (
        f'<path d="M{x1:.1f},{y1 - thickness / 2:.1f} '
        f'C{mx:.1f},{y1 - thickness / 2:.1f} {mx:.1f},{y2 - thickness / 2:.1f} {x2:.1f},{y2 - thickness / 2:.1f} '
        f'L{x2:.1f},{y2 + thickness / 2:.1f} '
        f'C{mx:.1f},{y2 + thickness / 2:.1f} {mx:.1f},{y1 + thickness / 2:.1f} {x1:.1f},{y1 + thickness / 2:.1f} Z" '
        f'class="band {band_class}"/>'
    )


def _flow_table(links: list[dict]) -> str:
    rows = []
    for link in sorted(links, key=lambda row: (row["source"], row["target"])):
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(link['source']))}</td>"
            f"<td>{html.escape(str(link['target']))}</td>"
            f"<td class='num'>{_fmt(float(link['amount_cr']))}</td>"
            f"<td>{html.escape(str(link.get('group', '')))}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>From</th><th>To</th><th>Rs. crore</th><th>Type</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def _source_rows_table(rows: list[dict]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('section', '')))}</td>"
            f"<td>{html.escape(str(row.get('head', '')))}</td>"
            f"<td class='num'>{_fmt(float(row.get('amount_cr') or 0))}</td>"
            f"<td>{html.escape(str(row.get('source_pdf', '')))}</td>"
            f"<td>{html.escape(str(row.get('page', '')))}</td>"
            f"<td>{html.escape(str(row.get('confidence', '')))}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>Section</th><th>Head</th><th>Rs. crore</th><th>Source</th><th>Page</th><th>Confidence</th></tr></thead><tbody>" + "".join(body) + "</tbody></table>"


def _fmt(value: float) -> str:
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _short_label(value: str, limit: int = 34) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip(" (/-") + "..."


def _flow_script(flow_years: list[dict], default_year: str | None) -> str:
    payload = {"defaultYear": default_year or (flow_years[-1]["year"] if flow_years else ""), "flowYears": flow_years}
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f"""
  <script id="finance-flow-data" type="application/json">{payload_json}</script>
  <script>
  function renderFinanceFlow(year) {{
    document.body.classList.add('has-flow-js');
    document.querySelectorAll('[data-year-panel]').forEach(function(panel) {{
      panel.hidden = panel.getAttribute('data-year-panel') !== year;
      panel.classList.toggle('active', !panel.hidden);
    }});
    document.querySelectorAll('.year-btn').forEach(function(button) {{
      var active = button.getAttribute('data-year') === year;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    }});
  }}
  (function() {{
    var data = JSON.parse(document.getElementById('finance-flow-data').textContent);
    document.querySelectorAll('.year-btn').forEach(function(button) {{
      button.addEventListener('click', function() {{ renderFinanceFlow(button.getAttribute('data-year')); }});
    }});
    renderFinanceFlow(data.defaultYear);
  }})();
  </script>
"""


def _css() -> str:
    return """
*{box-sizing:border-box;margin:0}body{font:400 16px/1.6 var(--sans);background:var(--bg);color:var(--ink)}
:root{--flow-receipts:#42c8b8;--flow-payments:#ff6b73;--flow-head:#f2cf55;--flow-other:var(--mut);--flow-opacity:.58}
@media (prefers-color-scheme: light){:root:not([data-theme=dark]){--flow-receipts:#147d72;--flow-payments:#c93b44;--flow-head:#a67f0d;--flow-opacity:.5}}
:root[data-theme=light]{--flow-receipts:#147d72;--flow-payments:#c93b44;--flow-head:#a67f0d;--flow-opacity:.5}
.wrap{max-width:1080px;margin:0 auto;padding:30px 20px 78px}
.crumb{font:700 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin-bottom:20px}
.crumb a{color:var(--blue);text-decoration:none}.crumb span{margin:0 6px;color:var(--line)}
h1{font:700 32px/1.12 var(--serif);margin-bottom:8px}.lede{max-width:72ch;color:var(--mut);margin-bottom:18px}
.flow-controls{display:flex;align-items:center;gap:14px;margin:18px 0 8px}.control-label{font:700 11px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--mut)}
.year-switcher{display:flex;flex-wrap:wrap;gap:8px}.year-btn{appearance:none;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--ink);padding:7px 10px;text-align:left;cursor:pointer}
.year-btn span{display:block;font:700 12px var(--mono)}.year-btn small{display:block;margin-top:2px;font:700 9px var(--mono);text-transform:uppercase;color:var(--mut)}
.year-btn.active{border-color:var(--blue);box-shadow:inset 3px 0 0 var(--blue)}.status-note{color:var(--mut);font-size:13px;margin-bottom:12px}.has-flow-js .year-panel[hidden]{display:none}
.year-panel{margin-top:18px}.year-panel h2{font:700 22px var(--serif);margin-bottom:10px}.year-panel h2 span{font:700 10px var(--mono);text-transform:uppercase;color:var(--mut);margin-left:8px}
.viz-scroll{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:var(--r);margin:18px 0 22px}
.sankey{display:block;width:100%;min-width:760px;height:auto;background:var(--panel)}
.caption{font:700 11px var(--mono);fill:var(--mut);letter-spacing:.08em;text-transform:uppercase}.node{fill:var(--bg);stroke:var(--line)}
.band{fill-opacity:var(--flow-opacity)}.band-receipts{fill:var(--flow-receipts)}.band-payments{fill:var(--flow-payments)}.band-payment-head{fill:var(--flow-head)}.band-other{fill:var(--flow-other)}
.node-label{font:700 13px var(--sans);fill:var(--ink)}.node-value{font:600 11px var(--mono);fill:var(--mut)}
.panel{margin-top:20px}.panel h2,.panel h3{font:700 18px var(--serif);margin-bottom:8px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);font-size:13px;text-align:left}th{font:700 11px var(--mono);text-transform:uppercase;color:var(--mut)}
.num{text-align:right;font-variant-numeric:tabular-nums}.notes{color:var(--mut);padding-left:20px;max-width:82ch}
@media(max-width:680px){h1{font-size:25px}.wrap{padding:22px 14px 60px}.flow-controls{display:block}.year-switcher{margin-top:8px}th,td{font-size:12px;padding:7px 6px}}
"""


if __name__ == "__main__":
    main()
