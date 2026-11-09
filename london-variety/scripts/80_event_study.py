"""Borough event studies: net migration (annual) and private rents (quarterly).

    y_bt = a_b + l_t + sum_{k != base} beta_k * 1[t = k] * D_b
                     + sum_c sum_{k != base} gamma_ck * 1[t = k] * X_cb + e_bt

D_b is either the standardised log amenity density (continuous) or within-zone amenity tercile
dummies T2, T3 (binned, T1 = reference). X_cb are time-invariant controls, standardised across the
32 boroughs and entered one at a time, then all together.

Inference: CR1 standard errors clustered by borough (fixest/reghdfe convention: borough fixed
effects are nested in clusters and not counted in K), and wild cluster restricted bootstrap
(WCR, null imposed, Rademacher weights, B draws) p-values for every event-time coefficient.
"""
import numpy as np
import pandas as pd
from scipy import stats

from config import CLEAN, OUT
from es_core import fit_cluster

B = 9999
SEED = 20261028
CONTROLS = {"garden": "garden_share", "telework": "telework_share", "age2039": "age20_39_share",
            "privrent": "private_rent_share"}
SPECS = {"baseline": [], **{f"+{k}": [k] for k in CONTROLS}, "+all": list(CONTROLS)}
ES = OUT / "event_study"
ES.mkdir(parents=True, exist_ok=True)


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def borough_vars() -> pd.DataFrame:
    a = pd.read_csv(CLEAN / "london_amenity_density_2019.csv")
    c = pd.read_csv(CLEAN / "controls_borough.csv")
    d = a[["la_code", "la_name", "london_zone", "per1k_IR", "pop_mid2019"]].merge(
        c[["la_code", *CONTROLS.values()]], on="la_code")
    assert len(d) == 32
    d["D_cont"] = zscore(np.log(d.per1k_IR))
    # terciles within zone by rank: Inner (13) -> 4/4/5, Outer (19) -> 6/6/7
    r = d.groupby("london_zone").per1k_IR.rank(method="first")
    n = d.groupby("london_zone").per1k_IR.transform("size")
    d["tercile"] = np.ceil(3 * r / n).astype(int)
    for k, col in CONTROLS.items():
        d[f"X_{k}"] = zscore(d[col])
    return d


def panels(bv: pd.DataFrame) -> dict:
    m = pd.read_csv(CLEAN / "migration_panel_borough_year.csv")
    m = m.merge(bv, on="la_code", suffixes=("", "_bv"))
    m["y"] = m.nonlondon_net / m.pop_mid2019 * 1000
    m["period"] = m.year_ending_june.astype(str)

    r = pd.read_csv(CLEAN / "rents_monthly_la.csv", parse_dates=["month"])
    r = r[r.la_code.isin(bv.la_code)]
    r["q"] = r.month.dt.to_period("Q")
    q = r.groupby(["la_code", "q"]).agg(index=("index", "mean"), n_months=("index", "size")).reset_index()
    q = q[q.n_months == 3]  # complete quarters only
    q["y"] = 100 * np.log(q["index"])
    q["period"] = q.q.astype(str)
    q = q.merge(bv, on="la_code")
    q.to_csv(CLEAN / "event_study_rents_quarterly.csv", index=False)  # read by 85_contdid.R
    return {
        "migration": dict(df=m, base="2019", ylab="Net migration with rest of UK per 1,000 (2019 pop)",
                          xlab="Year ending June", first_post="2020"),
        "rents": dict(df=q, base="2019Q4", ylab="100 x log PIPR index", xlab="Quarter", first_post="2020Q1"),
    }


def design(df: pd.DataFrame, base: str, treat_cols: list, ctrl_cols: list):
    periods = sorted(df.period.unique())
    ev = [p for p in periods if p != base]
    unit = pd.get_dummies(df.la_code, dtype=float)
    per = pd.get_dummies(df.period, dtype=float)[ev]
    blocks, names = [unit.values, per.values], [f"fe_{c}" for c in unit.columns] + [f"t_{p}" for p in ev]
    tested = []
    for v in treat_cols + ctrl_cols:
        blocks.append(per.values * df[v].values[:, None])
        cols = [f"{v}:{p}" for p in ev]
        names += cols
        if v in treat_cols:
            tested += cols
    X = np.hstack(blocks)
    return X, names, tested, ev, unit.shape[1]


def fit(df, base, treat_cols, ctrl_cols, rng_w):
    X, names, tested, ev, n_unit = design(df, base, treat_cols, ctrl_cols)
    tab, V = fit_cluster(X, df.y.values, names, tested, cl_se=df.la_code.values, w=rng_w, k_nested=n_unit)
    split = tab.name.str.rsplit(":", n=1, expand=True)
    tab.insert(0, "term", split[0])
    tab.insert(1, "period", split[1])
    out = tab.drop(columns=["name", "t_bootcluster"])
    out.attrs.update(tab.attrs)
    out.attrs["V"] = pd.DataFrame(V, index=tested, columns=tested)
    return out


def pre_trend_wald(res, pre_names):
    """Cluster-robust Wald test that all pre-period treatment coefficients are zero, F(q, G-1)."""
    V = res.attrs["V"].loc[pre_names, pre_names].values
    b = res.set_index(res.term + ":" + res.period).coef.loc[pre_names].values
    q, G = len(pre_names), res.attrs["n_clusters"]
    F = b @ np.linalg.pinv(V) @ b / q
    return F, stats.f.sf(F, q, G - 1), q


def main():
    bv = borough_vars()
    bv.to_csv(CLEAN / "event_study_borough_vars.csv", index=False)
    rng = np.random.default_rng(SEED)
    w = rng.choice([-1.0, 1.0], size=(B, 32))
    tables = []
    for outcome, o in panels(bv).items():
        df = o["df"].copy()
        df["T2"] = (df.tercile == 2).astype(float)
        df["T3"] = (df.tercile == 3).astype(float)
        for ttype, tcols in (("continuous", ["D_cont"]), ("binned", ["T2", "T3"])):
            for spec, ctrls in SPECS.items():
                res = fit(df, o["base"], tcols, [f"X_{k}" for k in ctrls], w)
                for tc in tcols:
                    pre = [f"{tc}:{p}" for p in sorted(df.period.unique()) if p < o["base"]]
                    F, pF, q = pre_trend_wald(res, pre)
                    res.loc[res.term == tc, ["pretrend_F", "pretrend_p", "pretrend_q"]] = [F, pF, q]
                res.insert(0, "spec", spec)
                res.insert(0, "treatment", ttype)
                res.insert(0, "outcome", outcome)
                for a in ("n_obs", "n_clusters", "k", "k_eff"):
                    res[a] = res.attrs[a]
                res["base_period"] = o["base"]
                if ttype == "continuous" and spec == "baseline":
                    V = res.attrs["V"]
                    V.to_csv(ES / f"vcov_{outcome}_continuous_baseline.csv")
                tables.append(res)
                print(f"{outcome:9s} {ttype:10s} {spec:10s} N={res.attrs['n_obs']} K={res.attrs['k']}")
    tab = pd.concat(tables, ignore_index=True)
    tab.attrs = {}
    tab.to_csv(ES / "regression_table.csv", index=False)
    print("written", ES / "regression_table.csv", len(tab))


if __name__ == "__main__":
    main()
