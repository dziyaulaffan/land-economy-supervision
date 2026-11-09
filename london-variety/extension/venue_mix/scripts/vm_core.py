"""Estimators for the venue-mix extension, built on the pilot's es_core.fit_cluster (CR1 + WCR bootstrap)."""
import numpy as np
import pandas as pd

import vm_common  # noqa: F401  (puts extension/scripts and the pilot's scripts on sys.path)
from e_core import B, SEED  # noqa: E402
from es_core import fit_cluster, rademacher  # noqa: E402


def ols_fe(df, y, regressors, fe="lad23cd", cluster="lad23cd", boot=True, tested=None, contrasts=None):
    """OLS of y on regressors with fixed effects `fe` (a column, or a list of columns for several sets),
    CR1 SEs clustered on `cluster`, 95% CI from t(G-1), WCR bootstrap p-values (Rademacher, B = 9,999).
    Returns the table of tested coefficients (default: all regressors) and the R-squared."""
    fes = [] if fe is None else ([fe] if isinstance(fe, str) else list(fe))
    d = df.dropna(subset=[y] + list(regressors)).reset_index(drop=True)
    blocks, names, k_nested = [], [], 0
    for i, f in enumerate(fes):
        D = pd.get_dummies(d[f], dtype=float)
        if i > 0:
            D = D.iloc[:, 1:]
        blocks.append(D.values); names += [f"fe{i}_{c}" for c in D.columns]
        if f == cluster:
            k_nested += D.shape[1]
    if not fes:
        blocks.append(np.ones((len(d), 1))); names.append("const")
    for r in regressors:
        blocks.append(d[[r]].values.astype(float)); names.append(r)
    X = np.hstack(blocks)
    yv = d[y].values.astype(float)
    cl = d[cluster].values
    G = len(np.unique(cl))
    w = rademacher(B, G, SEED) if boot else None
    tab, _ = fit_cluster(X, yv, names, list(tested or regressors), cl_se=cl, w=w, k_nested=k_nested,
                         contrasts=contrasts)
    beta = np.linalg.lstsq(X, yv, rcond=None)[0]
    u = yv - X @ beta
    tab = tab.rename(columns={"se_cluster": "se", "p_cluster": "p_cr1", "ci_low": "ci_lo", "ci_high": "ci_hi"})
    if "p_wcb" not in tab:
        tab["p_wcb"] = np.nan
    return tab.assign(n_obs=len(d), n_clusters=G, r2=1 - (u ** 2).sum() / ((yv - yv.mean()) ** 2).sum(),
                      y_mean=yv.mean(), y_sd=yv.std(ddof=1))


def row(tab, term):
    r = tab.set_index("name").loc[term]
    return {k: r[k] for k in ["coef", "se", "ci_lo", "ci_hi", "p_cr1", "p_wcb", "n_obs", "n_clusters", "r2"]}


CONTROLS = ["log_total_access", "log_pop_density", "log_job_density", "telework_share", "garden_share",
            "flat_share", "private_rent_share", "age20_39_share", "student_share"]
OLD_BANDS = ["50-64", "65-74", "75+"]


def msoa_outcomes():
    """One row per 2021 MSOA: inflow rates per 1,000 by census year and band, plus 50+ (bands summed)."""
    from vm_common import CLEAN
    s = pd.read_csv(CLEAN / "s4_msoa_inflows_on_msoa21.csv")
    s = s[s.age_band.isin(["20-24", "25-34", "20-34"] + OLD_BANDS)]
    old = (s[s.age_band.isin(OLD_BANDS)].groupby(["msoa21cd", "census_year"])
           [["migrants", "residents", "migrants_excl_nua"]].sum(min_count=1))
    nb = s[s.age_band.isin(OLD_BANDS)].groupby(["msoa21cd", "census_year"]).age_band.nunique()
    old = old[nb == 3].reset_index().assign(age_band="50+")
    old["rate_per_1000"] = old.migrants / old.residents * 1000
    old["rate_excl_nua_per_1000"] = old.migrants_excl_nua / old.residents * 1000
    s = pd.concat([s, old], ignore_index=True)
    w = s.pivot_table(index="msoa21cd", columns=["age_band", "census_year"], values="rate_per_1000")
    w.columns = [f"r_{a.replace('-', '').replace('+', 'p')}_{y}" for a, y in w.columns]
    x = s[s.census_year == 2001].pivot_table(index="msoa21cd", columns="age_band", values="rate_excl_nua_per_1000")
    x.columns = [f"rx_{a.replace('-', '').replace('+', 'p')}_2001" for a in x.columns]
    o = w.join(x).reset_index()
    for a in ["2024", "2534", "2034", "50p"]:
        o[f"dy_{a}"] = o[f"r_{a}_2021"] - o[f"r_{a}_2011"]                    # 2011 to 2021 change
        o[f"pl_{a}"] = o[f"r_{a}_2011"] - o[f"rx_{a}_2001"]                   # placebo, 2001 excl. no usual address
        o[f"pl_incl_{a}"] = o[f"r_{a}_2011"] - o[f"r_{a}_2001"]               # placebo, 2001 incl.
    return o


def msoa_frame(nations=("E",)):
    """Treatment, controls and outcomes for MSOAs in `nations`."""
    from vm_common import DATA
    c = pd.read_csv(DATA / "v3_controls_msoa.csv")
    d = c.merge(msoa_outcomes(), on="msoa21cd", how="left")
    d = d[d.nation.isin(nations)].copy()
    for v in ["fhrs", "osm"]:
        for lk in ["l10", "l15", "l30"]:
            for w in ["main", "yr_jun2021", "reopen"]:
                d[f"T_{w}_{v}_{lk}"] = d[f"vdl_{w}_{v}_{lk}"] / 10
    return d


def drop_singletons(d, cols, fe="lad23cd"):
    x = d.dropna(subset=cols)
    n = x.groupby(fe)[fe].transform("size")
    return x[n > 1]


def est(d, y, treat, controls, label, fe="lad23cd", boot=True, extra=None):
    """One MSOA regression; returns a one-row dict for the treatment coefficient with per-SD scaling."""
    x = drop_singletons(d, [y, treat] + list(controls)) if fe is not None else d.dropna(subset=[y, treat] + list(controls))
    t = ols_fe(x, y, [treat] + list(controls), fe=fe, boot=boot, tested=[treat])
    r = row(t, treat)
    sd10 = x[treat].std()                       # SD of VDL/10 in the estimation sample
    r.update(label=label, outcome=y, treatment=treat, controls="+".join(controls) if controls else "none",
             coef_per_sd=r["coef"] * sd10, ci_lo_per_sd=r["ci_lo"] * sd10, ci_hi_per_sd=r["ci_hi"] * sd10,
             treat_sd_days=sd10 * 10, y_mean=x[y].mean(), y_sd=x[y].std(), **(extra or {}))
    return r


RESULT_COLS = ["label", "outcome", "treatment", "coef", "se", "ci_lo", "ci_hi", "p_cr1", "p_wcb", "coef_per_sd",
               "ci_lo_per_sd", "ci_hi_per_sd", "treat_sd_days", "y_mean", "y_sd", "n_obs", "n_clusters", "r2",
               "controls"]
