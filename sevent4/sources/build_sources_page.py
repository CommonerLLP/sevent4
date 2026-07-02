"""Build the public "Sources" page + JSON endpoint for a sourced city.

Promotes data/cities/{city}/source/public_sources.json — the evidence-linked
inventory behind a console's public claims — onto the public surface, in two
forms: a reader-facing page (public/cities/{city}/sources/index.html) and a
machine-readable endpoint (public/cities/{city}/sources/sources.json) that
sister repos can consume without re-deriving the acquisition work.

An entry whose URL was never recorded at acquisition time renders as an honest
"no public URL recorded" finding, not a guessed link. The internal `evidence`
paths are verified to exist at build time but are not published (they name
files in the gitignored data/ tree).

Usage:
    python3 -m sevent4.sources.build_sources_page \
        --city data/cities/ahmedabad/city.yaml \
        --out-dir public/cities/ahmedabad/sources
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Any

from sevent4.adapters.finance_filesystem import HtmlFileWriter
from sevent4.adapters.sources_filesystem import FileSourcesInputRepository, JsonFileWriter
from sevent4.application.sources import publish_sources_page
from sevent4.ports.sources import SourcesCity


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the public sources page + JSON.")
    parser.add_argument("--city", required=True, help="Path to city.yaml")
    parser.add_argument("--out-dir", required=True, help="Output directory for index.html + sources.json")
    args = parser.parse_args()

    build_sources_page_from_files(args.city, args.out_dir)
    print(f"wrote {args.out_dir}/index.html and {args.out_dir}/sources.json")


def build_sources_page_from_files(city_config: str, out_dir: str | Path) -> None:
    out = Path(out_dir)
    publish_sources_page(
        FileSourcesInputRepository(city_config),
        HtmlFileWriter(out / "index.html"),
        JsonFileWriter(out / "sources.json"),
        render_html,
    )


# ── page ──────────────────────────────────────────────────────────────────

def render_html(city: SourcesCity, compiled: str, entries: list[dict[str, Any]]) -> str:
    total = len(entries)
    unlinked = sum(1 for entry in entries if not entry.get("url"))
    compiled_note = f" &middot; compiled {html.escape(compiled)}" if compiled else ""
    rows = "".join(_row_html(entry) for entry in entries)
    return f"""<!doctype html>
<html lang="en">
<head>
  <script>(function(){{try{{var t=localStorage.getItem('atlas-theme');if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}}})();</script>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sources — {html.escape(city.name)}</title>
  <link rel="icon" type="image/png" href="../../../assets/ixa-mark.png">
  <link rel="stylesheet" href="../../../assets/theme.css">
  <style>{_css()}</style>
</head>
<body>
  <main class="wrap">
    <nav class="crumb"><a href="../">&larr; Atlas</a> <span>/</span> <b>Sources</b></nav>
    <h1>Where this console's data comes from</h1>
    <p class="lede">
      Every layer, number, and name on the {html.escape(city.name)} console traces
      to one of the source records below. A record without a link means the
      source's public URL was never captured at acquisition time — that gap is
      reported, not papered over with a guessed link.
    </p>
    <p class="stat">{total} source records &middot; {unlinked} with no public URL recorded{compiled_note}</p>

    <input id="osearch" class="osearch" type="search"
      placeholder="Search by source, kind, or note (e.g. &quot;budget&quot;, &quot;DataMeet&quot;, &quot;GTFS&quot;)">
    <p id="onoresults" class="onoresults" hidden>No match. Clear the search to see all sources.</p>

    <div class="rows">{rows}</div>

    <footer class="prov">
      <h3>Handling &amp; reuse</h3>
      <p>
        This inventory is compiled from the repo&#x27;s own acquisition records:
        each entry is backed by a named internal record whose existence is
        verified every time this page is built. It is also published as
        <a href="sources.json">machine-readable JSON</a>
        (schema <code>sevent4.public_sources.v1</code>) so other projects can
        reuse the sourcing without re-deriving it.
      </p>
    </footer>
  </main>
  <script>{_js()}</script>
</body>
</html>
"""


def _row_html(entry: dict[str, Any]) -> str:
    kind = str(entry.get("kind", "")).strip().replace("_", " ")
    label = str(entry.get("label", "")).strip()
    url = entry.get("url")
    notes = str(entry.get("notes", "")).strip()
    search_key = " ".join(part.lower() for part in (kind, label, notes) if part)

    if url:
        who = (
            f'<span class="rname">{html.escape(label)}</span>'
            f' <a class="rsrc" href="{html.escape(str(url), quote=True)}">source</a>'
        )
        row_class = "row"
    else:
        who = (
            f'<span class="rname">{html.escape(label)}</span>'
            f' <span class="rsrc rsrc-text">no public URL recorded</span>'
        )
        row_class = "row row-ghost"

    note_html = f'<p class="rnote">{html.escape(notes)}</p>' if notes else ""
    return f"""
      <div class="{row_class}" data-search="{html.escape(search_key, quote=True)}">
        <span class="rhead">{html.escape(kind)}</span>
        <div class="rwho">{who}</div>
        {note_html}
      </div>
"""


def _js() -> str:
    # Same live-filter idiom as the officials directory — data-search substring
    # match toggled via .is-hidden.
    return """
  document.getElementById("osearch").addEventListener("input", (event) => {
    const q = event.target.value.trim().toLowerCase();
    let anyVisible = false;
    document.querySelectorAll(".row").forEach((row) => {
      const match = !q || (row.dataset.search || "").includes(q);
      row.classList.toggle("is-hidden", !match);
      if (match) anyVisible = true;
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
.onoresults{color:var(--mut);font-size:13px;margin:18px 0}
.is-hidden{display:none}
.rows{display:flex;flex-direction:column;gap:10px;margin-top:10px}
.row{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:var(--r);padding:9px 12px}
.row-ghost{border-left-style:dashed;border-left-color:var(--mut)}
.rhead{display:block;color:var(--mut);font:700 10px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;margin-bottom:5px}
.rwho{font-size:14.5px}
.rname{color:var(--ink);font-weight:700}
.rsrc{color:var(--gold);font:700 11px var(--mono);text-decoration:none;margin-left:6px}
.rsrc-text{color:var(--mut);font-weight:400}
.rnote{color:var(--mut);font-size:12.5px;line-height:1.5;margin-top:5px;max-width:70ch}
.prov{margin-top:44px;border-top:1px solid var(--line);padding-top:20px;color:var(--mut);font-size:13px}
.prov h3{font:700 12px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--ink);margin-bottom:10px}
.prov p{max-width:74ch}.prov a{color:var(--blue)}
.prov code{font:600 12px var(--mono);color:var(--ink)}
@media(max-width:640px){h1{font-size:25px}}
"""


if __name__ == "__main__":
    main()
