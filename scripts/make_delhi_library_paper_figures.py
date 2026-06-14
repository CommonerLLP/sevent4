#!/usr/bin/env python3
"""Figures for the Delhi Public Library paper (feat/delhi).

Built from DPL's own annual reports, so the figures are reproducible and
provenance-clean:
  - data/cities/delhi/source/libraries/dpl_annual_metrics.csv

Buildable now: the decade decline (issues + members) and the grant/spend/unspent
finance picture. The ward walk-access and transit-siting maps are NOT built yet —
they need the 112 DPL locations fully geocoded and Delhi transit (DMRC Metro, DTC/
cluster bus) layers, which are pending on this branch.

Run: .venv/bin/python3 scripts/make_delhi_library_paper_figures.py
"""
from __future__ import annotations

import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG = ROOT / "docs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

INK = "#172126"
BLUE = "#1B4E6B"
MUTED = "#66737A"
RULE = "#D6DEE2"
ALERT = "#B0412B"
GREEN = "#1f9e6b"
PAPER = "#FFFFFF"

mpl.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 10.5,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.titlecolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.linewidth": 0.8,
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
    "savefig.facecolor": PAPER,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})


def _thousands(x, _pos):
    return f"{x:,.0f}"


def _despine(ax, keep=("left", "bottom")):
    for side, spine in ax.spines.items():
        spine.set_visible(side in keep)


def _load():
    df = pd.read_csv(ROOT / "data/cities/delhi/source/libraries/dpl_annual_metrics.csv")
    return df.sort_values("year").reset_index(drop=True)


def fig_decline():
    """Hero: DPL issues (circulation) and total members, 2009-10 to 2023-24."""
    df = _load()
    yr = df["year"].tolist()
    x = range(len(yr))

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(8.4, 6.2), sharex=True, gridspec_kw={"hspace": 0.18}
    )
    covid = [i for i, y in enumerate(yr) if y in ("2020-21", "2021-22")]
    for ax in (ax1, ax2):
        ax.axvspan(min(covid) - 0.5, max(covid) + 0.5, color=RULE, alpha=0.55, zorder=0)

    iss = df["total_issues"]
    ax1.plot(x, iss, color=BLUE, lw=2.2, marker="o", ms=5, zorder=3)
    pk = iss.idxmax()
    ax1.annotate(f"peak {iss.loc[pk]:,.0f}\n({yr[pk]})",
                 xy=(pk, iss.loc[pk]), xytext=(pk + 0.3, iss.loc[pk] + 60000),
                 color=BLUE, fontsize=8.5)
    drop = (iss.iloc[-1] - iss.loc[pk]) / iss.loc[pk] * 100
    ax1.annotate(f"{iss.iloc[-1]:,.0f}\n({drop:+.0f}% vs peak)",
                 xy=(len(yr) - 1, iss.iloc[-1]), xytext=(len(yr) - 3.2, iss.iloc[-1] + 150000),
                 color=ALERT, fontsize=8.5,
                 arrowprops=dict(arrowstyle="-", color=ALERT, lw=0.8))
    ax1.set_ylabel("Annual issues (circulation)")
    ax1.yaxis.set_major_formatter(FuncFormatter(_thousands))
    ax1.set_ylim(0, 1_300_000)
    ax1.set_title("Use is collapsing: Delhi Public Library, 2009–10 to 2023–24",
                  loc="left", fontweight="bold", fontsize=12.5, pad=8)
    _despine(ax1)

    mem = df["total_members"]
    ax2.plot(x, mem, color=ALERT, lw=2.2, marker="o", ms=5, zorder=3)
    mpk = mem.idxmax()
    ax2.annotate(f"peak {mem.loc[mpk]:,.0f} ({yr[mpk]})",
                 xy=(mpk, mem.loc[mpk]), xytext=(mpk - 4.0, mem.loc[mpk] + 6000),
                 color=INK, fontsize=8.5)
    ax2.set_ylabel("Registered members")
    ax2.yaxis.set_major_formatter(FuncFormatter(_thousands))
    ax2.set_ylim(0, 210000)
    _despine(ax2)

    ax2.set_xticks(list(x))
    ax2.set_xticklabels(yr, rotation=45, ha="right", fontsize=8.5)
    fig.text(0.0, -0.02,
             "Source: Delhi Public Library annual reports (dpl.gov.in). "
             "Shaded band = 2020–22 (COVID).",
             fontsize=7.5, color=MUTED)
    fig.savefig(FIG / "figD1_dpl_decline.png")
    plt.close(fig)
    print(f"wrote figD1_dpl_decline.png (issues {iss.loc[pk]:,.0f} -> {iss.iloc[-1]:,.0f}, {drop:+.0f}%)")


def fig_finance():
    """Grant received vs spent vs unspent — DPL returns/under-spends its grant."""
    df = _load()
    f = df.dropna(subset=["grant_received_rs"]).copy()
    for c in ["grant_received_rs", "total_expenditure_rs", "closing_unspent_rs", "returned_to_ministry_rs"]:
        f[c + "_cr"] = f[c] / 1e7
    yr = f["year"].tolist()
    x = range(len(yr))
    w = 0.27

    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    ax.bar([i - w for i in x], f["grant_received_rs_cr"], width=w, color=BLUE, label="Grant received")
    ax.bar(list(x), f["total_expenditure_rs_cr"], width=w, color=MUTED, label="Total expenditure")
    ax.bar([i + w for i in x], f["closing_unspent_rs_cr"], width=w, color=ALERT, label="Closing unspent")

    for i, r in enumerate(f.itertuples()):
        ret = getattr(r, "returned_to_ministry_rs_cr")
        if ret and ret > 0.3:
            ax.annotate(f"₹{ret:.1f} cr returned\nto Ministry",
                        xy=(i, getattr(r, "closing_unspent_rs_cr")), xytext=(i, getattr(r, "closing_unspent_rs_cr") + 6),
                        ha="center", fontsize=7.5, color=ALERT)

    ax.set_ylabel("₹ crore")
    ax.set_xticks(list(x))
    ax.set_xticklabels(yr, fontsize=9)
    ax.set_title("Funded, not spent: DPL carries large unspent balances and returns grant",
                 loc="left", fontweight="bold", fontsize=11.5, pad=8)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    _despine(ax)
    fig.text(0.0, -0.04,
             "Source: Delhi Public Library annual reports (dpl.gov.in). Finance lines disclosed from 2021–22.",
             fontsize=7.5, color=MUTED)
    fig.savefig(FIG / "figD2_dpl_finance.png")
    plt.close(fig)
    print("wrote figD2_dpl_finance.png")


if __name__ == "__main__":
    fig_decline()
    fig_finance()
    print("Delhi figures written to", FIG)
