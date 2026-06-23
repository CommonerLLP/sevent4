#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sevent4.adapters.jurisdiction_geospatial import AhmedabadOverlapJurisdictionRepository
from sevent4.application.jurisdiction import publish_overlap_crosswalk


REPO = Path(__file__).resolve().parents[3]
DEFAULT_CITY = "ahmedabad"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build District/PC/AC/Ward many-to-many jurisdiction crosswalk.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Ahmedabad is implemented first.")
    parser.add_argument("--city-yaml", help="Path to city.yaml.")
    parser.add_argument("--out", help="Output JSON path.")
    parser.add_argument("--min-ward-pct", type=float, default=0.005, help="Minimum ward-overlap share to keep.")
    parser.add_argument("--min-area-m2", type=float, default=2500.0, help="Minimum overlap area to keep.")
    parser.add_argument(
        "--keep-parent-like-acs",
        action="store_true",
        help="Keep AC polygons that appear to contain several sibling ACs in the same PC.",
    )
    args = parser.parse_args()

    city = args.city.lower()
    if city != DEFAULT_CITY:
        sys.exit("Only the Ahmedabad overlap crosswalk recipe is implemented.")
    repository = AhmedabadOverlapJurisdictionRepository(
        REPO,
        city_yaml=args.city_yaml,
        out=args.out,
        min_ward_pct=args.min_ward_pct,
        min_area_m2=args.min_area_m2,
        drop_parent_like_acs=not args.keep_parent_like_acs,
    )
    result = publish_overlap_crosswalk(city, repository, repository)
    print(f"wrote {result.output_path}")
    print(
        "records={records} wards={wards} acs={acs} pcs={pcs} districts={districts}".format(
            records=len(result.document["records"]),
            wards=result.ward_count,
            acs=result.ac_count,
            pcs=result.pc_count,
            districts=result.district_count,
        )
    )


if __name__ == "__main__":
    main()
