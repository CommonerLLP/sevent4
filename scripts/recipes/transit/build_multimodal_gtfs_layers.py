#!/usr/bin/env python3
"""Build coastal city multimodal transit layers from GTFS feeds.

Manifest shape:
{
  "feeds": [
    {
      "feed_id": "mumbai_best_bus",
      "city": "mumbai",
      "mode": "bus",
      "operator": "Brihanmumbai Electric Supply and Transport",
      "stop_layer": "bus_stops",
      "route_layer": "bus_routes",
      "path": "source/transit/gtfs/best.zip"
    }
  ]
}

Paths are resolved relative to data/cities/<city> unless absolute.
"""
from __future__ import annotations

from sevent4.transit.multimodal_layers import main


if __name__ == "__main__":
    main()
