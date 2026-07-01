from __future__ import annotations

from dataclasses import dataclass

from sevent4.ports.officials import HtmlDocumentWriter, OfficialsInputRepository, OfficialsRenderer


@dataclass(frozen=True)
class OfficialsPageBuildResult:
    html: str


def publish_officials_directory(
    repository: OfficialsInputRepository,
    writer: HtmlDocumentWriter,
    render: OfficialsRenderer,
) -> OfficialsPageBuildResult:
    inputs = repository.load()
    html = render(inputs.city, inputs.as_of, inputs.attribution, inputs.records)
    writer.write_html(html)
    return OfficialsPageBuildResult(html=html)
