#!/usr/bin/env python3
"""Run a focused Delhi Public Library parliament probe through commoner-probe.

This deliberately uses commoner-probe's Sansad adapters, guarded HTTP session,
rate limiting, runlog, PDF download, and answer extraction. The only local
change is skipping MP-roster enrichment, which is not needed for an institutional
DPL profile and otherwise dominates runtime.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import shutil
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
COMMONER = ROOT.parent / "commoner-probe"


DPL_TERMS = (
    "delhi public library",
    "delhi library board",
)
DPL_CONTEXT_TERMS = (
    "dpl",
    "staff",
    "vacanc",
    "recruit",
    "post",
    "mobile",
    "branch",
    "modern",
    "digital",
    "grant",
    "ministry of culture",
    "raja rammohun",
    "rrrlf",
    "national mission on libraries",
)


def dpl_filter(title: str, query: str) -> bool:
    haystack = f"{title or ''} {query or ''}".lower()
    if any(term in haystack for term in DPL_TERMS):
        return True
    return "delhi" in haystack and any(term in haystack for term in DPL_CONTEXT_TERMS)


def load_commoner_probe() -> tuple[Any, Any, Any]:
    if str(COMMONER) not in sys.path:
        sys.path.insert(0, str(COMMONER))
    try:
        from commoner_probe.answers import extract_answers
        from commoner_probe.sansad import SansadProbe
        from commoner_probe.topics import load_topic
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "commoner-probe is required. Clone it as a sibling checkout or install "
            "commoner_probe before running this acquisition script."
        ) from exc
    return extract_answers, SansadProbe, load_topic


def focused_probe_class(sansad_probe_cls: Any) -> Any:
    class FocusedSansadProbe(sansad_probe_cls):
        def _enrich_askers(self, rec: dict) -> None:
            askers = rec.get("askers") or []
            rec["asker_details"] = [{"name": name, "party": None} for name in askers]
            rec["asker_entity_ids"] = [None for _ in askers]
            rec.setdefault("responder_entity_id", None)
            rec.setdefault("responder_role_at_event", None)

    return FocusedSansadProbe


def load_focused_topic(path: pathlib.Path, load_topic: Any) -> Any:
    topic = load_topic(path)
    return dataclasses.replace(topic, filter_fn=dpl_filter)


def summarize(out_dir: pathlib.Path) -> None:
    manifest = out_dir / "manifest.jsonl"
    answers = out_dir / "answers.jsonl"
    rows = []
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    print(f"manifest_rows={len(rows)}")
    for row in rows:
        print(
            "\t".join(
                [
                    row.get("date", ""),
                    row.get("house", ""),
                    str(row.get("qno") or row.get("qslno") or ""),
                    row.get("title", ""),
                    row.get("ministry", ""),
                    row.get("pdf_path", ""),
                ]
            )
        )
    if answers.exists():
        answer_rows = [line for line in answers.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(f"answer_rows={len(answer_rows)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default=str(ROOT / "scripts/probe_topics/delhi_public_library.json"))
    parser.add_argument("--out", default=str(ROOT / "data/tmp/commoner_probe_dpl/sansad"))
    parser.add_argument("--from-date", default="2009-01-01")
    parser.add_argument("--to-date", default="2026-06-15")
    parser.add_argument("--sessions", default="214-267")
    parser.add_argument("--max-records", type=int, default=80)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=0.15)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--no-download", action="store_true")
    args = parser.parse_args()

    extract_answers, sansad_probe_cls, load_topic = load_commoner_probe()
    FocusedSansadProbe = focused_probe_class(sansad_probe_cls)

    out_dir = pathlib.Path(args.out)
    if args.reset and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    topic = load_focused_topic(pathlib.Path(args.topic), load_topic)
    probe = FocusedSansadProbe(topic, out_dir, sleep=args.sleep, topic_path=args.topic)
    seen = probe.load_seen()
    probe.log(f"focused DPL run seen={len(seen)} download={not args.no_download}")
    added = 0
    added += probe.probe_ls(
        seen,
        from_date=args.from_date,
        to_date=args.to_date,
        qtype_filter=None,
        limit=args.limit,
        max_buckets=None,
        max_records=args.max_records,
        download=not args.no_download,
    )
    added += probe.probe_rs(
        seen,
        sessions=_parse_session_range(args.sessions),
        from_date=args.from_date,
        to_date=args.to_date,
        qtype_filter=None,
        limit=args.limit,
        max_buckets=None,
        max_records=args.max_records,
        download=not args.no_download,
    )
    probe.log(f"focused DPL run done added={added} total_seen={len(seen)}")
    extract_answers(out_dir, refresh=True, log_fn=print)
    summarize(out_dir)


def _parse_session_range(value: str) -> list[int]:
    out: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = [int(x.strip()) for x in part.split("-", 1)]
            out.extend(range(start, end + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


if __name__ == "__main__":
    main()
