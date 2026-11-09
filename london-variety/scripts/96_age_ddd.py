"""Young-adult migration: triple difference, student checks and a hospitality-worker control.

Outcome: net moves with the rest of the UK per 1,000 mid-2019 residents of the age group (as in
94_migration_age.py), borough x year ending June 2015-2025. Treatment D: standardised log borough amenity density.
All inference: CR1 clustered by borough, WCR bootstrap clustered by borough (Rademacher, B = 9,999).

1. Triple difference, stacking the young group (20-29, Y = 1) with a comparison group (family proxy, or 50+):
       y_bgt = a_bt + c_gt + e_bg + sum_{k != 2019} theta_k D_b Y_g 1[t=k] + e
   a_bt borough x year FE, c_gt group x year FE, e_bg borough x group FE (needed so theta_k is measured relative to
   2019; without it theta_k would absorb the time-invariant D x Y level difference). Period version: theta_C, theta_R,
   theta_L on D x Y x period (closure 2020-21, reopening 2022, later 2023-25; reference 2015-19 pooled) and
   theta_R - theta_C. Also the pre-period average theta over 2015-2018 as a summary pre-trend test.
2. Student check: 20-24 and 25-29 separately; 2011 full-time student share x year added; top-5 student-share
   boroughs dropped.
3. Hospitality-worker control: 2011 share of employed residents aged 16-34 working in accommodation and food (I)
   or "other" services (R, S, T, U: the finest split of arts and recreation available by age), x year in the
   young-adult event study, x Y x year in the triple difference. Variant with I only.
"""
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import CLEAN, LONDON, OUT, RAW, download, london_frame
from es_core import fit_cluster, rademacher

ES = OUT / "event_study"
NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
B, SEED = 9999, 20261028
BASE = 2019
YEARS = list(range(2015, 2026))
PERIODS = {"C": [2020, 2021], "R": [2022], "L": [2023, 2024, 2025]}
AGES = {"age20_29": [range(20, 30)], "age20_24": [range(20, 25)], "age25_29": [range(25, 30)],
        "family_0_15_30_49": [range(0, 16), range(30, 50)], "age50plus": [range(50, 200)]}
LAB = {"age20_29": "20-29", "age20_24": "20-24", "age25_29": "25-29", "family_0_15_30_49": "family proxy",
       "age50plus": "50+"}


def in_group(age, g):
    return np.logical_or.reduce([age.isin(list(r)) for r in AGES[g]])


def age_panel() -> pd.DataFrame:
    pop = pd.read_csv(RAW / "nomis" / "mye_population_mid2019_single_age_london.csv")
    pop["age"] = pop.C_AGE - 101
    m = pd.concat([pd.read_parquet(f) for f in sorted((RAW / "ons_internal_migration")
                                                      .glob("detailedestimates*.london.parquet"))])
    gla = set(LONDON)
    inn = m[m.inla.isin(gla) & ~m.outla.isin(gla)].rename(columns={"inla": "la_code"}).assign(s=1.0)
    out = m[m.outla.isin(gla) & ~m.inla.isin(gla)].rename(columns={"outla": "la_code"}).assign(s=-1.0)
    x = pd.concat([inn, out])
    x["net"] = x.moves * x.s
    lon = london_frame().la_code
    rows = []
    for g in AGES:
        n = x[in_group(x.age, g)].groupby(["la_code", "year_ending_june"]).net.sum().rename("net_moves").reset_index()
        p = pop[in_group(pop.age, g)].groupby("GEOGRAPHY_CODE").OBS_VALUE.sum().rename("pop_mid2019")
        n = n[n.la_code.isin(lon)].merge(p, left_on="la_code", right_index=True)
        n["group"] = g
        rows.append(n)
    d = pd.concat(rows, ignore_index=True)
    d["y"] = d.net_moves / d.pop_mid2019 * 1000
    # check against the round 6 panel
    old = pd.read_csv(CLEAN / "migration_net_by_age_group.csv")
    c = d.merge(old, on=["la_code", "year_ending_june", "group"], how="inner")
    assert len(c) == 352 * 3 and np.allclose(c.y, c.net_per1k_group), "age panel differs from round 6"
    return d


