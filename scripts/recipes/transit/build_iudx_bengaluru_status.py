#!/usr/bin/env python3
"""Build a local Bengaluru IUDX status packet from saved evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from sevent4.transit.iudx_access_probe import build_status_packet


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Bengaluru IUDX local status JSON.")
    parser.add_argument(
        "--request-packet",
        type=Path,
        default=Path("notes/transit/bengaluru-iudx-access-request-packet.json"),
    )
    parser.add_argument(
        "--probe",
        type=Path,
        default=Path("notes/transit/bengaluru-iudx-access-probe-2026-07-04T1723Z.json"),
    )
    parser.add_argument(
        "--transit-sources",
        type=Path,
        default=Path("data/cities/bengaluru/source/transit/multimodal_transit.sources.json"),
    )
    parser.add_argument(
        "--catalogue-detail",
        action="append",
        type=Path,
        default=[
            Path("data/cities/bengaluru/source/transit/iudx/bmtc-detail.json"),
            Path("data/cities/bengaluru/source/transit/iudx/bmrcl-network-detail.json"),
            Path("data/cities/bengaluru/source/transit/iudx/bmrcl-operations-detail.json"),
        ],
        help="Saved IUDX catalogue detail JSON to summarize for sample-file availability.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("notes/transit/bengaluru-iudx-status.json"),
    )
    parser.add_argument("--compiled-at")
    args = parser.parse_args()

    compiled_at = args.compiled_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    packet = build_status_packet(
        request_packet=_read_json(args.request_packet),
        probe_payload=_read_json(args.probe),
        transit_sources=_read_json(args.transit_sources),
        catalogue_details=[_read_json(path) for path in args.catalogue_detail],
        compiled_at=compiled_at,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(packet, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
