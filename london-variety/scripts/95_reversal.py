"""Reversal decomposition: amenity effect in closure, reopening and later periods, and reopening minus closure.

    y_it = a_i + l_t + b_C D_i 1[t in C] + b_R D_i 1[t in R] + b_L D_i 1[t in L] (+ controls) + e_it

Reference = all periods before the closure period. Reported: b_C, b_R, b_L and b_R - b_C (linear contrast),
each with the cluster-robust CI and a WCR bootstrap p-value (Rademacher, B = 9,999, borough clusters).

Outcomes and periods
  migration (borough, years ending June 2015-2025): all ages and the four age groups of 94_migration_age.py,
      net moves with the rest of the UK per 1,000 group residents. C = 2020-2021, R = 2022, L = 2023-2025.
  rents (borough, quarterly 2015Q1-2026Q3): 100 x log PIPR index. C = 2020Q2-2021Q2, R = 2021Q3-2022Q4,
      L = 2023Q1 onwards. 2020Q1 sits in the reference period. A trend-adjusted variant (D x linear time, so the
      pre-period trend is projected forward as in 82_rent_trend_break.py) is reported as a secondary row.
  MSOA house prices (2017Q1-2026Q3): headline specification of 87/92 (MSOA and borough-by-quarter FE; distance,
      teleworkability, garden and property type each x quarter; new build, leasehold). Same quarterly periods.
      CR1 clustered by MSOA; bootstrap clustered by borough. 2026 quarters are provisional.
Borough treatment D: standardised log borough amenity density. MSOA treatment: standardised log MSOA density.
"""
import gc
import importlib.util

import numpy as np
import pandas as pd
from pyfixest.estimation import demean

from config import CLEAN, OUT
from es_core import fit_cluster, rademacher

ES = OUT / "event_study"
B, SEED = 9999, 20261028
MIG = {"C": ["2020", "2021"], "R": ["2022"], "L": ["2023", "2024", "2025"]}
Q_C = ("2020Q2", "2021Q2")
Q_R = ("2021Q3", "2022Q4")
Q_L0 = "2023Q1"
GROUP_LABELS = {"all": "Migration, all ages", "age20_29": "Migration, ages 20-29", "age30_39": "Migration, ages 30-39",
                "family_0_15_30_49": "Migration, family proxy (0-15 and 30-49)", "age50plus": "Migration, ages 50+"}


def qperiod(q: pd.Series) -> pd.Series:
    out = pd.Series("ref", index=q.index)
    out[(q >= Q_C[0]) & (q <= Q_C[1])] = "C"
    out[(q >= Q_R[0]) & (q <= Q_R[1])] = "R"
    out[q >= Q_L0] = "L"
    return out


def contrasts():
    return {"R_minus_C": {"D:R": 1.0, "D:C": -1.0}}


def borough_fit(df, period_col, w, extra_trend=False):
    """df: la_code, period (time label), y, D, and period_col in {ref, C, R, L}."""
    unit = pd.get_dummies(df.la_code, dtype=float)
    per = pd.get_dummies(df.period, dtype=float)
    per = per.iloc[:, 1:]  # drop the first period as the time-FE reference
    blocks = [unit.values, per.values]
    names = [f"fe_{c}" for c in unit.columns] + [f"t_{p}" for p in per.columns]
    for P in ["C", "R", "L"]:
        blocks.append(((df[period_col] == P) * df.D).values[:, None])
        names.append(f"D:{P}")
    if extra_trend:
        blocks.append((df.D * df.tau).values[:, None])
        names.append("D:trend")
    X = np.hstack(blocks)
    tab, _ = fit_cluster(X, df.y.values, names, ["D:C", "D:R", "D:L"], cl_se=df.la_code.values, w=w,
                         k_nested=unit.shape[1], contrasts=contrasts())
    return tab


