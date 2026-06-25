from __future__ import annotations

from collections import Counter

from sevent4.domain.gujarat_transport import build_output, extract_rows_from_text


def extract_gujarat_transport(demand_texts) -> dict:
    """Build the deduped Gujarat city-transport scheme output from an iterable of
    (fiscal_year, source_pdf_name, pdftotext) tuples supplied by the adapter."""
    rows = []
    for fy, source_pdf, txt in demand_texts:
        rows.extend(extract_rows_from_text(txt, fy, source_pdf))
    return build_output(rows)


def summary_lines(out: dict) -> list[str]:
    lines = [f"✓ {len(out['rows'])} rows across {out['_meta']['years_found']}"]
    for entity, count in Counter(r["entity"] for r in out["rows"]).most_common():
        lines.append(f"   {entity:22} {count}")
    ebus = [r for r in out["rows"] if r["entity"] == "PM_EBUS_SEWA"]
    lines.append(f"\nPM E-bus lines captured: {len(ebus)}")
    for r in ebus[:8]:
        lines.append(
            f"   {r['fiscal_year']} ₹{r['amount_total_cr']} cr [{r.get('central_share')}] "
            f"{r['description_en'][:60]}"
        )
    return lines
