from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sevent4.ports.publication import CityConsolePublicSurface


@dataclass(frozen=True)
class CityConsoleBuildResult:
    html: str
    output_dir: Path


def publish_city_console(
    city,
    manifest,
    surface: CityConsolePublicSurface,
    render_console: Callable[[object, object, Path], str],
) -> CityConsoleBuildResult:
    surface.prepare()
    surface.publish_layers(city, manifest)
    html = render_console(city, manifest, surface.output_dir)
    surface.write_index(html)
    return CityConsoleBuildResult(html=html, output_dir=surface.output_dir)
