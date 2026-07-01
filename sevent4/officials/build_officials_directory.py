"""Build the "Who holds the seat" officials-directory page for a city.

Renders the full named-officials directory (data/cities/{city}/layers/officials.json)
grouped by department bucket — the deep reference counterpart to the console's
per-feature click-popup enrichment (which only covers AC/PC, the layers with click
geometry). An unconfirmed officeholder is rendered as a finding, not hidden as a
blank cell: the header states the completeness fact plainly, and each unresolved row
carries its own "not publicly confirmed" note rather than a bare dash.

Usage:
    python3 -m sevent4.officials.build_officials_directory \
        --city data/cities/ahmedabad/city.yaml \
        --out public/cities/ahmedabad/officials/index.html
"""
from __future__ import annotations

import argparse
import html
from typing import Any

from sevent4.adapters.finance_filesystem import HtmlFileWriter
from sevent4.adapters.officials_filesystem import FileOfficialsInputRepository
from sevent4.application.officials import publish_officials_directory
from sevent4.ports.officials import OfficialsCity

# Canonical department order — matches sevent4.officials_directory.v1's institution
# hierarchy, coarsest civic body first, election/revenue last. Any bucket not listed
# here (future schema growth) still renders, appended under "Other".
DEPARTMENT_ORDER: tuple[tuple[str, str], ...] = (
    ("municipal_corp_hq", "Municipal corporation — headquarters"),
    ("municipal_corp_zone", "Municipal corporation — zones"),
    ("development_authority", "Development authority"),
    ("utility_power", "Electricity utility"),
    ("utility_water_regional", "Regional water board"),
    ("transport_spv", "Transport SPVs"),
    ("police_commissionerate", "Police commissionerate"),
    ("admin_district", "District administration"),
    ("election_pc", "Lok Sabha (MP)"),
    ("election_ac", "Vidhan Sabha (MLA)"),
    ("revenue_sro", "Registration & stamps"),
)

CITY_OFFICIALS_CREDIT = "https://github.com/Vonter/city-officials"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the officials-directory page.")
    parser.add_argument("--city", required=True, help="Path to city.yaml")
    parser.add_argument("--out", required=True, help="Output HTML path")
    args = parser.parse_args()

    build_officials_directory_from_files(args.city, args.out)
    print(f"wrote {args.out}")


def build_officials_directory_from_files(city_config: str, out: str) -> None:
    publish_officials_directory(
        FileOfficialsInputRepository(city_config),
        HtmlFileWriter(out),
        render_html,
    )


# ── grouping ────────────────────────────────────────────────────────────────

