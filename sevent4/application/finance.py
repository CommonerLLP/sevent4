from __future__ import annotations

from dataclasses import dataclass

from sevent4.ports.finance import (
    BudgetExplorerInputRepository,
    BudgetExplorerRenderer,
    FinanceFlowInputRepository,
    FinanceFlowRenderer,
    HtmlDocumentWriter,
    MoneyFlowInputRepository,
    MoneyFlowRenderer,
)


@dataclass(frozen=True)
class FinancePageBuildResult:
    html: str


def publish_budget_explorer(
    repository: BudgetExplorerInputRepository,
    writer: HtmlDocumentWriter,
    render: BudgetExplorerRenderer,
) -> FinancePageBuildResult:
    inputs = repository.load()
    html = render(
        inputs.city,
        inputs.headline,
        inputs.civic_meta,
        inputs.civic_rows,
        getattr(inputs, "budget_stages", None),
        getattr(inputs, "deflator_series", None),
    )
    writer.write_html(html)
    return FinancePageBuildResult(html=html)


def publish_money_flow(
    repository: MoneyFlowInputRepository,
    writer: HtmlDocumentWriter,
    render: MoneyFlowRenderer,
) -> FinancePageBuildResult:
    inputs = repository.load()
    html = render(inputs.city)
    writer.write_html(html)
    return FinancePageBuildResult(html=html)


def publish_finance_flow(
    repository: FinanceFlowInputRepository,
    writer: HtmlDocumentWriter,
    render: FinanceFlowRenderer,
) -> FinancePageBuildResult:
    inputs = repository.load()
    html = render(
        inputs.city,
        inputs.title,
        inputs.subtitle,
        inputs.links,
        inputs.notes,
        getattr(inputs, "flow_years", None),
        getattr(inputs, "default_year", None),
    )
    writer.write_html(html)
    return FinancePageBuildResult(html=html)
