from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sevent4.ports.publication import (
    CityConsoleCity,
    CityConsoleInputRepository,
    CityConsoleManifest,
    CityConsolePublicSurface,
    CityConsoleRenderer,
)


@dataclass(frozen=True)
class CityConsoleBuildResult:
    html: str
    output_dir: Path


def publish_city_console(
    city: CityConsoleCity,
    manifest: CityConsoleManifest,
    surface: CityConsolePublicSurface,
    render_console: CityConsoleRenderer,
) -> CityConsoleBuildResult:
    surface.prepare()
    surface.publish_layers(city, manifest)
    html = render_console(city, manifest, surface.output_dir)
    surface.write_index(html)
    return CityConsoleBuildResult(html=html, output_dir=surface.output_dir)


def publish_city_console_from_repository(
    repository: CityConsoleInputRepository,
    surface: CityConsolePublicSurface,
    render_console: CityConsoleRenderer,
) -> CityConsoleBuildResult:
    inputs = repository.load()
    return publish_city_console(inputs.city, inputs.manifest, surface, render_console)
