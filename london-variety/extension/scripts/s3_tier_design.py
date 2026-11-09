"""Step 3: tier closures (pre-analysis plan, Design 2).

E_b = days 1 Jul 2020-30 Jun 2021 with indoor hospitality legally closed in LA b (B4 `indoor_closed`, population-
weighted for partial areas) on which it was not closed in every LA of the same nation (national lockdown days
excluded). Standardised across the 316 LADs. Quarterly E_bq by the same rule, 2020Q3-2021Q2.
First stage: Google retail and recreation change (B5) on E. Outcome: young (20-29) minus comparison net migration
per 1,000 in the year to June 2021 minus its 2016-2019 mean. Model: region FE + E + E x D + D + six controls +
mean weekly case rate. Each LA is its own cluster (CR1 and WCR bootstrap, B = 9,999). Balance check of E.
"""
import numpy as np
import pandas as pd

from e_core import B, SEED, fit_cluster, rademacher
from ext_config import CLEAN

DROP = {"E09000001", "E06000053"}
CTRL = ["X_telework_share", "X_garden_share", "X_flat_share", "X_private_rent_share", "X_age20_39_share",
        "X_student_share"]
COMP = {"family_0_15_30_49": "family proxy", "age50plus": "ages 50+"}
QUARTERS = ["2020Q3", "2020Q4", "2021Q1", "2021Q2"]


def extra_days():
    d = pd.read_csv(CLEAN / "b4_restrictions_daily_lad23.csv", usecols=["lad23_code", "nation", "date",
                                                                         "indoor_closed"])
    d = d[(d.date >= "2020-07-01") & (d.date <= "2021-06-30")].copy()
    d["indoor_closed"] = d.indoor_closed.astype(float)
    nat = d.groupby(["nation", "date"]).indoor_closed.min().rename("national").reset_index()
    d = d.merge(nat, on=["nation", "date"])
    d["extra"] = d.indoor_closed * (d.national < 0.999)
    d["quarter"] = pd.PeriodIndex(pd.to_datetime(d.date), freq="Q").astype(str)
    e = d.groupby("lad23_code").extra.sum().rename("E_days")
    eq = d.groupby(["lad23_code", "quarter"]).extra.sum().rename("E_days_q").reset_index()
    nat_days = nat[nat.national >= 0.999].groupby("nation").size()
    return e.reset_index().rename(columns={"lad23_code": "la_code"}), eq.rename(columns={"lad23_code": "la_code"}), nat_days


def ols(df, y, regs, fe=None, cluster="la_code", w=None, contrasts=None, absorb=()):
    df = df.dropna(subset=[y] + regs).reset_index(drop=True)
    blocks, names = [np.ones((len(df), 1))], ["const"]
    if fe:
        for f in fe:
            dm = pd.get_dummies(df[f], dtype=float, drop_first=True)
            blocks.append(dm.values); names += [f"{f}_{c}" for c in dm.columns]
    if absorb:
        blocks.append(df[list(absorb)].values.astype(float)); names += list(absorb)
    blocks.append(df[regs].values.astype(float)); names += regs
    G = df[cluster].nunique()
    tab, _ = fit_cluster(np.hstack(blocks), df[y].values, names, regs, cl_se=df[cluster].values,
                         w=rademacher(B, G, SEED) if w is None else w, contrasts=contrasts)
    return tab.assign(n_obs=len(df), n_clusters=G)


def fmt(t, term, d=3):
    r = t.set_index("name").loc[term]
    return f"{r.coef:.{d}f} ({r.p_wcb:.3f})"