def _grouped(records: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    by_dept: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        by_dept.setdefault(str(row.get("department", "")), []).append(row)
    known = [dept for dept, _ in DEPARTMENT_ORDER if dept in by_dept]
    other = sorted(dept for dept in by_dept if dept not in dict(DEPARTMENT_ORDER))
    labels = dict(DEPARTMENT_ORDER)
    order = [(dept, labels.get(dept, dept)) for dept in known] + [(dept, dept) for dept in other]
    return [(dept, label, by_dept[dept]) for dept, label in order]


# ── page ──────────────────────────────────────────────────────────────────

def render_html(city: OfficialsCity, as_of: str, attribution: str, records: list[dict[str, Any]]) -> str:
    total = len(records)
    unconfirmed = sum(1 for row in records if not str(row.get("name", "")).strip())
    groups = _grouped(records)
    jump = "".join(
        f'<a href="#dept-{html.escape(dept, quote=True)}">{html.escape(label)}'
        f' <span class="jcount">{len(rows)}</span></a>'
        for dept, label, rows in groups
    )
    sections = "".join(_section_html(dept, label, rows, as_of) for dept, label, rows in groups)
    return f"""<!doctype html>
<html lang="en">
<head>
  <script>(function(){{try{{var t=localStorage.getItem('atlas-theme');if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}}})();</script>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Who holds the seat — {html.escape(city.name)}</title>
  <link rel="icon" type="image/png" href="../../../assets/ixa-mark.png">
  <link rel="stylesheet" href="../../../assets/theme.css">
  <style>{_css()}</style>
</head>
<body>
  <main class="wrap">
    <nav class="crumb"><a href="../">&larr; Atlas</a> <span>/</span> <b>Who holds the seat</b></nav>
    <h1>Who holds the seat</h1>
    <p class="lede">
      Every civic institution with power over {html.escape(city.name)} — the
      municipal corporation, the development authority, the utilities, the police,
      the district administration, and the elected MP/MLA seats — and the person
      currently named to it, where that is publicly knowable.
    </p>
    <p class="stat">{total} tracked &middot; {unconfirmed} not publicly confirmed as of {html.escape(as_of)}</p>

    <input id="osearch" class="osearch" type="search"
      placeholder="Search by name, seat, or institution (e.g. &quot;MLA&quot;, &quot;Torrent&quot;, &quot;zone&quot;)">
    <nav class="ojump" aria-label="Jump to sector">{jump}</nav>
    <p id="onoresults" class="onoresults" hidden>No match. Clear the search to see the full directory.</p>

    {sections}

    <footer class="prov">
      <h3>Sources &amp; handling</h3>
      <p>
        {html.escape(attribution)} Every filled row cites its own source (linked
        above); every unconfirmed row states what was checked instead of leaving a
        blank cell. An unconfirmed officeholder is itself a finding — it means the
        seat's occupant is not currently traceable from a public source, not that no
        one holds it. See <a href="{html.escape(CITY_OFFICIALS_CREDIT)}">Vonter/city-officials</a>
        (CC-BY 4.0) for the record-shape this directory's structure is modeled on.
      </p>
    </footer>
  </main>
  <script>{_js()}</script>
</body>
</html>
"""


def _section_html(dept: str, label: str, rows: list[dict[str, Any]], as_of: str) -> str:
    body = "".join(_row_html(row, as_of) for row in rows)
    return f"""
    <section class="block" id="dept-{html.escape(dept, quote=True)}" data-dept="{html.escape(dept, quote=True)}">
      <h2>{html.escape(label)} <span class="jcount">{len(rows)}</span></h2>
      <div class="rows">{body}</div>
    </section>
"""


def _row_html(row: dict[str, Any], as_of: str) -> str:
    institution = str(row.get("institution", "")).strip()
    area = str(row.get("area", "")).strip()
    designation = str(row.get("designation", "")).strip()
    name = str(row.get("name", "")).strip()
    source = str(row.get("source", "")).strip()
    notes = str(row.get("notes", "")).strip()
    heading = " &middot; ".join(html.escape(part) for part in (area, designation) if part)
    search_key = " ".join(part.lower() for part in (institution, area, designation, name) if part)

    if name:
        # a few acquired records cite more than one URL separated by " ; " — link
        # only the first so the href stays a single, working URL
        first_source = source.split(" ; ")[0].strip()
        if first_source.startswith("http://") or first_source.startswith("https://"):
            src = f' <a class="rsrc" href="{html.escape(first_source, quote=True)}">source</a>'
        elif first_source:
            # non-URL provenance notes (e.g. "reused from this repo's own <file>")
            # are shown as plain text, never linkified — a real URL check, not a
            # link that just happens to render
            src = f' <span class="rsrc rsrc-text">{html.escape(first_source)}</span>'
        else:
            src = ""
        who = f'<span class="rname">{html.escape(name)}</span>{src}'
        row_class = "row"
    else:
        who = f'<span class="rghost">not publicly confirmed as of {html.escape(as_of)}</span>'
        row_class = "row row-ghost"

    note_html = f'<p class="rnote">{html.escape(notes)}</p>' if notes else ""
    return f"""
      <div class="{row_class}" data-search="{html.escape(search_key, quote=True)}">
        <span class="rhead">{heading}</span>
        <div class="rwho">{who}</div>
        {note_html}
      </div>
"""


def _js() -> str:
    # Same live-filter idiom as the console's own layer search (data-search
    # substring match, toggled via .is-hidden) — filters rows across every
    # sector at once without breaking the department grouping.
    return """
  document.getElementById("osearch").addEventListener("input", (event) => {
    const q = event.target.value.trim().toLowerCase();
    let anyVisible = false;
    document.querySelectorAll(".block").forEach((section) => {
      let shown = 0;
      section.querySelectorAll(".row").forEach((row) => {
        const match = !q || (row.dataset.search || "").includes(q);
        row.classList.toggle("is-hidden", !match);
        if (match) shown += 1;
      });
      section.classList.toggle("is-hidden", shown === 0);
      if (shown) anyVisible = true;
    });
    document.getElementById("onoresults").hidden = anyVisible || !q;
  });
"""


def _css() -> str:
    return """
*{box-sizing:border-box;margin:0}body{font:400 16px/1.6 var(--sans);color:var(--ink);background:var(--bg)}
.wrap{max-width:860px;margin:0 auto;padding:32px 22px 80px}
.crumb{font:700 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin-bottom:18px}
.crumb a{color:var(--blue);text-decoration:none}.crumb span{margin:0 6px;color:var(--line)}
h1{font:700 30px/1.15 var(--serif);letter-spacing:-.01em;margin-bottom:8px}
.lede{color:var(--mut);font-size:16px;max-width:70ch;margin-bottom:10px}
.stat{font:700 12px/1 var(--mono);letter-spacing:.04em;color:var(--gold);margin-bottom:18px}
.osearch{width:100%;min-height:44px;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:var(--r);padding:9px 12px;font:600 14px var(--sans);margin-bottom:12px}
.osearch::placeholder{color:var(--mut)}
.ojump{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px}
.ojump a{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);color:var(--mut);font:700 10px/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;text-decoration:none;padding:7px 10px;white-space:nowrap}
.ojump a:hover{border-color:var(--blue);color:var(--blue)}
.jcount{color:var(--mut);font:700 10px var(--mono)}
.onoresults{color:var(--mut);font-size:13px;margin:18px 0}
.is-hidden{display:none}
.block{margin:34px 0 0;border-top:1px solid var(--hair);padding-top:20px}
h2{font:700 18px/1.25 var(--serif);margin-bottom:12px}
h2 .jcount{font:700 11px var(--mono);margin-left:4px}
.rows{display:flex;flex-direction:column;gap:10px}
.row{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:var(--r);padding:9px 12px}
.row-ghost{border-left-style:dashed;border-left-color:var(--mut)}
.rhead{display:block;color:var(--mut);font:700 10px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;margin-bottom:5px}
.rwho{font-size:14.5px}
.rname{color:var(--ink);font-weight:700}
.rghost{color:var(--mut);font-style:italic}
.rsrc{color:var(--gold);font:700 11px var(--mono);text-decoration:none;margin-left:6px}
.rsrc-text{color:var(--mut);font-weight:400}
.rnote{color:var(--mut);font-size:12.5px;line-height:1.5;margin-top:5px;max-width:70ch}
.prov{margin-top:44px;border-top:1px solid var(--line);padding-top:20px;color:var(--mut);font-size:13px}
.prov h3{font:700 12px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--ink);margin-bottom:10px}
.prov p{max-width:74ch}.prov a{color:var(--blue)}
@media(max-width:640px){h1{font-size:25px}}
"""


if __name__ == "__main__":
    main()
