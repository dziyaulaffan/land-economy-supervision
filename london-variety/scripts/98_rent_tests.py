"""Rent tests for the young-adult migration results (2016-2025 migration sample, as in the report).

1. Rent-change control: each borough's change in log PIPR rent from 2019Q4 to 2021Q4 (standardised), interacted
   with the young-adult indicator and year, added to the triple difference against the family proxy and ages 50+.
2. Pre-pandemic rent responsiveness, years to June 2016-2019 only: 20-29 net migration per 1,000 on the borough's
   lagged annual change in log rent (log PIPR index June t-1 minus June t-2, x 100), borough and year FE; and the
   same regressor x young in a triple difference against the family proxy (borough x year, group x year and
   borough x group FE). PIPR borough series start January 2015, so the lagged change exists from the year to June
   2017; a contemporaneous variant (June t minus June t-1) covers 2016-2019.
3. 30-39 and 20-29 event-study coefficients for 2021 and 2022, from report_migration_2016.csv.
All inference: CR1 clustered by borough, WCR bootstrap clustered by borough (Rademacher, B = 9,999).
"""
import importlib.util

import numpy as np
import pandas as pd

from config import CLEAN, OUT
from es_core import fit_cluster, rademacher

ES = OUT / "event_study"
_spec = importlib.util.spec_from_file_location("m96", __file__.replace("98_rent_tests.py", "96_age_ddd.py"))
m96 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m96)
COMP = {"family_0_15_30_49": "family proxy", "age50plus": "ages 50+"}


def cell(t, term):
    r = t.set_index("term").loc[term]
    return f"{r.coef:.2f} ({r.p_wcb:.3f})"


def rent_change_1921():
    q = pd.read_csv(CLEAN / "event_study_rents_quarterly.csv").pivot(index="la_code", columns="q", values="y")
    r = (q["2021Q4"] - q["2019Q4"]).rename("rent_chg_1921").reset_index()   # log points (100 x log index)
    r["X_rent_chg_1921"] = (r.rent_chg_1921 - r.rent_chg_1921.mean()) / r.rent_chg_1921.std()
    return r


def june_rent_changes():
    m = pd.read_csv(CLEAN / "rents_monthly_la.csv", usecols=["month", "la_code", "index"])
    m = m[m.la_code.str.startswith("E09") & m.month.str.endswith("-06-01")].copy()
    m["yr"] = m.month.str[:4].astype(int)
    lv = m.pivot(index="la_code", columns="yr", values="index").pipe(np.log) * 100
    rows = []
    for t in range(2016, 2020):
        for b in lv.index:
            rows.append({"la_code": b, "year_ending_june": t,
                         "dlr_lag": lv.loc[b, t - 1] - lv.loc[b, t - 2] if t - 2 in lv.columns else np.nan,
                         "dlr_contemp": lv.loc[b, t] - lv.loc[b, t - 1]})
    return pd.DataFrame(rows)


def fe_rent_fit(df, x, w):
    """y = a_b + l_t + beta x_bt + e."""
    df = df.sort_values(["la_code", "year_ending_june"]).reset_index(drop=True)
    unit = pd.get_dummies(df.la_code, dtype=float)
    yrs = sorted(df.year_ending_june.unique())[1:]
    T = m96.year_dummies(df.year_ending_june.values, yrs)
    X = np.hstack([unit.values, T, df[[x]].values])
    names = [f"fe_{c}" for c in unit.columns] + [f"t_{y}" for y in yrs] + ["rent"]
    tab, _ = fit_cluster(X, df.y.values, names, ["rent"], cl_se=df.la_code.values, w=w, k_nested=unit.shape[1])
    return tab.assign(term="rent", n_obs=len(df))


def ddd_rent_fit(st, x, w):
    """y_bgt = a_bt + c_gt + e_bg + beta x_bt Y_g + e."""
    st = st.sort_values(["la_code", "group", "year_ending_june"]).reset_index(drop=True)
    Y = st.Y.values
    bt = pd.get_dummies(st.la_code + "_" + st.year_ending_june.astype(str), dtype=float)
    gt = m96.year_dummies(st.year_ending_june.values, sorted(st.year_ending_june.unique())) * Y[:, None]
    boroughs = sorted(st.la_code.unique())
    bg = np.column_stack([((st.la_code == b) & (Y == 1)).astype(float) for b in boroughs[1:]])
    X = np.hstack([bt.values, gt, bg, (st[x].values * Y)[:, None]])
    names = [f"bt_{c}" for c in bt.columns] + [f"gt_{i}" for i in range(gt.shape[1])] + \
            [f"bg_{b}" for b in boroughs[1:]] + ["rentY"]
    tab, _ = fit_cluster(X, st.y.values, names, ["rentY"], cl_se=st.la_code.values, w=w,
                         k_nested=bt.shape[1] + bg.shape[1])
    return tab.assign(term="rent x young", n_obs=len(st))


