"""Exploratory charts, 2017-2023: rents, house prices, net migration, retail & recreation mobility.

Each measure is shown three ways: Inner vs Outer London (ONS statistical definition), boroughs
above vs below the London-wide median 2019 amenity density (I+R local units per 1,000 residents),
and amenity split at the median within Inner and within Outer London separately, which separates
the two dimensions. City of London is excluded (32 boroughs). Group lines are unweighted means
across boroughs of each borough's own series, so every borough counts once. No modelling.
"""
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from config import CLEAN, FIG

C1, C2 = "#2a78d6", "#eb6834"  # categorical slots 1-2 (validated reference palette)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
COVID = [("2020-03-23", "2020-06-15"), ("2020-11-05", "2020-12-02"), ("2021-01-06", "2021-04-12")]
SPLITS = {"london_zone": ("Inner London", "Outer London"), "amenity_group": ("High amenity", "Low amenity")}
SPLIT_TITLE = {"london_zone": "Inner vs Outer London", "amenity_group": "Above vs below median amenity density",
               "zone_amenity_group": "Amenity split within Inner and within Outer London"}
# group -> (colour, linestyle). Two-way splits use slots 1-2; the within-zone split keeps hue for
# zone and uses line style for amenity, so identity never rests on colour alone.
STYLE = {"Inner London": (C1, "-"), "Outer London": (C2, "-"), "High amenity": (C1, "-"),
         "Low amenity": (C2, "-"), "Inner, high amenity": (C1, "-"), "Inner, low amenity": (C1, "--"),
         "Outer, high amenity": (C2, "-"), "Outer, low amenity": (C2, "--")}
ZONE_GROUPS = ("Inner, high amenity", "Inner, low amenity", "Outer, high amenity", "Outer, low amenity")

plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "lines.linewidth": 2,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "legend.frameon": False})


def groups() -> pd.DataFrame:
    return pd.read_csv(CLEAN / "london_amenity_density_2019.csv")[
        ["la_code", "london_zone", "amenity_group", "zone_amenity_group", "per1k_IR", "pop_mid2019"]]


def shade(ax, monthly=True):
    for a, b in COVID:
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color="#d9d8d3", alpha=0.45, lw=0)


def draw(ax, df, x, y, split, ylabel, ref=None, markers=False):
    for g in SPLITS.get(split, ZONE_GROUPS):
        c, ls = STYLE[g]
        sub = df[df[split] == g]
        s = sub.groupby(x)[y].mean()
        n = sub.la_code.nunique()
        ax.plot(s.index, s.values, color=c, ls=ls, label=f"{g} (n={n})", marker="o" if markers else None,
                ms=4)
        if len(SPLITS.get(split, ZONE_GROUPS)) == 2:
            ax.annotate(g, (s.index[-1], s.values[-1]), xytext=(4, 0), textcoords="offset points",
                        color=INK2, fontsize=8, va="center")
    if ref is not None:
        ax.axhline(ref, color=INK2, lw=0.8, ls=":")
    ax.set_ylabel(ylabel)
    ax.legend(loc="best", fontsize=8)


def rents(g):
    r = pd.read_csv(CLEAN / "rents_monthly_la.csv", parse_dates=["month"])
    r = r[r.la_code.str.startswith("E09") & r.month.between("2017-01-01", "2023-12-01")]
    base = r[r.month == "2020-01-01"].set_index("la_code").avg_rent
    r["rent_idx_jan2020"] = r.avg_rent / r.la_code.map(base) * 100
    return r.merge(g, on="la_code")


def prices(g):
    p = pd.read_csv(CLEAN / "house_prices_monthly_la_type_2017_2023.csv", parse_dates=["month"])
    p = p[(p.region == "London") & (p.property_type == "All")].sort_values(["la_code", "month"])
    p["med_3m"] = p.groupby("la_code").median_price_catA.transform(lambda s: s.rolling(3, min_periods=2).mean())
    base = p[p.month.dt.year == 2019].groupby("la_code").median_price_catA.mean()
    p["price_idx_2019"] = p.med_3m / p.la_code.map(base) * 100
    nb = p[p.month.dt.year == 2019].groupby("la_code").n_catA.mean()
    p["n_3m"] = p.groupby("la_code").n_catA.transform(lambda s: s.rolling(3, min_periods=2).mean())
    p["sales_idx_2019"] = p.n_3m / p.la_code.map(nb) * 100
    return p.merge(g, on="la_code")


def migration(g):
    m = pd.read_csv(CLEAN / "migration_panel_borough_year.csv")
    m = m.merge(g[["la_code", "amenity_group", "zone_amenity_group", "pop_mid2019"]], on="la_code")
    m = m[m.year_ending_june.between(2017, 2023)]
    m["net_per1k"] = m.all_net / m.pop_mid2019 * 1000
    m["net_nonlondon_per1k"] = m.nonlondon_net / m.pop_mid2019 * 1000
    m["x"] = pd.to_datetime(m.year_ending_june.astype(str) + "-06-30")
    return m


