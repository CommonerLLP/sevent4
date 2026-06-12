"""Build the SevenT4 "Who controls the money" flow page for a major project.

Renders a hand-built inline-SVG money-flow (Sankey-style) diagram: where the
capital comes from, through which vehicle, to whom it is paid — and, beneath it,
who repays and who bears the externalities. No external CDN.

Editorial spine: Who decided? · Who profits? · Who pays?

This first instance is the Ahmedabad Metro. Figures are public-record financing
and procurement facts; contract values that are not public are shown as an
un-sized fan and labelled as such. Individual-corruption allegations are NOT
asserted here.

Usage:
    python3 -m sevent4.finance.build_money_flow \
        --city data/cities/ahmedabad/city.yaml \
        --out public/cities/ahmedabad/money/index.html
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path

from ..city_dataset import CityDataset


# ── the data (public record) ──────────────────────────────────────────────

# Sources of Phase 1 capital (₹ crore). JICA loan is the sovereign-guaranteed
# Japanese ODA tranche; the remainder is GoI + Gujarat equity/land.
SOURCES = [
    {"label": "JICA loan (Japan)", "sub": "yen ODA · sovereign-guaranteed", "cr": 5968, "color": "#dc4c4c"},
    {"label": "GoI + Gujarat", "sub": "equity, subordinate debt, land", "cr": 4805, "color": "#5a86f5"},
]
SOURCE_TOTAL = sum(s["cr"] for s in SOURCES)

SPV = {"label": "GMRC", "sub": "Gujarat-state SPV (ex-MEGA) — the elected city controls none of it"}

# Who gets paid. Contract values are not all public, so the fan is un-sized.
RECIPIENTS = [
    {"label": "J Kumar Infraprojects", "owner": "Gupta family", "role": "viaducts", "flag": "IN"},
    {"label": "Afcons", "owner": "Shapoorji Pallonji", "role": "tunnels", "flag": "IN"},
    {"label": "L&T", "owner": "widely held (LIC + instns)", "role": "tunnels", "flag": "IN"},
    {"label": "Tata Projects", "owner": "Tata Sons", "role": "viaduct + stations", "flag": "IN"},
    {"label": "Simplex Infra.", "owner": "Mundhra family", "role": "viaduct", "flag": "IN"},
    {"label": "Hyundai Rotem", "owner": "Hyundai Motor Group", "role": "96 coaches", "flag": "KOR"},
    {"label": "Nippon Signal", "owner": "listed, Japan", "role": "signalling", "flag": "JPN"},
    {"label": "SYSTRA + RITES + AECOM", "owner": "FR / IN-PSU / US", "role": "general consultant", "flag": "FR"},
]

FOREIGN = {"KOR", "JPN", "FR", "US"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the SevenT4 money-flow page.")
    parser.add_argument("--city", required=True, help="Path to city.yaml")
    parser.add_argument("--out", required=True, help="Output HTML path")
    args = parser.parse_args()

    city = CityDataset.from_yaml(args.city)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(city), encoding="utf-8")
    print(f"wrote {out}")


# ── svg flow diagram ──────────────────────────────────────────────────────

def _band(x1: float, yt1: float, yb1: float, x2: float, yt2: float, yb2: float, color: str, op: float) -> str:
    mx = (x1 + x2) / 2
    d = (
        f"M{x1:.1f},{yt1:.1f} C{mx:.1f},{yt1:.1f} {mx:.1f},{yt2:.1f} {x2:.1f},{yt2:.1f} "
        f"L{x2:.1f},{yb2:.1f} C{mx:.1f},{yb2:.1f} {mx:.1f},{yb1:.1f} {x1:.1f},{yb1:.1f} Z"
    )
    return f'<path d="{d}" fill="{color}" fill-opacity="{op}"/>'


def _flow_svg() -> str:
    W, H = 880, 640
    top = 96
    col_h = 300  # SPV stack height
    src_x0, src_x1 = 40, 188
    spv_x0, spv_x1 = 372, 520
    rcp_x0, rcp_x1 = 700, 868

    parts = [f'<svg viewBox="0 0 {W} {H}" class="flow" role="img" preserveAspectRatio="xMidYMid meet">']

    # column captions
    parts.append(f'<text class="cap" x="{src_x0}" y="{top - 18}">Who puts money in</text>')
    parts.append(f'<text class="cap" x="{spv_x0}" y="{top - 18}">Through</text>')
    parts.append(f'<text class="cap" x="{rcp_x0}" y="{top - 18}">Who gets paid</text>')

    # source nodes + bands into SPV (proportional)
    y = top
    spv_y = top
    for s in SOURCES:
        h = col_h * s["cr"] / SOURCE_TOTAL
        # source box
        parts.append(f'<rect class="node" x="{src_x0}" y="{y:.1f}" width="{src_x1 - src_x0}" height="{h:.1f}" rx="3"/>')
        parts.append(f'<text class="nlab" x="{src_x0 + 8}" y="{y + 18:.1f}">{html.escape(s["label"])}</text>')
        parts.append(f'<text class="nsub" x="{src_x0 + 8}" y="{y + 34:.1f}">{html.escape(s["sub"])}</text>')
        parts.append(f'<text class="ncr" x="{src_x1 - 8}" y="{y + 18:.1f}">₹{s["cr"]:,} cr</text>')
        # band into SPV
        parts.append(_band(src_x1, y, y + h, spv_x0, spv_y, spv_y + h, s["color"], 0.42))
        y += h
        spv_y += h

    # SPV node
    parts.append(f'<rect class="spv" x="{spv_x0}" y="{top}" width="{spv_x1 - spv_x0}" height="{col_h}" rx="4"/>')
    parts.append(f'<text class="spvlab" x="{(spv_x0 + spv_x1) / 2:.1f}" y="{top + col_h / 2 - 6:.1f}">{html.escape(SPV["label"])}</text>')
    parts.append(f'<text class="spvsub" x="{(spv_x0 + spv_x1) / 2:.1f}" y="{top + col_h / 2 + 14:.1f}">state SPV</text>')

    # recipient fan (un-sized: equal slices)
    n = len(RECIPIENTS)
    slice_h = col_h / n
    rcp_top, rcp_gap, rcp_box = top - 6, 8, 34
    for i, r in enumerate(RECIPIENTS):
        yt = rcp_top + i * (rcp_box + rcp_gap)
        yb = yt + rcp_box
        foreign = r["flag"] in FOREIGN
        color = "#edc233" if foreign else "#8f98a6"
        parts.append(_band(spv_x1, top + i * slice_h, top + (i + 1) * slice_h, rcp_x0, yt, yb, color, 0.34))
        parts.append(f'<rect class="rnode{" foreign" if foreign else ""}" x="{rcp_x0}" y="{yt:.1f}" width="{rcp_x1 - rcp_x0}" height="{rcp_box}" rx="3"/>')
        tag = f' <tspan class="flag">▸{html.escape(r["flag"])}</tspan>' if foreign else ""
        parts.append(f'<text class="rlab" x="{rcp_x0 + 8}" y="{yt + 14:.1f}">{html.escape(r["label"])}{tag}</text>')
        parts.append(f'<text class="rsub" x="{rcp_x0 + 8}" y="{yt + 27:.1f}">{html.escape(r["owner"])} · {html.escape(r["role"])}</text>')

    # repayment arrow: from SPV bottom down to the public bar
    bar_y = top + col_h + 78
    ax = spv_x0 + 30
    parts.append(
        f'<path class="repay" d="M{ax},{top + col_h} C{ax},{top + col_h + 40} {src_x0 + 60},{bar_y - 30} {src_x0 + 70},{bar_y}" '
        f'marker-end="url(#arw)"/>'
    )
    parts.append(f'<text class="repaylab" x="{ax + 12}" y="{top + col_h + 42}">repaid ~30–40 yrs · + FX risk</text>')

    # the public bar
    parts.append(f'<rect class="public" x="{src_x0}" y="{bar_y}" width="{rcp_x1 - src_x0}" height="46" rx="4"/>')
    parts.append(f'<text class="publab" x="{src_x0 + 16}" y="{bar_y + 20}">THE PUBLIC</text>')
    parts.append(f'<text class="pubsub" x="{src_x0 + 16}" y="{bar_y + 37}">repays the loan for a generation · carries the FX risk · breathes the construction dust · had no vote in any of it</text>')

    # arrowhead marker
    parts.append('<defs><marker id="arw" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#edc233"/></marker></defs>')

    parts.append("</svg>")
    return "".join(parts)


# ── page ──────────────────────────────────────────────────────────────────

def render_html(city: CityDataset) -> str:
    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Who controls the money — {html.escape(city.name)} Metro</title>
  <link rel="icon" type="image/png" href="../../../assets/ixa-mark.png">
  <link rel="stylesheet" href="../../../assets/maplibre-gl.css">
  <style>{_css()}</style>
</head>
<body>
  <main class="wrap">
    <nav class="crumb"><a href="../">&larr; Atlas</a> <span>/</span> <a href="../finance/">City finance</a> <span>/</span> <b>Who controls the money</b></nav>
    <h1>Who controls the money</h1>
    <p class="spine"><b>Who decided?</b> &middot; <b>Who profits?</b> &middot; <b>Who pays?</b></p>
    <p class="lede">
      The {html.escape(city.name)} Metro is ~₹16,000 crore of capital — the city's
      single biggest mobility decision. Almost none of it is on the elected
      municipal corporation's books. Follow Phase 1's ₹10,773 crore: where it came
      from, through which vehicle, and to whom it was paid.
    </p>

    {_flow_svg()}

    <p class="figmnote">
      Source amounts are proportional. The recipient fan is <b>un-sized</b>:
      individual contract values are not all public. Gold = value paid to a
      foreign supplier (the Japanese loan partly returns to Japan via Nippon
      Signal — the tied-aid loop).
    </p>

    <section class="block">
      <h2>The asymmetry</h2>
      <p class="note">
        Every party on the right is paid in full <b>whether or not the trains run,
        and whether the project is on time or five years late.</b> The risks — cost
        overrun, delay, low ridership, foreign-exchange movement, and the years of
        dust and congestion along the corridor — sit entirely with the public and
        the people who live beside the line. A delay is not a shared misfortune; it
        is a one-sided transfer.
      </p>
      {_risk_grid()}
    </section>

    <section class="block">
      <h2>Why this is the point, not a footnote</h2>
      <p class="note">
        The bus the city <i>does</i> control — AMTS — gets about ₹525 crore a year,
        and Janmarg/BRTS about ₹143 crore. The Phase 1 delay alone cost an estimated
        ₹5,000–8,000 crore in overrun and forgone returns — <b>a decade or more of
        the entire city bus programme</b>. The most expensive mobility decision in
        the city is the one least accountable to the city's voters. That is the
        74th-Amendment devolution gap, made into a money trail. See the
        <a href="../finance/">22-year city budget</a> for the bus-funding line.
      </p>
    </section>

    <footer class="prov">
      <h3>Sources &amp; handling</h3>
      <p>
        Financing and procurement facts are public record (GMRC; JICA; press
        reporting on contract awards). Contract-value splits that are not public
        are not invented. The "Gupta family" shown as J Kumar Infraprojects'
        promoter is a matter of company record and is <b>unrelated</b> to any
        individual named in delay or scam reporting; no individual-corruption claim
        is made or implied here.
      </p>
    </footer>
  </main>
</body>
</html>
"""


