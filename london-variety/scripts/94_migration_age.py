"""Net migration with the rest of the UK by age group, and borough event studies for each group.

Moves: the London rows of the ONS detailed origin-destination estimates cached by 10_migration.py
(raw/ons_internal_migration/detailedestimatesYYYY.london.parquet), years ending June 2015-2025. Age is age at
30 June of the year ending (ONS definition), so it can be one year older than at the move.
Net moves with the rest of the UK = moves into the borough from outside Greater London (33 authorities,
incl. the City) minus moves out to outside Greater London, Scotland and Northern Ireland included,
matching nonlondon_net in migration_panel_borough_year.csv.

Groups: 20-29; 30-39; family proxy = ages 0-15 and 30-49 together; 50+.
The family proxy overlaps the 30-39 group. Rates: net moves per 1,000 mid-2019 residents of the same group
(ONS mid-2019 estimates rebased to Census 2021, Nomis NM_2002_1, single year of age).
Event study: baseline continuous specification of 80_event_study.py (borough and year FE, standardised log
amenity density x year, 2019 omitted), CR1 by borough and WCR bootstrap (B = 9,999).
"""
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import CLEAN, LONDON, OUT, RAW, download, london_frame
from es_core import fit_cluster, rademacher

ES = OUT / "event_study"
NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
GROUPS = {"age20_29": [range(20, 30)], "age30_39": [range(30, 40)],
          "family_0_15_30_49": [range(0, 16), range(30, 50)], "age50plus": [range(50, 200)]}
LABELS = {"age20_29": "Ages 20-29", "age30_39": "Ages 30-39", "family_0_15_30_49": "Family proxy: 0-15 and 30-49",
          "age50plus": "Ages 50+", "all": "All ages"}
COLORS = {"age20_29": "#2a78d6", "age30_39": "#eb6834", "family_0_15_30_49": "#1baf7a", "age50plus": "#eda100"}
BASE = "2019"
B, SEED = 9999, 20261028


def in_group(age: pd.Series, g: str) -> pd.Series:
    return np.logical_or.reduce([age.isin(list(r)) for r in GROUPS[g]])


def population_by_group() -> pd.DataFrame:
    """Mid-2019 population by single year of age (codes 101-191 = ages 0..89 and 90+)."""
    lon = london_frame()
    url = (f"{NOMIS}/NM_2002_1.data.csv?geography={','.join(lon.la_code)}&date=2019&gender=0"
           f"&c_age={','.join(str(c) for c in range(101, 192))}&measures=20100"
           "&select=geography_code,c_age,obs_value")
    p = pd.read_csv(download(url, RAW / "nomis" / "mye_population_mid2019_single_age_london.csv"))
    p["age"] = p.C_AGE - 101  # 90 means 90+
    out = {}
    for g in GROUPS:
        out[g] = p[in_group(p.age, g)].groupby("GEOGRAPHY_CODE").OBS_VALUE.sum()
    out["all"] = p.groupby("GEOGRAPHY_CODE").OBS_VALUE.sum()
    return pd.DataFrame(out).rename_axis("la_code").reset_index()


def net_by_group() -> pd.DataFrame:
    frames = [pd.read_parquet(f) for f in sorted((RAW / "ons_internal_migration").glob("detailedestimates*.london.parquet"))]
    m = pd.concat(frames, ignore_index=True)
    gla = set(LONDON)
    inn = m[m.inla.isin(gla) & ~m.outla.isin(gla)].rename(columns={"inla": "la_code"}).assign(sign=1.0)
    out = m[m.outla.isin(gla) & ~m.inla.isin(gla)].rename(columns={"outla": "la_code"}).assign(sign=-1.0)
    x = pd.concat([inn[["la_code", "year_ending_june", "age", "moves", "sign"]],
                   out[["la_code", "year_ending_june", "age", "moves", "sign"]]])
    x["net"] = x.moves * x.sign
    res = {}
    for g in GROUPS:
        res[g] = x[in_group(x.age, g)].groupby(["la_code", "year_ending_june"]).net.sum()
    res["all"] = x.groupby(["la_code", "year_ending_june"]).net.sum()
    return pd.DataFrame(res).fillna(0).reset_index()


