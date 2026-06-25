#!/usr/bin/env python3
"""Devolution scorecard — TWO complementary cuts of the same service map.

1. DEVOLUTION ("who runs it"): of the resident-facing 12th-Schedule services, how many
   does the ELECTED corporation actually run vs a board/SPV/state/private firm?
   (Electricity & police excluded — never municipal functions; shown as context.)

2. DECIDED_BY ("who decided it"): of ALL the city's service arrangements (electricity and
   police INCLUDED), how many were decided/controlled by the elected city vs the state or
   the centre? This is the sharper axis — the point is not which functions are municipal,
   but whether the elected city decided the arrangement at all. A private electricity
   licensee (Torrent/Adani) is not a "devolution failure" (electricity was never the city's
   to lose) but it IS state-decided, not city-decided — so it counts here.

decided_by is derived deterministically from each service's `type`:
   corporation -> city · state_board/state_dept/spv/private -> state · railways -> centre.
(Even an in-house corporation function sits under a STATE-enacted municipal law, so "city"
here means "the elected corporation is the decision-locus", the closest thing to local control.)
"""
from __future__ import annotations
from pathlib import Path

from sevent4.adapters.filesystem import FileDevolutionScorecardRepository
from sevent4.application.public_site import format_devolution_scorecard_report, publish_devolution_scorecard_from_repository

ROOT = Path(__file__).resolve().parents[2]


def main():
    repository = FileDevolutionScorecardRepository(ROOT)
    result = publish_devolution_scorecard_from_repository(repository, repository)
    print(format_devolution_scorecard_report(result, str(repository.scorecard_path)))


if __name__ == "__main__":
    main()
