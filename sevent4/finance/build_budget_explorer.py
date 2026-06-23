"""Build a municipal-finance explorer page for The Unelected City.

Reads neutral civic-finance source data (a long headline budget timeseries and a
detailed recent civic-lines series) and renders a self-contained HTML page. No
external CDN: charts are hand-built inline SVG. No private design dependency.

The accountability frame: a municipal budget is a record of what the city
government chooses to fund. The bus undertaking (AMTS) funding line is the spine
that connects this page to the transit layers on the atlas map.

Usage:
    python3 -m sevent4.finance.build_budget_explorer \
        --city data/cities/ahmedabad/city.yaml \
        --out public/cities/ahmedabad/finance/index.html
"""
from __future__ import annotations

import argparse
import html
from typing import Any

from sevent4.adapters.finance_filesystem import FileBudgetExplorerInputRepository, HtmlFileWriter
from sevent4.application.finance import publish_budget_explorer
from sevent4.city_dataset import CityDataset
from sevent4.finance.budget_data import fy_start, load_civic_lines, load_headline


# Civic lines we surface, in display order, with the colour used on the atlas
# where an equivalent map layer exists (BRTS red, transit blue, etc.).
CIVIC_LINES = [
    ("AMTS", "City bus (AMTS)", "#8f98a6"),
    ("ajl_brts", "BRTS / Janmarg", "#dc4c4c"),
    ("school_board", "School board top-up", "#1e9f8f"),
    ("vs_hospital", "V.S. Hospital grant", "#49a35f"),
    ("library_mj", "M.J. Library grant", "#e0b84d"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a municipal-finance explorer page for The Unelected City.")
    parser.add_argument("--city", required=True, help="Path to city.yaml")
    parser.add_argument("--out", required=True, help="Output HTML path")
    args = parser.parse_args()

    build_budget_explorer_from_files(args.city, args.out)
    print(f"wrote {args.out}")


# ── data loading ──────────────────────────────────────────────────────────

def build_budget_explorer_from_files(city_config: str, out: str) -> None:
    publish_budget_explorer(
        FileBudgetExplorerInputRepository(city_config),
        HtmlFileWriter(out),
        render_html,
    )


def amts_series(headline: list[dict[str, Any]], civic_rows: list[dict[str, Any]]) -> list[tuple[int, float]]:
    """Merge the long headline AMTS column with the detailed civic-lines AMTS
    rows. Both record the same 'Loan to AMTS' budget-estimate line and agree on
    overlapping years, so the union fills gaps in either source."""
    by_year: dict[int, float] = {}
    for row in headline:
        if row["amts_cr"] is not None:
            by_year[row["start"]] = row["amts_cr"]
    for row in civic_rows:
        if row.get("line") == "AMTS" and row.get("amount_cr") is not None:
            by_year.setdefault(fy_start(row["year"]), float(row["amount_cr"]))
    return sorted(by_year.items())


def civic_series(civic_rows: list[dict[str, Any]], line: str) -> list[tuple[int, float]]:
    points: dict[int, float] = {}
    for row in civic_rows:
        if row.get("line") == line and row.get("amount_cr") is not None:
            points[fy_start(row["year"])] = float(row["amount_cr"])
    return sorted(points.items())


def headline_series(headline: list[dict[str, Any]], key: str) -> list[tuple[int, float]]:
    return [(row["start"], row[key]) for row in headline if row[key] is not None]


# ── svg charting (no external dependency) ─────────────────────────────────

def line_chart(
    lines: list[dict[str, Any]],
    *,
    width: int = 720,
    height: int = 320,
    unit: str = "₹ crore",
) -> str:
    """Render a multi-line chart as inline SVG.

    Each line: {"label": str, "color": str, "points": [(x:int, y:float), ...]}.
    X is the financial-year start; gaps (missing years) break the line.
    """
    pad_l, pad_r, pad_t, pad_b = 52, 16, 18, 34
    all_x = sorted({x for line in lines for x, _ in line["points"]})
    all_y = [y for line in lines for _, y in line["points"]]
    if not all_x or not all_y:
        return "<svg></svg>"
    x_min, x_max = min(all_x), max(all_x)
    y_max = max(all_y)
    y_top = _nice_ceiling(y_max)

    def px(x: int) -> float:
        span = (x_max - x_min) or 1
        return pad_l + (x - x_min) / span * (width - pad_l - pad_r)

    def py(y: float) -> float:
        return height - pad_b - (y / y_top) * (height - pad_t - pad_b)

    parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" class="chart" role="img" '
        f'preserveAspectRatio="xMidYMid meet">'
    ]

    # y gridlines + labels
    for i in range(5):
        val = y_top * i / 4
        y = py(val)
        parts.append(f'<line class="grid" x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}"/>')
        parts.append(f'<text class="ylab" x="{pad_l - 8:.1f}" y="{y + 3:.1f}">{_fmt(val)}</text>')

    # x labels: first, last, and a few in between
    for x in _x_ticks(all_x):
        xp = px(x)
        parts.append(f'<text class="xlab" x="{xp:.1f}" y="{height - pad_b + 18:.1f}">{x}</text>')

    # lines + dots
    for line in lines:
        pts = sorted(line["points"])
        color = line["color"]
        # break the polyline across year gaps so missing years are not interpolated
        segments: list[list[tuple[int, float]]] = []
        prev: int | None = None
        for x, y in pts:
            if prev is not None and x - prev > 1:
                segments.append([])
            if not segments:
                segments.append([])
            segments[-1].append((x, y))
            prev = x
        for seg in segments:
            if len(seg) >= 2:
                d = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in seg)
                parts.append(f'<polyline class="ln" points="{d}" style="stroke:{color}"/>')
        for x, y in pts:
            parts.append(f'<circle class="dot" cx="{px(x):.1f}" cy="{py(y):.1f}" r="2.6" style="fill:{color}"/>')

    parts.append(f'<text class="unit" x="{pad_l - 8:.1f}" y="{pad_t - 4:.1f}">{html.escape(unit)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _nice_ceiling(value: float) -> float:
    if value <= 0:
        return 1.0
    import math

    magnitude = 10 ** math.floor(math.log10(value))
    for step in (1, 2, 2.5, 5, 10):
        candidate = step * magnitude
        if candidate >= value:
            return candidate
    return 10 * magnitude


def _x_ticks(years: list[int]) -> list[int]:
    if len(years) <= 6:
        return years
    first, last = years[0], years[-1]
    mids = [years[len(years) // 3], years[2 * len(years) // 3]]
    return sorted(set([first] + mids + [last]))


def _fmt(value: float) -> str:
    if value >= 1000:
        return f"{value:,.0f}"
    if value >= 100:
        return f"{value:.0f}"
    return f"{value:.0f}"


# ── page ──────────────────────────────────────────────────────────────────

def _delta(series: list[tuple[int, float]]) -> tuple[float, float, int, int]:
    first, last = series[0], series[-1]
    factor = last[1] / first[1] if first[1] else 0.0
    return first[1], last[1], first[0], last[0]


def _legend(lines: list[dict[str, Any]]) -> str:
    chips = []
    for line in lines:
        chips.append(
            f'<span class="lg"><span class="sw" style="background:{html.escape(line["color"])}"></span>'
            f'{html.escape(line["label"])}</span>'
        )
    return '<div class="legend">' + "".join(chips) + "</div>"


def render_html(
    city: CityDataset,
    headline: list[dict[str, Any]],
    civic_meta: dict[str, Any],
    civic_rows: list[dict[str, Any]],
) -> str:
    amts = amts_series(headline, civic_rows)
    total = headline_series(headline, "total_cr")
    prop = headline_series(headline, "property_tax_cr")

    amts_first, amts_last, amts_y0, amts_y1 = _delta(amts)
    total_first, total_last, total_y0, total_y1 = _delta(total)

    hero_chart = line_chart(
        [{"label": "City bus (AMTS) allocation", "color": "#5a86f5", "points": amts}],
        unit="₹ crore",
    )
    civic_lines = [
        {"label": label, "color": color, "points": civic_series(civic_rows, key) if key != "AMTS" else amts_recent(amts)}
        for key, label, color in CIVIC_LINES
    ]
    civic_lines = [line for line in civic_lines if line["points"]]
    civic_chart = line_chart(civic_lines, unit="₹ crore")
    total_chart = line_chart(
        [{"label": "Total revenue budget", "color": "#edc233", "points": total}],
        unit="₹ crore",
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <script>(function(){{try{{var t=localStorage.getItem('atlas-theme');if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}}})();</script>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Part IXA: The Municipalities - {html.escape(city.name)} city finance</title>
  <link rel="icon" type="image/png" href="../../../assets/ixa-mark.png">
  <link rel="stylesheet" href="../../../assets/theme.css">
  <link rel="stylesheet" href="../../../assets/maplibre-gl.css">
  <style>{_css()}</style>
</head>
<body>
  <main class="wrap">
    <header class="head">
      <nav class="crumb"><a href="../">&larr; Atlas</a> <span>/</span> <b>City finance</b></nav>
      <h1>What {html.escape(city.name)} city budget funds</h1>
      <p class="lede">
        A municipal budget is a record of what the city government chooses to pay
        for. These lines are read directly from {html.escape(city.name)} Municipal
        Corporation budget books. The bus undertaking line is the same money that
        runs the routes on the <a href="../">atlas map</a>.
      </p>
    </header>

    <section class="cards">
      <div class="card">
        <div class="k">City bus (AMTS) allocation</div>
        <div class="v">&#8377;{amts_first:,.0f} cr &rarr; &#8377;{amts_last:,.0f} cr</div>
        <div class="s">{amts_y0}&ndash;{str(amts_y0 + 1)[-2:]} to {amts_y1}&ndash;{str(amts_y1 + 1)[-2:]} &middot; {amts_last / amts_first:.1f}&times;</div>
      </div>
      <div class="card">
        <div class="k">Total revenue budget</div>
        <div class="v">&#8377;{total_first:,.0f} cr &rarr; &#8377;{total_last:,.0f} cr</div>
        <div class="s">{total_y0}&ndash;{str(total_y0 + 1)[-2:]} to {total_y1}&ndash;{str(total_y1 + 1)[-2:]} &middot; {total_last / total_first:.1f}&times;</div>
      </div>
      <div class="card">
        <div class="k">Bus share of budget</div>
        <div class="v">{amts_first / total_first * 100:.1f}% &rarr; {amts_last / total_last * 100:.1f}%</div>
        <div class="s">AMTS allocation as a share of the total</div>
      </div>
    </section>

    <section class="block">
      <h2>The city bus, funded over two decades</h2>
      <p class="note">
        The AMTS line is the corporation&rsquo;s capital support to the bus
        undertaking (&ldquo;Loan to AMTS&rdquo;), the legible budget anchor each
        year. The {amts_y1}&ndash;{str(amts_y1 + 1)[-2:]} book reframes this as
        &ldquo;AMTS + BRTS = 3000 EV buses (GCC model).&rdquo;
      </p>
      {hero_chart}
    </section>

    <section class="block">
      <h2>What the corporation tops up</h2>
      <p class="note">
        Recent budget books (2018&ndash;2024) make several civic lines legible:
        the bus undertaking, BRTS/Janmarg, the school board top-up over the state
        grant, the V.S. Hospital grant, and the M.J. Library grant. These are the
        choices the elected corporation controls directly.
      </p>
      {_legend(civic_lines)}
      {civic_chart}
    </section>

    <section class="block">
      <h2>Total revenue budget</h2>
      {total_chart}
    </section>

    <section class="block">
      <h2>Every figure, with its source</h2>
      <p class="note">
        Each row is read from a specific page of a specific budget book, with a
        confidence rating. Where a figure could not be cleanly isolated from the
        scanned table, it is left blank rather than guessed.
      </p>
      {_table(headline)}
    </section>

    <footer class="prov">
      <h3>Sources &amp; method</h3>
      <p>
        Figures are extracted from {html.escape(city.name)} Municipal Corporation
        budget books (English editions). Amounts are normalised to rupees crore;
        1 crore = 100 lakh. Budget books carry several columns &mdash; prior-year
        actual, current-year revised estimate, and budget-year estimate &mdash;
        and each headline figure prefers the self-labelled narrative allocation.
        Figures are human-verified from the source PDFs and carry per-row
        confidence; they are a research reading of public documents, not an
        official account. Treat low-confidence and blank cells with caution.
      </p>
      <p class="caveat">{html.escape(_first_caveat(civic_meta))}</p>
    </footer>
  </main>
</body>
</html>
"""


def amts_recent(amts: list[tuple[int, float]]) -> list[tuple[int, float]]:
    """The civic-lines comparison chart covers 2018-2024; clip AMTS to match."""
    return [(x, y) for x, y in amts if 2018 <= x <= 2024]


def _table(headline: list[dict[str, Any]]) -> str:
    head = (
        "<tr><th>Year</th><th>AMTS (bus)</th><th>M.J. Library</th>"
        "<th>Property tax</th><th>Total budget</th><th>Conf.</th><th>Pg.</th></tr>"
    )
    body = []
    for row in headline:
        def cell(value: float | None) -> str:
            return f"{value:,.2f}" if value is not None else "&mdash;"

        conf = row["confidence"]
        body.append(
            f"<tr><td>{html.escape(row['year'])}</td>"
            f"<td class='num'>{cell(row['amts_cr'])}</td>"
            f"<td class='num'>{cell(row['mj_library_cr'])}</td>"
            f"<td class='num'>{cell(row['property_tax_cr'])}</td>"
            f"<td class='num'>{cell(row['total_cr'])}</td>"
            f"<td class='conf conf-{html.escape(conf)}'>{html.escape(conf)}</td>"
            f"<td class='num'>{html.escape(row['page'])}</td></tr>"
        )
    return f'<div class="tablewrap"><table class="fin"><thead>{head}</thead><tbody>{"".join(body)}</tbody></table></div>'


def _first_caveat(civic_meta: dict[str, Any]) -> str:
    caveats = civic_meta.get("caveats", [])
    return caveats[0] if caveats else ""


def _css() -> str:
    return """
*{box-sizing:border-box;margin:0}body{font:400 16px/1.6 var(--sans);color:var(--ink);background:var(--bg)}
.wrap{max-width:860px;margin:0 auto;padding:32px 22px 80px}
.crumb{font:700 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin-bottom:20px}
.crumb a{color:var(--blue);text-decoration:none}.crumb span{margin:0 6px;color:var(--line)}
h1{font:700 30px/1.18 var(--serif);letter-spacing:-.01em;margin-bottom:12px}
.lede{color:var(--mut);font-size:16px;max-width:62ch}.lede a{color:var(--blue)}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:28px 0}
.card{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:var(--r);padding:14px 15px}
.card .k{font:700 10px/1.2 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--mut)}
.card .v{font:700 22px/1.2 var(--serif);margin:7px 0 4px}
.card .s{font:600 11px/1.3 var(--mono);color:var(--mut)}
.block{margin:40px 0;border-top:1px solid var(--hair);padding-top:26px}
h2{font:700 21px/1.25 var(--serif);margin-bottom:8px}
.note{color:var(--mut);font-size:14.5px;max-width:64ch;margin-bottom:16px}
.chart{width:100%;height:auto;display:block;background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:8px}
.chart .grid{stroke:var(--hair);stroke-width:1}
.chart .ln{fill:none;stroke-width:2.2;stroke-linejoin:round;stroke-linecap:round}
.chart .dot{stroke:var(--bg);stroke-width:.8}
.chart .ylab{fill:var(--mut);font:600 10px var(--mono);text-anchor:end}
.chart .xlab{fill:var(--mut);font:600 10px var(--mono);text-anchor:middle}
.chart .unit{fill:var(--mut);font:700 9px var(--mono);text-anchor:end;letter-spacing:.06em}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:12px}
.lg{font:600 12px var(--mono);color:var(--mut);display:flex;align-items:center;gap:6px}
.lg .sw{width:11px;height:11px;border-radius:2px;display:inline-block}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:var(--r)}
table.fin{border-collapse:collapse;width:100%;font:600 12.5px/1.3 var(--mono)}
table.fin th{background:var(--panel2);color:var(--mut);text-align:left;padding:9px 11px;font-size:10px;letter-spacing:.06em;text-transform:uppercase;border-bottom:1px solid var(--line)}
table.fin td{padding:8px 11px;border-bottom:1px solid var(--hair)}
table.fin td.num{text-align:right;font-variant-numeric:tabular-nums}
table.fin tr:last-child td{border-bottom:none}
.conf{font-size:10px;text-transform:uppercase;letter-spacing:.05em}
.conf-high{color:#49a35f}.conf-medium{color:var(--gold)}.conf-unverified,.conf-low{color:var(--red)}
.prov{margin-top:48px;border-top:1px solid var(--line);padding-top:22px;color:var(--mut);font-size:13.5px}
.prov h3{font:700 12px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--ink);margin-bottom:10px}
.prov p{max-width:70ch;margin-bottom:10px}.prov .caveat{font-style:italic;border-left:2px solid var(--gold);padding-left:10px}
@media(max-width:620px){.cards{grid-template-columns:1fr}h1{font-size:25px}}
"""


if __name__ == "__main__":
    main()