def main():
    E, Eq, nat_days = extra_days()
    c = pd.read_csv(CLEAN / "b3_la_crosssection.csv")[["la_code", "region", "z_log_per1k_IR"]].rename(
        columns={"z_log_per1k_IR": "D"})
    s = pd.read_csv(CLEAN / "s1_controls_la2023.csv")[["la_code"] + CTRL]
    cr = pd.read_csv(CLEAN / "s3_case_rates_la2023_year_to_june2021.csv")
    rate_col = "mean_weekly_rate_jul2020_jun2021"
    cr = cr[["la_code", rate_col]].rename(columns={rate_col: "case_rate"})
    x = c.merge(E, on="la_code").merge(s, on="la_code").merge(cr, on="la_code", how="left")
    x = x[~x.la_code.isin(DROP)].copy()
    x["E"] = (x.E_days - x.E_days.mean()) / x.E_days.std()
    x["C"] = (x.case_rate - x.case_rate.mean()) / x.case_rate.std()
    x["ExD"] = x.E * x.D
    L = [f"National lockdown days excluded per nation (1 Jul 2020-30 Jun 2021): {nat_days.to_dict()}.",
         f"E_days: mean {x.E_days.mean():.1f}, SD {x.E_days.std():.1f}, min {x.E_days.min():.1f}, "
         f"max {x.E_days.max():.1f}; LAs with E_days > 0: {(x.E_days > 0).sum()} of {len(x)}; "
         f"case rate missing for {x.case_rate.isna().sum()} LAs.", ""]

    # first stage, cross-section
    m = pd.read_csv(CLEAN / "b5_closure_intensity_la_quarter.csv")
    m = m[m.quarter.isin(QUARTERS) & ~m.low_coverage]
    x = x.merge(m.groupby("la_code").closure_rr_mean.mean().rename("rr_mean").reset_index(), on="la_code", how="left")
    fs = ols(x, "rr_mean", ["E"] + CTRL, fe=["region"])
    out = [fs.assign(part="first stage, cross-section")]
    L.append(f"First stage (cross-section): mean retail+rec change 2020Q3-2021Q2 on E (per SD), region FE, six "
             f"controls: {fmt(fs, 'E')}, N = {int(fs.n_obs.iloc[0])}.")
    # first stage, quarterly panel
    pq = Eq.merge(m[["la_code", "quarter", "closure_rr_mean"]], on=["la_code", "quarter"]).merge(
        c[["la_code", "region"]], on="la_code")
    pq = pq[~pq.la_code.isin(DROP)]
    pq["E_q10"] = pq.E_days_q / 10
    rq_cols = []
    for (rg, qq) in {(a, b) for a, b in zip(pq.region, pq.quarter) if b != QUARTERS[0]}:
        col = f"rq_{rg}_{qq}"
        pq[col] = ((pq.region == rg) & (pq.quarter == qq)).astype(float)
        rq_cols.append(col)
    fq = ols(pq, "closure_rr_mean", ["E_q10"], fe=["la_code"], absorb=sorted(rq_cols))
    out.append(fq.assign(part="first stage, quarterly panel"))
    L.append(f"First stage (quarterly panel 2020Q3-2021Q2): retail+rec change on extra closure days (per 10 days), "
             f"LA FE and region x quarter FE: {fmt(fq, 'E_q10')}, N = {int(fq.n_obs.iloc[0])}.")
    L.append("")

    # outcome
    mg = pd.read_csv(CLEAN / "b3_migration_la_year_by_age_group.csv")
    mg = mg[mg.group.isin(["age20_29"] + list(COMP))].pivot_table(index=["la_code", "year_ending_june"],
                                                                    columns="group", values="all_net_per1k")
    mg = mg.reset_index()
    L.append("| Comparison | Model | E | E x D | D | Case rate | N |")
    L.append("|---|---|---|---|---|---|---|")
    for comp, lab in COMP.items():
        mg["dy"] = mg.age20_29 - mg[comp]
        pre = mg[mg.year_ending_june.between(2016, 2019)].groupby("la_code").dy.mean().rename("pre")
        slope = mg[mg.year_ending_june.between(2016, 2019)].groupby("la_code").apply(
            lambda g: np.polyfit(g.year_ending_june, g.dy, 1)[0], include_groups=False).rename("pre_trend")
        y21 = mg[mg.year_ending_june == 2021].set_index("la_code").dy.rename("y21")
        z = x.merge(pd.concat([pre, slope, y21], axis=1).reset_index(), on="la_code")
        z["delta"] = z.y21 - z.pre
        for mlab, regs in (("E only", ["E", "D"] + CTRL + ["C"]), ("headline", ["E", "ExD", "D"] + CTRL + ["C"])):
            t = ols(z, "delta", regs, fe=["region"])
            out.append(t.assign(part=f"outcome {mlab}", comp=comp))
            L.append(f"| {lab} | {mlab} | {fmt(t, 'E', 2)} | " + (fmt(t, 'ExD', 2) if "ExD" in regs else "")
                     + f" | {fmt(t, 'D', 2)} | {fmt(t, 'C', 2)} | {int(t.n_obs.iloc[0])} |")
        if comp == "family_0_15_30_49":
            z["pre_trend_std"] = (z.pre_trend - z.pre_trend.mean()) / z.pre_trend.std()
            bal = ols(z, "E", ["pre_trend_std", "D", "C"] + CTRL, fe=["region"])
            out.append(bal.assign(part="balance"))
            L.append("")
            L.append("Balance (E on pre-2020 young-minus-family trend, D, case rate and controls, region FE; per SD): "
                     + "; ".join(f"{r} {fmt(bal, r)}" for r in ["pre_trend_std", "D", "C"] + CTRL) + ".")
            L.append("")
    res = pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore")
    res.to_csv(CLEAN / "s3_tier_design.csv", index=False)
    x.to_csv(CLEAN / "s3_extra_closure_days_la.csv", index=False)
    Eq.to_csv(CLEAN / "s3_extra_closure_days_la_quarter.csv", index=False)
    (CLEAN / "s3_tier_design.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