def census_controls() -> pd.DataFrame:
    lon = london_frame().la_code
    geo = ",".join(lon)
    f1 = download(f"{NOMIS}/NM_623_1.data.csv?geography={geo}&rural_urban=0&cell=0,9&measures=20100"
                  "&select=geography_code,cell,obs_value", RAW / "census2011" / "ks501ew_students_la.csv")
    s = pd.read_csv(f1).pivot(index="GEOGRAPHY_CODE", columns="CELL", values="OBS_VALUE")
    f2 = download(f"{NOMIS}/NM_771_1.data.csv?geography={geo}&c_sex=0&c_indgpuk11=0,6,15&c_age=1,2,3,4,5"
                  "&measures=20100&select=geography_code,c_indgpuk11,c_age,obs_value",
                  RAW / "census2011" / "dc6110ew_industry_age16_34_la.csv")
    h = pd.read_csv(f2).groupby(["GEOGRAPHY_CODE", "C_INDGPUK11"]).OBS_VALUE.sum().unstack()
    c = pd.DataFrame({"student_share": s[9] / s[0],
                      "hosp_share_I_RSTU": (h[6] + h[15]) / h[0], "hosp_share_I": h[6] / h[0],
                      "employed_16_34": h[0]})
    c.index.name = "la_code"
    c = c.reset_index()
    for v in ["student_share", "hosp_share_I_RSTU", "hosp_share_I"]:
        c[f"X_{v}"] = (c[v] - c[v].mean()) / c[v].std()
    c.to_csv(CLEAN / "borough_student_hospitality_2011.csv", index=False)
    return c


def year_dummies(t, years):
    return np.column_stack([(t == y).astype(float) for y in years])


def es_fit(df, w, controls=(), contrasts_periods=True):
    """Single-group borough event study, optional controls x year, plus period contrasts of the year coefficients
    (closure average, reopening, later average, reopening minus closure)."""
    df = df.sort_values(["la_code", "year_ending_june"]).reset_index(drop=True)
    ev = [y for y in YEARS if y != BASE]
    unit = pd.get_dummies(df.la_code, dtype=float)
    T = year_dummies(df.year_ending_june.values, ev)
    blocks, names = [unit.values, T], [f"fe_{c}" for c in unit.columns] + [f"t_{y}" for y in ev]
    blocks.append(T * df.D.values[:, None]); names += [f"D:{y}" for y in ev]
    for c in controls:
        blocks.append(T * df[c].values[:, None]); names += [f"{c}:{y}" for y in ev]
    con = {}
    if contrasts_periods:
        avg = lambda ys: {f"D:{y}": 1 / len(ys) for y in ys}
        con = {"closure_avg": avg(PERIODS["C"]), "reopening": avg(PERIODS["R"]), "later_avg": avg(PERIODS["L"]),
               "pre_avg_2015_2018": avg([y for y in (2015, 2016, 2017, 2018) if y in YEARS])}  # pre-period years present
        r_minus_c = {f"D:{y}": 1.0 for y in PERIODS["R"]}
        for y in PERIODS["C"]:
            r_minus_c[f"D:{y}"] = -1 / len(PERIODS["C"])
        con["reopening_minus_closure"] = r_minus_c
    tab, _ = fit_cluster(np.hstack(blocks), df.y.values, names, [f"D:{y}" for y in ev], cl_se=df.la_code.values,
                         w=w, k_nested=unit.shape[1], contrasts=con)
    tab["term"] = tab.name.str.replace("D:", "", regex=False)
    return tab.assign(n_obs=tab.attrs["n_obs"], k=tab.attrs["k"], n_boroughs=df.la_code.nunique())


def ddd_fit(stack, w, controls=(), period_model=False):
    stack = stack.sort_values(["la_code", "group", "year_ending_june"]).reset_index(drop=True)
    t = stack.year_ending_june.values
    Y = stack.Y.values
    bt = pd.get_dummies(stack.la_code + "_" + stack.year_ending_june.astype(str), dtype=float)
    gt = year_dummies(t, YEARS) * Y[:, None]                         # young x year (all years)
    boroughs = sorted(stack.la_code.unique())
    bg = np.column_stack([((stack.la_code == b) & (Y == 1)).astype(float) for b in boroughs[1:]])
    blocks = [bt.values, gt, bg]
    names = [f"bt_{c}" for c in bt.columns] + [f"gt_{y}" for y in YEARS] + [f"bg_{b}" for b in boroughs[1:]]
    if period_model:
        P = {k: np.isin(t, v).astype(float) for k, v in PERIODS.items()}
        for k in ["C", "R", "L"]:
            blocks.append((P[k] * stack.D.values * Y)[:, None]); names.append(f"DY:{k}")
        tested = ["DY:C", "DY:R", "DY:L"]
        con = {"reopening_minus_closure": {"DY:R": 1.0, "DY:C": -1.0}}
    else:
        ev = [y for y in YEARS if y != BASE]
        T = year_dummies(t, ev)
        blocks.append(T * (stack.D.values * Y)[:, None]); names += [f"DY:{y}" for y in ev]
        tested = [f"DY:{y}" for y in ev]
        avg = lambda ys: {f"DY:{y}": 1 / len(ys) for y in ys}
        con = {"closure_avg": avg(PERIODS["C"]), "reopening": avg(PERIODS["R"]), "later_avg": avg(PERIODS["L"]),
               "pre_avg_2015_2018": avg([y for y in (2015, 2016, 2017, 2018) if y in YEARS])}  # pre-period years present
        r_minus_c = {"DY:2022": 1.0, "DY:2020": -0.5, "DY:2021": -0.5}
        con["reopening_minus_closure"] = r_minus_c
    ev_all = [y for y in YEARS if y != BASE]
    T_all = year_dummies(t, ev_all)
    for c in controls:
        blocks.append(T_all * (stack[c].values * Y)[:, None]); names += [f"{c}Y:{y}" for y in ev_all]
    X = np.hstack(blocks)
    tab, _ = fit_cluster(X, stack.y.values, names, tested, cl_se=stack.la_code.values, w=w,
                         k_nested=bt.shape[1] + bg.shape[1], contrasts=con)
    tab["term"] = tab.name.str.replace("DY:", "", regex=False)
    return tab.assign(n_obs=tab.attrs["n_obs"], k=tab.attrs["k"])