def main():
    w = rademacher(m96.B, 32, m96.SEED)
    d = pd.read_csv(CLEAN / "migration_net_by_age_group_extended.csv")
    rc = rent_change_1921()
    d = d.merge(rc, on="la_code")
    L, out = [], []

    # 1. triple difference with the rent-change control, 2016-2025
    m96.YEARS = list(range(2016, 2026))
    ext = d[d.year_ending_june.isin(m96.YEARS)]
    print("rent change 2019Q4-2021Q4 (log points):", rc.rent_chg_1921.describe().round(2).to_dict())
    print("corr with D:", round(np.corrcoef(d.drop_duplicates("la_code").D, d.drop_duplicates("la_code").rent_chg_1921)[0, 1], 3))
    terms = ["2020", "2021", "2022", "reopening_minus_closure"]
    L.append("### 1. Triple difference with the 2019Q4-2021Q4 rent-change control (2016-2025; WCB p)\n")
    L.append("| Comparison | Control | 2020 | 2021 | 2022 | Reopening - closure |")
    L.append("|---|---|---|---|---|---|")
    for comp, lab in COMP.items():
        st = ext[ext.group.isin(["age20_29", comp])].copy()
        st["Y"] = (st.group == "age20_29").astype(float)
        for c, cl in (((), "none"), (("X_rent_chg_1921",), "rent change 2019Q4-2021Q4 x young x year")):
            t = m96.ddd_fit(st, w, c)
            out.append(t.assign(test="1 rent-change control", group=comp, control=cl))
            L.append(f"| {lab} | {cl} | " + " | ".join(cell(t, k) for k in terms) + " |")
    m96.YEARS = list(range(2015, 2026))

    # 2. pre-pandemic rent responsiveness, 2016-2019
    rch = june_rent_changes()
    pre = d[d.year_ending_june.between(2016, 2019)].merge(rch, on=["la_code", "year_ending_june"])
    print("lagged change SD:", round(pre.drop_duplicates(["la_code", "year_ending_june"]).dlr_lag.std(), 2),
          "contemporaneous SD:", round(pre.drop_duplicates(["la_code", "year_ending_june"]).dlr_contemp.std(), 2))
    L.append("\n### 2. Pre-pandemic rent responsiveness (net moves per 1,000 per log point of rent change; WCB p)\n")
    L.append("| Model | Rent change | Years | Coefficient (p) | CI 95% (CR1) | N |")
    L.append("|---|---|---|---|---|---|")
    for x, xl, yrs in (("dlr_lag", "lagged, June t-1 vs June t-2", (2017, 2019)),
                       ("dlr_contemp", "contemporaneous, June t vs June t-1", (2016, 2019))):
        p = pre[pre.year_ending_june.between(*yrs)]
        yr = f"{yrs[0]}-{yrs[1]}"
        t = fe_rent_fit(p[p.group == "age20_29"], x, w)
        out.append(t.assign(test="2 pre-pandemic", group="age20_29", control=f"{x} {yr}"))
        r = t.iloc[0]
        L.append(f"| 20-29, borough and year FE | {xl} | {yr} | {r.coef:.3f} ({r.p_wcb:.3f}) | "
                 f"[{r.ci_low:.3f}, {r.ci_high:.3f}] | {int(r.n_obs)} |")
        st = p[p.group.isin(["age20_29", "family_0_15_30_49"])].copy()
        st["Y"] = (st.group == "age20_29").astype(float)
        t = ddd_rent_fit(st, x, w)
        out.append(t.assign(test="2 pre-pandemic", group="family_0_15_30_49", control=f"{x} {yr}"))
        r = t.iloc[0]
        L.append(f"| Triple difference vs family proxy | {xl} | {yr} | {r.coef:.3f} ({r.p_wcb:.3f}) | "
                 f"[{r.ci_low:.3f}, {r.ci_high:.3f}] | {int(r.n_obs)} |")

    # 3. 30-39 alongside 20-29 (existing 2016-2025 event studies)
    rep = pd.read_csv(ES / "report_migration_2016.csv", dtype={"term": str})
    rep = rep[(rep.analysis == "event study") & (rep.control == "none") & (rep["sample"] == "32 boroughs")]
    L.append("\n### 3. Event-study coefficients by age group (2016-2025; WCB p)\n")
    L.append("| Age group | 2021 | 2022 |")
    L.append("|---|---|---|")
    for g, lab in (("age20_29", "20-29"), ("age30_39", "30-39")):
        t = rep[rep.group == g]
        L.append(f"| {lab} | {cell(t, '2021')} | {cell(t, '2022')} |")

    pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore").to_csv(
        ES / "rent_tests.csv", index=False)
    (ES / "rent_tests.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
