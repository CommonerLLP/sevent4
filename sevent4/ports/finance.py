from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class FinanceCity(Protocol):
    name: str
    source_dir: Path


@dataclass(frozen=True)
class BudgetExplorerInput:
    city: FinanceCity
    headline: list[dict[str, Any]]
    civic_meta: dict[str, Any]
    civic_rows: list[dict[str, Any]]


@dataclass(frozen=True)
class MoneyFlowInput:
    city: FinanceCity


class BudgetExplorerInputRepository(Protocol):
    def load(self) -> BudgetExplorerInput:
        ...


class MoneyFlowInputRepository(Protocol):
    def load(self) -> MoneyFlowInput:
        ...


class HtmlDocumentWriter(Protocol):
    def write_html(self, html: str) -> None:
        ...


class BudgetExplorerRenderer(Protocol):
    def __call__(
        self,
        city: FinanceCity,
        headline: list[dict[str, Any]],
        civic_meta: dict[str, Any],
        civic_rows: list[dict[str, Any]],
    ) -> str:
        ...


class MoneyFlowRenderer(Protocol):
    def __call__(self, city: FinanceCity) -> str:
        ...
