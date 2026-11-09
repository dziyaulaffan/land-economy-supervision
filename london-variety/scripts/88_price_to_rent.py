"""Price-to-rent ratio by borough, 2017Q1 to the latest quarter, split by amenity within Inner and Outer London.

Price: quarterly median Category A sale price (D/S/T/F, price >= 10,000) in each of the 32 boroughs, from the
matched Land Registry sales used by 87_msoa_house_prices.py (borough from the NSPL LA code).
Rent: PIPR average monthly private rent for the borough, mean of the three months in the quarter.
Ratio = median price / (12 x average monthly rent), i.e. years of rent.
Groups: within-zone median split of 2019 amenity density (zone_amenity_group, 40_amenity_density.py).
Group lines are unweighted means of borough ratios. No quality adjustment on either side.
"""
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import CLEAN, OUT
from plot_events import event_key, mark_events, shade_provisional

ES = OUT / "event_study"
STYLE = {"Inner, high amenity": ("#2a78d6", "-"), "Inner, low amenity": ("#2a78d6", "--"),
         "Outer, high amenity": ("#eb6834", "-"), "Outer, low amenity": ("#eb6834", "--")}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def main():
    s = pd.read_parquet(sorted(CLEAN.glob("msoa_sales_*.parquet"))[-1])
    s = s[(s.ppd_category == "A") & s.property_type.isin(["D", "S", "T", "F"]) & (s.price >= 10_000)]
    a = pd.read_csv(CLEAN / "london_amenity_density_2019.csv")[["la_code", "la_name", "london_zone",
                                                                 "zone_amenity_group", "per1k_IR"]]
    s = s[s.laua.isin(a.la_code)]
    p = s.groupby(["laua", "quarter"]).price.agg(median_price="median", n_sales="size").reset_index()
    p = p.rename(columns={"laua": "la_code", "quarter": "period"})

    r = pd.read_csv(CLEAN / "rents_monthly_la.csv", parse_dates=["month"])
    r = r[r.la_code.isin(a.la_code)]
    r["period"] = r.month.dt.to_period("Q").astype(str)
    rq = r.groupby(["la_code", "period"]).agg(avg_rent=("avg_rent", "mean"), n_months=("avg_rent", "size")).reset_index()
    rq = rq[rq.n_months == 3]

    d = p.merge(rq, on=["la_code", "period"]).merge(a, on="la_code")
    d = d[d.period >= "2017Q1"]
    d["price_to_rent"] = d.median_price / (12 * d.avg_rent)
    base = d[d.period.str.startswith("2019")].groupby("la_code").price_to_rent.mean()
    d["ptr_index_2019"] = d.price_to_rent / d.la_code.map(base) * 100
    d.sort_values(["la_code", "period"]).to_csv(CLEAN / "price_to_rent_borough_quarter.csv", index=False)
    assert d.la_code.nunique() == 32
    end = d.period.max()
    print(f"{d.la_code.nunique()} boroughs, {d.period.min()}-{end}, min sales per borough-quarter {d.n_sales.min()}")

    g = d.groupby(["zone_amenity_group", "period"])[["price_to_rent", "ptr_index_2019"]].mean().reset_index()
    g.to_csv(ES / "price_to_rent_groups.csv", index=False)
    quarters = sorted(d.period.unique())
    pos = {q: i for i, q in enumerate(quarters)}
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.4))
    for ax, col, ylab in ((axes[0], "price_to_rent", "Median price / annual PIPR rent (years)"),
                          (axes[1], "ptr_index_2019", "Price-to-rent ratio, borough 2019 average = 100")):
        for grp, (c, ls) in STYLE.items():
            t = g[g.zone_amenity_group == grp]
            n = d[d.zone_amenity_group == grp].la_code.nunique()
            ax.plot(t.period.map(pos), t[col], color=c, ls=ls, lw=2, label=f"{grp} (n={n})")
        if col == "ptr_index_2019":
            ax.axhline(100, color=INK2, lw=0.8)
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.spines[["top", "right"]].set_visible(False)
        ticks = [i for i, q in enumerate(quarters) if q.endswith("Q1")]
        ax.set_xticks(ticks)
        ax.set_xticklabels([quarters[i][:4] for i in ticks])
        ax.set_ylabel(ylab)
        mark_events(ax, quarters)
        shade_provisional(ax, quarters)
        ax.legend(fontsize=7.5, frameon=False, loc="lower left")
    axes[0].set_title("Price-to-rent ratio by amenity group within zone", loc="left", fontsize=9, color=INK, pad=14)
    axes[1].set_title("Indexed to each borough's 2019 average", loc="left", fontsize=9, color=INK, pad=14)
    note = (f"Quarterly, 2017Q1-{end}. Price: borough median Category A sale price (Land Registry, D/S/T/F). Rent: "
            "PIPR average monthly rent, mean over the quarter, x 12. Groups: boroughs above and below the 2019 "
            "amenity-density median within Inner London (13) and within Outer London (19); lines are unweighted "
            "means of borough ratios. Neither side is quality-adjusted; PIPR covers all tenancies (stock) while "
            "sales are new transactions (flow). Hatched: 2026, provisional (sales registration lag). " + event_key())
    fig.text(0.01, 0.01, "\n".join(textwrap.wrap(note, 210)), fontsize=7, color=INK2, va="bottom")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(ES / "price_to_rent.png", dpi=150)
    piv = g.pivot(index="period", columns="zone_amenity_group", values="ptr_index_2019")
    print(piv.loc[["2019Q4", "2020Q4", "2021Q4", "2022Q4", "2023Q4", "2025Q4", end]].round(1).to_string())


if __name__ == "__main__":
    main()
