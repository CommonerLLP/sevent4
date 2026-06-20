#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen


REPO = Path(__file__).resolve().parents[3]

# Ahmedabad is the first implemented representative-source adapter. Other cities
# should add their ward roster, committee, zone, and officer source documents.
DEFAULT_CITY = "ahmedabad"

CITY_REPRESENTATIVE_SOURCES = {
    "ahmedabad": [
        {
            "id": "ward_councillors_2026_27",
            "label": "Councillors 2026-27",
            "url": "https://ahmedabadcity.gov.in/ViewFile/ViewFile?TYPE=FileRepository,2638",
            "notes": "AMC ward councillor names and information.",
        },
        {
            "id": "standing_committee_english_2026_27",
            "label": "Standing Committee Member List - English",
            "url": "https://ahmedabadcity.gov.in/ViewFile/ViewFile?TYPE=FileRepository,2645",
            "notes": "AMC Standing Committee member list in English.",
        },
    ]
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch public city representative source documents.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Ahmedabad is implemented first.")
    parser.add_argument("--out-dir", help="Document output directory.")
    parser.add_argument("--manifest", help="JSON manifest output path.")
    parser.add_argument("--dry-run", action="store_true", help="List sources without downloading.")
    args = parser.parse_args()

    city = args.city.lower()
    sources = CITY_REPRESENTATIVE_SOURCES.get(city)
    if not sources:
        sys.exit(f"No representative-source adapter for city={city!r}. Add public source URLs first.")

    out_dir = Path(args.out_dir) if args.out_dir else REPO / "data" / "cities" / city / "source" / "representatives" / "docs"
    manifest = Path(args.manifest) if args.manifest else REPO / "data" / "cities" / city / "source" / "representatives" / "representative_sources.json"
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for source in sources:
        filename = f"{source['id']}.pdf"
        out_path = out_dir / filename
        row = {**source, "city": city, "path": str(out_path.relative_to(REPO))}
        if args.dry_run:
            print(f"{source['id']}\t{source['label']}\t{source['url']}")
        else:
            download(source["url"], out_path)
            print(f"wrote {out_path}")
        rows.append(row)

    if not args.dry_run:
        manifest.write_text(json.dumps({"city": city, "items": rows}, indent=2), encoding="utf-8")
        print(f"wrote {manifest}")


def download(url: str, out_path: Path) -> None:
    request = Request(url, headers={"User-Agent": "The Unelected City city-representative fetcher"})
    try:
        with urlopen(request, timeout=60) as response:
            out_path.write_bytes(response.read())
            return
    except Exception as exc:
        curl = shutil.which("curl")
        if not curl:
            raise
        result = subprocess.run(
            [curl, "-L", "--fail", "--silent", "--show-error", url],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            out_path.write_bytes(result.stdout)
            return
        raise RuntimeError(result.stderr.decode("utf-8", errors="ignore").strip() or str(exc)) from exc


if __name__ == "__main__":
    main()
