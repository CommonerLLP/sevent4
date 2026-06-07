#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from sevent4.city_dataset import CityDataset
from sevent4.metrics.ward_service_access import build_metrics

# Ahmedabad is the first implemented city recipe. Other cities can use this once
# their source service layers match the SevenT4 city data contract.
DEFAULT_CITY = "ahmedabad"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ward service-access metrics for a city.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Defaults to Ahmedabad.")
    parser.add_argument("--city-yaml", help="Path to city.yaml.")
    parser.add_argument("--out", help="Output CSV path.")
    args = parser.parse_args()

    city = args.city.lower()
    city_yaml = Path(args.city_yaml) if args.city_yaml else REPO / "data" / "cities" / city / "city.yaml"
    dataset = CityDataset.from_yaml(city_yaml)
    out = Path(args.out) if args.out else dataset.outputs_dir / "ward_service_access.csv"
    build_metrics(dataset, out)


if __name__ == "__main__":
    main()