def main():
    pop = population_by_group()
    net = net_by_group()
    lon = london_frame()
    net = net[net.la_code.isin(lon.la_code)]
    # check: all-ages net equals nonlondon_net in the existing panel
    panel = pd.read_csv(CLEAN / "migration_panel_borough_year.csv")[["la_code", "year_ending_june", "nonlondon_net"]]
    chk = net.merge(panel, on=["la_code", "year_ending_june"])
    assert len(chk) == 352 and np.allclose(chk["all"], chk.nonlondon_net, atol=1e-6), "all-ages net does not match panel"
    long = net.melt(id_vars=["la_code", "year_ending_june"], var_name="group", value_name="net_moves")
    long = long.merge(pop.melt(id_vars="la_code", var_name="group", value_name="pop_mid2019"), on=["la_code", "group"])
    long["net_per1k_group"] = long.net_moves / long.pop_mid2019 * 1000
    long.to_csv(CLEAN / "migration_net_by_age_group.csv", index=False)

    bv = pd.read_csv(CLEAN / "event_study_borough_vars.csv")[["la_code", "D_cont"]]
    w = rademacher(B, 32, SEED)
    rows = []
    for g in ["all", *GROUPS]:
        df = long[long.group == g].merge(bv, on="la_code").sort_values(["la_code", "year_ending_june"])
        df["period"] = df.year_ending_june.astype(str)
        ev = [p for p in sorted(df.period.unique()) if p != BASE]
        unit = pd.get_dummies(df.la_code, dtype=float)
        per = pd.get_dummies(df.period, dtype=float)[ev]
        X = np.hstack([unit.values, per.values, per.values * df.D_cont.values[:, None]])
        names = [f"fe_{c}" for c in unit.columns] + [f"t_{p}" for p in ev] + [f"D:{p}" for p in ev]
        tab, _ = fit_cluster(X, df.net_per1k_group.values, names, [f"D:{p}" for p in ev], cl_se=df.la_code.values,
                             w=w, k_nested=unit.shape[1])
        tab["period"] = tab.name.str.split(":").str[1]
        tab.insert(0, "group", g)
        tab["n_obs"], tab["k"] = tab.attrs["n_obs"], tab.attrs["k"]
        tab["mean_outcome_2015_2019"] = df[df.year_ending_june <= 2019].net_per1k_group.mean()
        rows.append(tab.drop(columns=["t_bootcluster"]))
    res = pd.concat(rows, ignore_index=True)
    res.to_csv(ES / "migration_age_event_study.csv", index=False)
    piv = res.pivot_table(index="period", columns="group", values=["coef", "p_wcb"])
    lines = ["| Year to June | " + " | ".join(LABELS[g] for g in ["all", *GROUPS]) + " |", "|---|" + "---|" * 5]
    for p_ in piv.index:
        lines.append(f"| {p_} | " + " | ".join(f"{piv.loc[p_, ('coef', g)]:.2f} ({piv.loc[p_, ('p_wcb', g)]:.3f})"
                                              for g in ["all", *GROUPS]) + " |")
    means = res.groupby("group").mean_outcome_2015_2019.first()
    lines.append("| Mean outcome, 2015-2019 | " + " | ".join(f"{means[g]:.2f}" for g in ["all", *GROUPS]) + " |")
    (ES / "migration_age_event_study.md").write_text(
        "Net migration with the rest of the UK per 1,000 mid-2019 residents of the group; coefficient per SD of "
        "standardised log borough amenity density; borough WCB p in brackets; 2019 omitted.\n\n"
        + "\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    plot(res)


def plot(res):
    INK, INK2, GRID, PRE = "#0b0b0b", "#52514e", "#e4e3df", "#efeeea"
    years = sorted(set(res.period) | {BASE})
    pos = {y: i for i, y in enumerate(years)}
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axvspan(-0.5, pos["2020"] - 0.5, color=PRE, lw=0, zorder=0)
    ax.axhline(0, color=INK2, lw=0.8)
    offs = dict(zip(GROUPS, [-0.24, -0.08, 0.08, 0.24]))
    for g in GROUPS:
        t = res[res.group == g]
        t = pd.concat([t, pd.DataFrame([{"period": BASE, "coef": 0.0, "ci_low": 0.0, "ci_high": 0.0, "p_wcb": 1.0}])])
        x = t.period.map(pos) + offs[g]
        sig = t.p_wcb < 0.05
        ax.vlines(x, t.ci_low, t.ci_high, color=COLORS[g], lw=1.4, zorder=2)
        ax.plot(x.sort_values(), t.set_index(x).coef.sort_index(), color=COLORS[g], lw=0.8, alpha=0.6, zorder=2)
        ax.scatter(x[sig], t.coef[sig], s=30, color=COLORS[g], zorder=3, label=f"{LABELS[g]} (WCB p<0.05)")
        ax.scatter(x[~sig], t.coef[~sig], s=30, facecolor="#fcfcfb", edgecolor=COLORS[g], zorder=3,
                   label=f"{LABELS[g]} (WCB p>=0.05)")
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years)
    ax.set_xlabel("Year ending June")
    ax.set_ylabel("Net moves with rest of UK per 1,000 group residents,\nper SD of log borough amenity density")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=7.5, frameon=False, ncol=2, loc="lower left")
    ax.set_title("Borough event study of net migration by age group", loc="left", fontsize=10, color=INK)
    note = ("32 boroughs, years ending June 2015-2025, 2019 omitted (each group plotted at 0). Borough and year FE. "
            "Bars: 95% CI, CR1 clustered by borough, t(31). Filled: WCR bootstrap p<0.05 (Rademacher, B=9,999). "
            "Family proxy = ages 0-15 plus 30-49, overlapping the 30-39 group. Age is age at 30 June. The year to "
            "June 2020 includes about 3 months of pandemic; reopenings fall in the years to June 2021 and 2022.")
    fig.text(0.01, 0.005, "\n".join(textwrap.wrap(note, 190)), fontsize=7, color=INK2, va="bottom")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(ES / "migration_age_event_study.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