def cell(t, term):
    r = t.set_index("term").loc[term]
    return f"{r.coef:.2f} ({r.p_wcb:.3f})"


def main():
    w = rademacher(B, 32, SEED)
    d = age_panel()
    ctl = census_controls()
    bv = pd.read_csv(CLEAN / "event_study_borough_vars.csv")[["la_code", "D_cont"]].rename(columns={"D_cont": "D"})
    d = d.merge(bv, on="la_code").merge(ctl, on="la_code")
    d.to_csv(CLEAN / "migration_net_by_age_group_extended.csv", index=False)
    print(ctl[["student_share", "hosp_share_I_RSTU", "hosp_share_I"]].describe().round(3).to_string())
    print("corr with D:", d.drop_duplicates("la_code")[["D", "X_student_share", "X_hosp_share_I_RSTU",
                                                         "X_hosp_share_I"]].corr().iloc[0].round(3).to_dict())
    results = []

    # 1. triple difference
    for comp in ["family_0_15_30_49", "age50plus"]:
        st = d[d.group.isin(["age20_29", comp])].copy()
        st["Y"] = (st.group == "age20_29").astype(float)
        for ctrl_lab, ctrls in (("none", ()), ("hospitality I+RSTU", ("X_hosp_share_I_RSTU",)),
                                ("hospitality I only", ("X_hosp_share_I",))):
            for model, pm in (("yearly", False), ("periods", True)):
                t = ddd_fit(st, w, ctrls, period_model=pm)
                results.append(t.assign(analysis="triple difference", comparison=f"20-29 vs {LAB[comp]}",
                                        model=model, control=ctrl_lab, sample="32 boroughs"))
        print("DDD", comp, flush=True)

    # 2 and 3. single-group young-adult event studies
    top5 = ctl.nlargest(5, "student_share").la_code.tolist()
    for g in ["age20_29", "age20_24", "age25_29"]:
        base = d[d.group == g]
        variants = [("none", (), "32 boroughs", base),
                    ("student share", ("X_student_share",), "32 boroughs", base),
                    ("none", (), "drop top-5 student boroughs", base[~base.la_code.isin(top5)])]
        if g == "age20_29":
            variants += [("hospitality I+RSTU", ("X_hosp_share_I_RSTU",), "32 boroughs", base),
                         ("hospitality I only", ("X_hosp_share_I",), "32 boroughs", base)]
        for ctrl_lab, ctrls, smp, df in variants:
            if smp != "32 boroughs":
                df = df.copy()
            t = es_fit(df, rademacher(B, df.la_code.nunique(), SEED), ctrls)
            results.append(t.assign(analysis="young-adult event study", comparison=LAB[g], model="yearly",
                                    control=ctrl_lab, sample=smp))
        print("ES", g, flush=True)

    res = pd.concat(results, ignore_index=True).drop(columns=["t_bootcluster"])
    res.to_csv(ES / "age_ddd_student_hospitality.csv", index=False)
    write_tables(res, top5, ctl)
    plot(res)


