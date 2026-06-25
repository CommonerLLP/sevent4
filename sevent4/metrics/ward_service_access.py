from __future__ import annotations

import argparse
from pathlib import Path

from sevent4.adapters.metrics_filesystem import (
    CsvWardServiceAccessWriter,
    FileWardServiceAccessInputRepository,
)
from sevent4.application.metrics import build_ward_service_access
from sevent4.city_dataset import CityDataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute ward-level civic service access metrics.")
    parser.add_argument("--city", required=True, help="Path to city.yaml")
    parser.add_argument("--out", help="Output CSV path; defaults to outputs_dir/ward_service_access.csv")
    args = parser.parse_args()
    city = CityDataset.from_yaml(args.city)
    out = Path(args.out) if args.out else city.outputs_dir / "ward_service_access.csv"
    build_metrics(city, out)


def build_metrics(city: str | Path | CityDataset, out: str | Path) -> None:
    result = build_ward_service_access(
        FileWardServiceAccessInputRepository(city).load(),
        CsvWardServiceAccessWriter(out),
    )
    print(f"wrote {out} ({len(result.rows)} wards)")


if __name__ == "__main__":
    main()
