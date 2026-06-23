from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sevent4.domain.pollution import PollutionBoardCapacityRecord
from sevent4.ports.evidence import PollutionBoardCapacityRepository, PublicJsonDocumentWriter

DISPLAY = {
    "ahmedabad": "Ahmedabad",
    "bengaluru": "Bengaluru",
    "chennai": "Chennai",
    "delhi": "Delhi",
    "kolkata": "Kolkata",
}
FEATURED = {"delhi", "kolkata"}


def build_pollution_board_roster(capacity_records: Sequence[PollutionBoardCapacityRecord]) -> list[dict[str, Any]]:
    boards: list[dict[str, Any]] = []
    for record in sorted(capacity_records, key=lambda item: item.city):
        row = {
            "city": record.city,
            "name": DISPLAY.get(record.city, record.city.title()),
            "board": record.board,
            "sanctioned": record.sanctioned,
            "vacant": record.vacant,
            "vacancy_pct": record.vacancy_pct,
            "year": record.year,
            "status": record.status,
            "tier": record.tier,
            "featured": record.city in FEATURED,
            **record.finance,
            "console": f"../../cities/{record.city}/index.html",
        }
        if record.capacity_claim_id:
            row["capacity_claim_id"] = record.capacity_claim_id
        if record.finance_claim_id:
            row["finance_claim_id"] = record.finance_claim_id
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
