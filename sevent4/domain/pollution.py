from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class PollutionBoardFact:
    metric: str
    value: Any
    year: str
    confidence: str
    status: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PollutionBoardFact":
        metric = data.get("metric")
        if not isinstance(metric, str) or not metric.strip():
            raise ValueError("pollution board fact metric is required")
        return cls(
            metric=metric,
            value=data.get("value"),
            year=str(data.get("year") or data.get("period") or ""),
            confidence=str(data.get("confidence") or "low"),
            status=str(data.get("status") or "found"),
        )


@dataclass(frozen=True)
class PollutionBoardCapacityRecord:
    city: str
    board: str
    facts: tuple[PollutionBoardFact, ...]
    finance: Mapping[str, Any]

    @classmethod
    def from_dict(cls, city: str, data: Mapping[str, Any]) -> "PollutionBoardCapacityRecord":
        board = data.get("board")
        if not isinstance(board, str) or not board.strip():
            raise ValueError(f"{city}: pollution board is required")
        finance = data.get("finance") or {}
        if not isinstance(finance, Mapping):
            raise ValueError(f"{city}: pollution board finance must be an object")
        facts = data.get("facts") or []
        if not isinstance(facts, list):
            raise ValueError(f"{city}: pollution board facts must be a list")
        return cls(
            city=city,
            board=board,
            facts=tuple(PollutionBoardFact.from_dict(fact) for fact in facts),
            finance=MappingProxyType(dict(finance)),
        )

    @property
    def sanctioned(self) -> Any:
        fact = self.latest_fact("posts_sanctioned")
        return fact.value if fact else None

    @property
    def vacant(self) -> Any:
        fact = self.latest_fact("posts_vacant")
        return fact.value if fact else None

    @property
    def vacancy_pct(self) -> int | None:
        pct_fact = self.latest_fact("vacancy_pct")
        if pct_fact and isinstance(pct_fact.value, int | float):
            return round(pct_fact.value)
        if isinstance(self.sanctioned, int | float) and isinstance(self.vacant, int | float) and self.sanctioned:
            return round(self.vacant / self.sanctioned * 100)
        return None

    @property
    def status(self) -> str:
        return "live" if self.vacancy_pct is not None else "pending"

    @property
    def tier(self) -> str:
        if self.status != "live":
            return "pending"
        confidence = (
            self.latest_fact("posts_sanctioned")
            or self.latest_fact("posts_vacant")
            or self.latest_fact("vacancy_pct")
        )
        return "primary" if confidence and confidence.confidence == "high" else "reported"

    @property
    def year(self) -> str:
        fact = self.latest_fact("vacancy_pct") or self.latest_fact("posts_sanctioned") or self.latest_fact("posts_vacant")
        return fact.year[:4] if fact else ""

    @property
    def capacity_claim_id(self) -> str | None:
        if self.status != "live":
            return None
        return f"claim-why-air-{self.board.lower()}-vacancy-{self.year}"

    @property
    def finance_claim_id(self) -> str | None:
        finance_year = self.finance.get("finance_year")
        if not finance_year:
            return None
        if self.finance.get("surplus_cr") is not None:
            return f"claim-why-air-{self.board.lower()}-surplus-{finance_year}"
        if self.finance.get("cash_opening_balance_cr") is not None:
            return f"claim-why-air-{self.board.lower()}-finance-{finance_year}"
        return None

    def latest_fact(self, metric: str) -> PollutionBoardFact | None:
        rows = [fact for fact in self.facts if fact.metric == metric and fact.value is not None]
        if not rows:
            return None
        return sorted(rows, key=lambda fact: (fact.status == "found", fact.year), reverse=True)[0]
