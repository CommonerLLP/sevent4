from __future__ import annotations

from typing import Protocol


class DelhiBoundaryProvider(Protocol):
    """Downloads + normalises the Delhi boundary GeoDataFrames."""

    def acs(self):
        ...

    def pcs(self):
        ...

    def wards(self):
        ...

    def districts(self, acs):
        ...
