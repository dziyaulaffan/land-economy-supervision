"""Policy and reopening markers, and provisional-quarter shading, for quarterly event-study plots.

Each event is a dotted vertical line tagged with a letter at the top of the panel; event_key() returns the
matching text for the figure note.
"""
import pandas as pd

EVENTS = [
    ("A", "2020-07-04", "first reopening (4 Jul 2020)", "#1baf7a"),
    ("B", "2021-05-17", "indoor hospitality reopens (17 May 2021)", "#1baf7a"),
    ("C", "2021-07-19", "remaining restrictions end (19 Jul 2021)", "#1baf7a"),
    ("D", "2021-12-16", "first Bank Rate rise (16 Dec 2021)", "#6250d6"),
    ("E", "2022-09-23", "mini-budget (23 Sep 2022)", "#6250d6"),
]
PROVISIONAL_YEAR = "2026"


def date_x(date: str, quarters: list) -> float:
    """Position of a calendar date on an axis where quarter i is centred at x = i."""
    d = pd.Timestamp(date)
    q = pd.Period(d, "Q")
    i = quarters.index(str(q))
    frac = (d - q.start_time) / (q.end_time - q.start_time)
    return i - 0.5 + frac


def mark_events(ax, quarters: list, fontsize: float = 7.5):
    ymin, ymax = ax.get_ylim()
    for tag, date, _, col in EVENTS:
        if str(pd.Period(pd.Timestamp(date), "Q")) not in quarters:
            continue
        x = date_x(date, quarters)
        ax.axvline(x, color=col, lw=0.9, ls=":", zorder=1)
        ax.text(x, ymax, tag, fontsize=fontsize, color=col, ha="center", va="bottom", fontweight="bold")
    ax.set_ylim(ymin, ymax)


def event_key() -> str:
    return "Dotted lines: " + "; ".join(f"{t} {lab}" for t, _, lab, _ in EVENTS) + " (green: reopenings, violet: rates)."


def shade_provisional(ax, quarters: list, label: bool = True):
    prov = [i for i, q in enumerate(quarters) if q.startswith(PROVISIONAL_YEAR)]
    if not prov:
        return
    ax.axvspan(prov[0] - 0.5, prov[-1] + 0.5, facecolor="none", edgecolor="#b9b8b2", hatch="///", lw=0, zorder=0)
    if label:
        ymin, ymax = ax.get_ylim()
        ax.text(prov[0] - 0.4, ymin + 0.03 * (ymax - ymin), "provisional", fontsize=6.5, color="#52514e", va="bottom")
