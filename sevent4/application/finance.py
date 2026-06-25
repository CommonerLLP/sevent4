from __future__ import annotations

from dataclasses import dataclass

from sevent4.ports.finance import (
    BudgetExplorerInputRepository,
    BudgetExplorerRenderer,
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
    html = render(inputs.city, inputs.headline, inputs.civic_meta, inputs.civic_rows)
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
