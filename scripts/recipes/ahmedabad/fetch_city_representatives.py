#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sevent4.adapters.representatives_filesystem import (
    JsonRepresentativeManifestWriter,
    RepresentativeDocumentDownloader,
)
from sevent4.application.representatives import CITY_REPRESENTATIVE_SOURCES, build_representative_source_manifest


REPO = Path(__file__).resolve().parents[3]
DEFAULT_CITY = "ahmedabad"


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

    out_dir = (
        Path(args.out_dir)
        if args.out_dir
        else REPO / "data" / "cities" / city / "source" / "representatives" / "docs"
    )
    manifest_path = (
        Path(args.manifest)
        if args.manifest
        else REPO / "data" / "cities" / city / "source" / "representatives" / "representative_sources.json"
    )
    document = build_representative_source_manifest(
        city,
        sources,
        lambda source: str((out_dir / f"{source['id']}.pdf").relative_to(REPO)),
    )
    if args.dry_run:
        for source in sources:
            print(f"{source['id']}\t{source['label']}\t{source['url']}")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    downloader = RepresentativeDocumentDownloader()
    for source in sources:
        out_path = out_dir / f"{source['id']}.pdf"
        downloader.download(source["url"], out_path)
        print(f"wrote {out_path}")

    JsonRepresentativeManifestWriter(manifest_path).write_manifest(document)
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()
