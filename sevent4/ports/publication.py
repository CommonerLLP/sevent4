from __future__ import annotations

from typing import Protocol


class PublicPageRepository(Protocol):
    def page_ids(self) -> set[str]:
        ...

    def links_for_page(self, page_id: str) -> list[str]:
        ...

