#!/usr/bin/env python3
"""Wire Bengaluru work-order finance layers into the city console manifest.

Thin CLI wrapper: layer shaping lives in sevent4.domain.bengaluru_finance,
dispatch in sevent4.application.bengaluru_finance, and JSON filesystem IO in
sevent4.adapters.bengaluru_finance_filesystem.
"""
from __future__ import annotations

import sevent4.adapters.bengaluru_finance_filesystem as finance_store
from sevent4.application.bengaluru_finance import wire_finance_layer
from sevent4.domain.bengaluru_finance import build_yearly_geojson  # noqa: F401


def main() -> None:
    result = wire_finance_layer(finance_store, finance_store.CITY, finance_store.LAYERS)
    print(f"joined {result['matched']}/{result['features']} ward polygons to the ledger -> ward_workorders.geojson")
    print(f"wrote ward_workorders_yearly.geojson ({result['yearly_features']} ward-year features)")
    print("patched manifest: ward_workorders + ward_workorders_yearly layers added (group 'Who pays')")


if __name__ == "__main__":
    main()
