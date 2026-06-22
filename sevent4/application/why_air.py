from __future__ import annotations

from typing import Any, Mapping

from sevent4.ports.evidence import PollutionBoardCapacityRepository, PublicJsonDocumentWriter

DISPLAY = {
    "ahmedabad": "Ahmedabad",
    "bengaluru": "Bengaluru",
    "chennai": "Chennai",
    "delhi": "Delhi",
    "kolkata": "Kolkata",
}
FEATURED = {"delhi", "kolkata"}


def build_pollution_board_roster(capacity_by_city: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    boards: list[dict[str, Any]] = []
    for city in sorted(capacity_by_city):
        data = capacity_by_city[city]
        facts = list(data.get("facts", []))
        board = str(data.get("board", ""))

        sanctioned_fact = _latest(facts, "posts_sanctioned")
        vacant_fact = _latest(facts, "posts_vacant")
        pct_fact = _latest(facts, "vacancy_pct")

        sanctioned = sanctioned_fact["value"] if sanctioned_fact else None
        vacant = vacant_fact["value"] if vacant_fact else None
        pct = None
        if pct_fact and isinstance(pct_fact["value"], int | float):
            pct = round(pct_fact["value"])
        elif isinstance(sanctioned, int | float) and isinstance(vacant, int | float) and sanctioned:
            pct = round(vacant / sanctioned * 100)

        if pct is None:
            status, tier = "pending", "pending"
        else:
            confidence = (sanctioned_fact or vacant_fact or pct_fact or {}).get("confidence", "low")
            tier = "primary" if confidence == "high" else "reported"
            status = "live"

        year_source = pct_fact or sanctioned_fact or vacant_fact or {}
        year = str(year_source.get("year", "") or "")[:4]
        finance = dict(data.get("finance") or {})

        row = {
            "city": city,
            "name": DISPLAY.get(city, city.title()),
            "board": board,
            "sanctioned": sanctioned,
            "vacant": vacant,
            "vacancy_pct": pct,
            "year": year,
            "status": status,
            "tier": tier,
            "featured": city in FEATURED,
            **finance,
            "console": f"../../cities/{city}/index.html",
        }
        if status == "live":
            row["capacity_claim_id"] = f"claim-why-air-{board.lower()}-vacancy-{year}"
        if finance and finance.get("finance_year"):
            finance_year = finance["finance_year"]
            if finance.get("surplus_cr") is not None:
                row["finance_claim_id"] = f"claim-why-air-{board.lower()}-surplus-{finance_year}"
            elif finance.get("cash_opening_balance_cr") is not None:
                row["finance_claim_id"] = f"claim-why-air-{board.lower()}-finance-{finance_year}"
        boards.append(row)

    boards.sort(key=lambda row: (row["vacancy_pct"] is None, -(row["vacancy_pct"] or 0)))
    return boards


def build_pollution_board_table(repository: PollutionBoardCapacityRepository) -> dict[str, list[dict[str, Any]]]:
    return {"boards": build_pollution_board_roster(repository.list_capacity_records())}


def publish_pollution_board_table(
    repository: PollutionBoardCapacityRepository,
    writer: PublicJsonDocumentWriter,
) -> dict[str, list[dict[str, Any]]]:
    document = build_pollution_board_table(repository)
    writer.write_json(document)
    return document


def _latest(facts: list[Mapping[str, Any]], metric: str) -> Mapping[str, Any] | None:
    rows = [fact for fact in facts if fact.get("metric") == metric and fact.get("value") is not None]
    if not rows:
        return None
    rows.sort(key=lambda fact: (fact.get("status") == "found", str(fact.get("year", ""))), reverse=True)
    return rows[0]