def msoa_fit(w):
    spec = importlib.util.spec_from_file_location("m92", __file__.replace("95_reversal.py", "92_msoa_access_event_study.py"))
    m92 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m92)
    d, end = m92.analysis_sample()
    d["P"] = qperiod(d.quarter)
    ev = [q for q in sorted(d.quarter.unique()) if q != "2019Q4"]
    Q = pd.get_dummies(d.quarter, dtype=float)[ev].values
    cols = [(f"D:{P}", ((d.P == P) * d.D_msoa).values) for P in ["C", "R", "L"]]
    ctrl = [(c, d[v].values) for c, v in m92.HEADLINE_CTRLS.items()]
    ctrl += [(f"type{t}", d[f"type_{t}"].values) for t in ["S", "T", "F"]]
    static = ["type_S", "type_T", "type_F", "new_build", "leasehold"]
    k = 1 + len(cols) + len(ctrl) * len(ev) + len(static)
    Xy = np.empty((len(d), k))
    Xy[:, 0] = d.y.values
    names, j = [], 1
    for nm, v in cols:
        Xy[:, j] = v
        names.append(nm)
        j += 1
    for nm, v in ctrl:
        Xy[:, j:j + len(ev)] = Q * v[:, None]
        names += [f"{nm}:{q}" for q in ev]
        j += len(ev)
    Xy[:, j:] = d[static].values
    names += static
    Xy_dm, conv = demean(Xy, d[["msoa_id", "bq_id"]].to_numpy().astype(np.uint64), np.ones(len(d)), tol=1e-10)
    assert conv
    del Xy
    gc.collect()
    tab, _ = fit_cluster(Xy_dm[:, 1:], Xy_dm[:, 0], names, ["D:C", "D:R", "D:L"], cl_se=d.msoa_id.values,
                         cl_boot=d.la_code.values, w=w, k_absorbed_counted=d.bq_id.nunique() - 1, contrasts=contrasts())
    tab.attrs["end"] = end
    return tab


def main():
    w = rademacher(B, 32, SEED)
    out = []

    mig = pd.read_csv(CLEAN / "migration_net_by_age_group.csv")
    bv = pd.read_csv(CLEAN / "event_study_borough_vars.csv")[["la_code", "D_cont"]].rename(columns={"D_cont": "D"})
    for g, lab in GROUP_LABELS.items():
        df = mig[mig.group == g].merge(bv, on="la_code")
        df["period"] = df.year_ending_june.astype(str)
        df["y"] = df.net_per1k_group
        df["P"] = "ref"
        for P, yrs in MIG.items():
            df.loc[df.period.isin(yrs), "P"] = P
        tab = borough_fit(df, "P", w)
        out.append(tab.assign(outcome=lab, unit="borough-year", periods="C 2020-21, R 2022, L 2023-25 (years to June)",
                              clusters_se="borough (32)", clusters_boot="borough (32)"))
        print(lab, flush=True)

    r = pd.read_csv(CLEAN / "event_study_rents_quarterly.csv")
    r["D"] = r.D_cont
    r["P"] = qperiod(r.period)
    periods = sorted(r.period.unique())
    r["tau"] = r.period.map({p: i for i, p in enumerate(periods)}) - periods.index("2019Q4")
    for trend, lab in ((False, "Rents (PIPR), no trend"),
                       (True, "Rents (PIPR), pre-trend projected (secondary)")):
        tab = borough_fit(r, "P", w, extra_trend=trend)
        out.append(tab.assign(outcome=lab, unit="borough-quarter", periods="C 2020Q2-2021Q2, R 2021Q3-2022Q4, L 2023Q1-2026Q3",
                              clusters_se="borough (32)", clusters_boot="borough (32)"))
        print(lab, flush=True)

    tab = msoa_fit(w)
    out.append(tab.assign(outcome="MSOA house prices, headline spec", unit="sale",
                          periods=f"C 2020Q2-2021Q2, R 2021Q3-2022Q4, L 2023Q1-{tab.attrs['end']} (2026 provisional)",
                          clusters_se="MSOA (982)", clusters_boot="borough (32)"))
    print("MSOA house prices", flush=True)

    res = pd.concat([t.assign(n_obs=t.attrs["n_obs"], k=t.attrs["k"]) for t in out], ignore_index=True)
    res = res.drop(columns=["t_bootcluster"])
    res["term"] = res.name.map({"D:C": "closure", "D:R": "reopening", "D:L": "later", "R_minus_C": "reopening - closure"})
    res.to_csv(ES / "reversal_decomposition.csv", index=False)

    lines = ["| Outcome | Closure b_C | Reopening b_R | Later b_L | **b_R - b_C** | N |", "|---|---|---|---|---|---|"]
    for o, g in res.groupby("outcome", sort=False):
        g = g.set_index("term")
        cell = lambda t: f"{g.loc[t, 'coef']:.3f} ({g.loc[t, 'p_wcb']:.3f})"
        lines.append(f"| {o} | {cell('closure')} | {cell('reopening')} | {cell('later')} | **{cell('reopening - closure')}**"
                     f" | {int(g.n_obs.iloc[0]):,} |")
    note = ("Coefficient per SD of standardised log amenity density (borough density for migration and rents, MSOA "
            "density for house prices); WCR bootstrap p in brackets (borough clusters). Units: migration, net moves "
            "per 1,000 group residents; rents, 100 x log points; house prices, log points.")
    (ES / "reversal_decomposition.md").write_text(note + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
