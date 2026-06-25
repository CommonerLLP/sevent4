from __future__ import annotations

from pathlib import Path

from sevent4.city_dataset import CityDataset
from sevent4.finance.budget_data import load_civic_lines, load_headline
from sevent4.ports.finance import BudgetExplorerInput, MoneyFlowInput


class FileBudgetExplorerInputRepository:
    def __init__(self, city_config: str | Path) -> None:
        self.city_config = Path(city_config)

    def load(self) -> BudgetExplorerInput:
        city = CityDataset.from_yaml(self.city_config)
        budget_dir = city.source_dir / "budget"
        civic_meta, civic_rows = load_civic_lines(budget_dir / "amc_civic_lines.json")
        return BudgetExplorerInput(
            city=city,
            headline=load_headline(budget_dir / "amc_budget_22yr.csv"),
            civic_meta=civic_meta,
            civic_rows=civic_rows,
        )


class FileMoneyFlowInputRepository:
    def __init__(self, city_config: str | Path) -> None:
        self.city_config = Path(city_config)

    def load(self) -> MoneyFlowInput:
        return MoneyFlowInput(city=CityDataset.from_yaml(self.city_config))


class HtmlFileWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_html(self, html: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(html, encoding="utf-8")
