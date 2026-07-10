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
    budget_stages: list[dict[str, Any]] | None = None
    deflator_series: dict[str, float] | None = None


@dataclass(frozen=True)
class MoneyFlowInput:
    city: FinanceCity


@dataclass(frozen=True)
class FinanceFlowInput:
    city: FinanceCity
    title: str
    subtitle: str
    links: list[dict[str, Any]]
    notes: list[str]
    flow_years: list[dict[str, Any]] | None = None
    default_year: str | None = None


class BudgetExplorerInputRepository(Protocol):
    def load(self) -> BudgetExplorerInput:
        ...


class MoneyFlowInputRepository(Protocol):
    def load(self) -> MoneyFlowInput:
        ...


class FinanceFlowInputRepository(Protocol):
    def load(self) -> FinanceFlowInput:
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
        budget_stages: list[dict[str, Any]] | None = None,
        deflator_series: dict[str, float] | None = None,
    ) -> str:
        ...


class MoneyFlowRenderer(Protocol):
    def __call__(self, city: FinanceCity) -> str:
        ...


class FinanceFlowRenderer(Protocol):
    def __call__(
        self,
        city: FinanceCity,
        title: str,
        subtitle: str,
        links: list[dict[str, Any]],
        notes: list[str],
        flow_years: list[dict[str, Any]] | None = None,
        default_year: str | None = None,
    ) -> str:
        ...