def mobility(g):
    d = pd.read_csv(CLEAN / "mobility_daily_london.csv", parse_dates=["date"])
    d = d[d.la_code.str.startswith("E09")].sort_values(["la_code", "date"])
    for c in ["retail_recreation", "workplaces"]:
        d[c + "_7d"] = d.groupby("la_code")[c].transform(lambda s: s.rolling(7, min_periods=4).mean())
    return d.drop(columns="london_zone").merge(g, on="la_code")


def main():
    g = groups()
    data = {"rents": rents(g), "prices": prices(g), "migration": migration(g), "mobility": mobility(g)}
    rows = [
        ("rents", "month", "rent_idx_jan2020", "Avg private rent, Jan 2020 = 100", 100, "Private rents (ONS PIPR)"),
        ("prices", "month", "price_idx_2019", "Median price, 3m avg, 2019 = 100", 100,
         "House prices (Land Registry, all types, cat. A)"),
        ("migration", "x", "net_nonlondon_per1k", "Net internal migration with rest of UK\nper 1,000 (2019 pop)", 0,
         "Net migration with outside London (years ending June)"),
        ("mobility", "date", "retail_recreation_7d", "% vs Jan-Feb 2020 baseline, 7d avg", 0,
         "Retail & recreation mobility (Google)"),
    ]
    fig, axes = plt.subplots(len(rows), 2, figsize=(11, 13), sharex=False)
    for i, (k, x, y, yl, ref, title) in enumerate(rows):
        for j, split in enumerate(SPLITS):
            ax = axes[i, j]
            shade(ax)
            draw(ax, data[k], x, y, split, yl if j == 0 else "", ref, markers=(k == "migration"))
            ax.set_title(f"{title}\n{SPLIT_TITLE[split]}", fontsize=9, color=INK, loc="left")
            ax.set_xlim(pd.Timestamp("2017-01-01"), pd.Timestamp("2024-03-01"))
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.text(0.01, 0.005, "Shaded: national lockdowns (23 Mar-15 Jun 2020, 5 Nov-2 Dec 2020, 6 Jan-12 Apr 2021). "
             "Lines are unweighted means across 32 boroughs (City of London excluded). "
             "Mobility data end 15 Oct 2022.", fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0.015, 1, 1))
    fig.savefig(FIG / "exploratory_panel.png", dpi=150)

    # within-zone amenity split: four measures, 2 x 2
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, (k, x, y, yl, ref, title) in zip(axes.flat, rows):
        shade(ax)
        draw(ax, data[k], x, y, "zone_amenity_group", yl, ref, markers=(k == "migration"))
        ax.set_title(f"{title}\n{SPLIT_TITLE['zone_amenity_group']}", fontsize=9, color=INK, loc="left")
        ax.set_xlim(pd.Timestamp("2017-01-01"), pd.Timestamp("2024-03-01"))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.legend(loc="best", fontsize=7)
    fig.text(0.01, 0.005, "Amenity split at the median within each zone (Inner 13 boroughs: 6 high, 7 low; "
             "Outer 19: 9 high, 10 low). Solid = high, dashed = low amenity. City of London excluded.",
             fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(FIG / "exploratory_within_zone.png", dpi=150)

    # supporting single charts
    extra = [
        ("prices", "month", "sales_idx_2019", "Transactions, 3m avg, 2019 = 100", 100, "sales_volume",
         "Housing transactions (stamp duty holiday Jul 2020-Sep 2021)"),
        ("mobility", "date", "workplaces_7d", "% vs Jan-Feb 2020 baseline, 7d avg", 0, "workplaces_mobility",
         "Workplaces mobility (Google)"),
        ("migration", "x", "net_per1k", "Net internal migration, all moves\nper 1,000 (2019 pop)", 0,
         "net_migration_all", "Net internal migration incl. within-London moves"),
        ("rents", "month", "avg_rent", "Average monthly private rent (GBP)", None, "rent_levels",
         "Average private rent level (ONS PIPR)"),
    ]
    for k, x, y, yl, ref, fname, title in extra:
        fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
        for ax, split in zip(axes, SPLITS):
            shade(ax)
            draw(ax, data[k], x, y, split, yl, ref)
            ax.set_title(f"{title}\n{SPLIT_TITLE[split]}", fontsize=9, color=INK, loc="left")
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        fig.tight_layout()
        fig.savefig(FIG / f"{fname}.png", dpi=150)
    plt.close("all")

    # chart data for inspection
    for k, df in data.items():
        df.to_csv(CLEAN / f"chartdata_{k}.csv", index=False)
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