def write_tables(res, top5, ctl):
    names = dict(zip(london_frame().la_code, london_frame().la_name))
    L = []
    # triple difference, yearly
    L.append("### Triple difference, yearly (theta_k per SD of log amenity density; per 1,000 group residents; WCB p)\n")
    yrs = [str(y) for y in YEARS if y != BASE]
    L.append("| Comparison | Control | " + " | ".join(yrs) + " | pre avg 2015-18 | closure avg | reopening | later avg | "
             "reopening - closure |")
    L.append("|---|---|" + "---|" * (len(yrs) + 5))
    for (comp, ctrl), t in res[(res.analysis == "triple difference") & (res.model == "yearly")].groupby(
            ["comparison", "control"], sort=False):
        L.append(f"| {comp} | {ctrl} | " + " | ".join(cell(t, y) for y in yrs) + " | "
                 + " | ".join(cell(t, k) for k in ["pre_avg_2015_2018", "closure_avg", "reopening", "later_avg",
                                                   "reopening_minus_closure"]) + " |")
    L.append("\n### Triple difference, period model (reference 2015-2019 pooled)\n")
    L.append("| Comparison | Control | Closure | Reopening | Later | Reopening - closure | N |")
    L.append("|---|---|---|---|---|---|---|")
    for (comp, ctrl), t in res[(res.analysis == "triple difference") & (res.model == "periods")].groupby(
            ["comparison", "control"], sort=False):
        L.append(f"| {comp} | {ctrl} | {cell(t, 'C')} | {cell(t, 'R')} | {cell(t, 'L')} | "
                 f"{cell(t, 'reopening_minus_closure')} | {int(t.n_obs.iloc[0])} |")
    L.append("\n### Young-adult event studies: 2020 and 2022 coefficients and period contrasts\n")
    L.append("| Age group | Control | Sample | 2015 | 2016 | 2020 | 2021 | 2022 | closure avg | reopening - closure | N |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for (g, ctrl, smp), t in res[res.analysis == "young-adult event study"].groupby(
            ["comparison", "control", "sample"], sort=False):
        L.append(f"| {g} | {ctrl} | {smp} | " + " | ".join(cell(t, y) for y in ["2015", "2016", "2020", "2021", "2022"])
                 + f" | {cell(t, 'closure_avg')} | {cell(t, 'reopening_minus_closure')} | {int(t.n_obs.iloc[0])} |")
    top = ", ".join(f"{names[c]} ({ctl.set_index('la_code').student_share[c]:.1%})" for c in top5)
    L.append(f"\nTop-5 student-share boroughs dropped: {top}.")
    (ES / "age_ddd_student_hospitality.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def plot(res):
    C = {"none": "#2a78d6", "hospitality I+RSTU": "#eb6834"}
    INK, INK2, GRID, PRE = "#0b0b0b", "#52514e", "#e4e3df", "#efeeea"
    yrs = [str(y) for y in YEARS]
    pos = {y: i for i, y in enumerate(yrs)}
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.2), sharey=True)
    panels = [("triple difference", "20-29 vs family proxy"), ("triple difference", "20-29 vs 50+"),
              ("young-adult event study", "20-29")]
    for ax, (an, comp) in zip(axes, panels):
        ax.axvspan(-0.5, pos["2020"] - 0.5, color=PRE, lw=0, zorder=0)
        ax.axhline(0, color=INK2, lw=0.8)
        for ctrl, dx in (("none", -0.12), ("hospitality I+RSTU", 0.12)):
            t = res[(res.analysis == an) & (res.comparison == comp) & (res.model == "yearly") & (res.control == ctrl)
                    & (res["sample"] == "32 boroughs") & res.term.str.fullmatch(r"\d{4}")]
            t = pd.concat([t, pd.DataFrame([{"term": "2019", "coef": 0.0, "ci_low": 0.0, "ci_high": 0.0, "p_wcb": 1.0}])])
            x = t.term.map(pos) + dx
            sig = t.p_wcb < 0.05
            lab = "no extra control" if ctrl == "none" else "+ young hospitality-worker share x year"
            ax.vlines(x, t.ci_low, t.ci_high, color=C[ctrl], lw=1.3)
            ax.scatter(x[sig], t.coef[sig], s=24, color=C[ctrl], zorder=3, label=f"{lab} (WCB p<0.05)")
            ax.scatter(x[~sig], t.coef[~sig], s=24, facecolor="#fcfcfb", edgecolor=C[ctrl], zorder=3,
                       label=f"{lab} (WCB p>=0.05)")
        ax.set_xticks(range(len(yrs)))
        ax.set_xticklabels([y[2:] for y in yrs])
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.spines[["top", "right"]].set_visible(False)
        ttl = f"Triple difference: {comp}" if an == "triple difference" else "Event study: ages 20-29"
        ax.set_title(ttl, loc="left", fontsize=9, color=INK)
        ax.set_xlabel("Year ending June")
    axes[0].set_ylabel("Net moves per 1,000 group residents,\nper SD of log borough amenity density")
    axes[0].legend(fontsize=7, frameon=False, loc="lower left")
    note = ("Triple difference: borough x year, age-group x year and borough x age-group FE; theta_k on D x young x year, "
            "2019 omitted. Event study: borough and year FE, D x year. Bars: 95% CI, CR1 clustered by borough (32). "
            "Filled: WCR bootstrap p<0.05 by borough (B=9,999). Hospitality control: 2011 share of employed residents "
            "aged 16-34 in accommodation and food (I) or other services (R-U), x (young x) year.")
    fig.text(0.01, 0.01, "\n".join(textwrap.wrap(note, 220)), fontsize=7, color=INK2, va="bottom")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(ES / "age_ddd.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