def _risk_grid() -> str:
    rows = [
        ("Capex ₹10,773 cr", "state SPV", "contractors", "the public"),
        ("Overrun ~₹2,000 cr", "—", "contractors", "the public"),
        ("5-year delay", "—", "lender (paid)", "the public"),
        ("FX (yen loan)", "—", "—", "the public"),
        ("Empty trains", "—", "paid anyway", "the public"),
        ("Dust &amp; snarls", "—", "—", "corridor residents"),
    ]
    body = []
    for what, decides, profits, bears in rows:
        body.append(
            f"<tr><td>{what}</td><td>{decides}</td><td>{profits}</td>"
            f"<td class='bears'>{bears}</td></tr>"
        )
    return (
        '<div class="tablewrap"><table class="risk"><thead>'
        "<tr><th>The risk on…</th><th>Who decides</th><th>Who profits</th><th>Who bears it</th></tr>"
        f"</thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def _css() -> str:
    return """
:root{color-scheme:dark;--bg:#0a0c10;--panel:#13161d;--panel2:#171b23;--ink:#ece9e2;--mut:#8b929f;--line:#262c38;--hair:#1b1f28;--blue:#5a86f5;--red:#f0303d;--gold:#edc233;--r:6px;--serif:Georgia,"Iowan Old Style","Times New Roman",serif;--mono:ui-monospace,Menlo,"SF Mono",Consolas,monospace;--sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
[data-theme=light]{color-scheme:light;--bg:#f3f1ea;--panel:#fff;--panel2:#f6f3ea;--ink:#16181d;--mut:#586071;--line:#d7d1c2;--hair:#e7e2d6;--blue:#22409A;--red:#c8102e;--gold:#9a7b14}
*{box-sizing:border-box;margin:0}body{font:400 16px/1.6 var(--sans);color:var(--ink);background:var(--bg)}
.wrap{max-width:940px;margin:0 auto;padding:32px 22px 80px}
.crumb{font:700 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin-bottom:18px}
.crumb a{color:var(--blue);text-decoration:none}.crumb span{margin:0 6px;color:var(--line)}
h1{font:700 30px/1.15 var(--serif);letter-spacing:-.01em;margin-bottom:8px}
.spine{font:700 13px/1 var(--mono);letter-spacing:.04em;color:var(--gold);margin-bottom:14px}
.lede{color:var(--mut);font-size:16px;max-width:70ch;margin-bottom:26px}
.flow{width:100%;height:auto;display:block;background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:10px}
.flow .cap{fill:var(--mut);font:700 10px var(--mono);letter-spacing:.1em;text-transform:uppercase}
.flow .node{fill:var(--panel2);stroke:var(--line)}
.flow .nlab{fill:var(--ink);font:700 12px var(--sans)}
.flow .nsub{fill:var(--mut);font:600 9.5px var(--mono)}
.flow .ncr{fill:var(--ink);font:700 11px var(--mono);text-anchor:end}
.flow .spv{fill:#2a2030;stroke:var(--gold);stroke-width:1.4}
.flow .spvlab{fill:var(--ink);font:800 18px var(--serif);text-anchor:middle}
.flow .spvsub{fill:var(--gold);font:700 9px var(--mono);letter-spacing:.12em;text-transform:uppercase;text-anchor:middle}
.flow .rnode{fill:var(--panel2);stroke:var(--line)}
.flow .rnode.foreign{stroke:var(--gold)}
.flow .rlab{fill:var(--ink);font:700 11px var(--sans)}
.flow .rlab .flag{fill:var(--gold);font:800 9px var(--mono)}
.flow .rsub{fill:var(--mut);font:600 9px var(--mono)}
.flow .repay{fill:none;stroke:var(--gold);stroke-width:2;stroke-dasharray:4 3}
.flow .repaylab{fill:var(--gold);font:700 10px var(--mono)}
.flow .public{fill:#241015;stroke:var(--red);stroke-width:1.4}
.flow .publab{fill:var(--ink);font:800 15px var(--serif)}
.flow .pubsub{fill:var(--mut);font:600 10.5px var(--mono)}
.figmnote{color:var(--mut);font-size:12.5px;max-width:74ch;margin:12px 0 0}
.block{margin:38px 0 0;border-top:1px solid var(--hair);padding-top:24px}
h2{font:700 21px/1.25 var(--serif);margin-bottom:8px}
.note{color:var(--mut);font-size:15px;max-width:70ch;margin-bottom:16px}.note a{color:var(--blue)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:var(--r)}
table.risk{border-collapse:collapse;width:100%;font:600 13px/1.3 var(--mono)}
table.risk th{background:var(--panel2);color:var(--mut);text-align:left;padding:9px 12px;font-size:10px;letter-spacing:.06em;text-transform:uppercase;border-bottom:1px solid var(--line)}
table.risk td{padding:9px 12px;border-bottom:1px solid var(--hair)}
table.risk td.bears{color:var(--red);font-weight:700}
table.risk tr:last-child td{border-bottom:none}
.prov{margin-top:44px;border-top:1px solid var(--line);padding-top:20px;color:var(--mut);font-size:13px}
.prov h3{font:700 12px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--ink);margin-bottom:10px}
.prov p{max-width:74ch}.prov b{color:var(--ink)}
@media(max-width:640px){h1{font-size:25px}}
"""


if __name__ == "__main__":
    main()
