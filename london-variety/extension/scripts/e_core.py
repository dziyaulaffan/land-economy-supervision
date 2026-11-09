"""Estimators for the national extension, built on the pilot's es_core.fit_cluster (CR1 + WCR bootstrap).

ddd_diff: the triple difference in differenced form. With two groups per LA-year, LA-by-year effects make the
stacked model y_bgt = a_bt + c_gt + e_bg + theta_k D_b Y_g 1[t=k] + ... numerically equivalent to regressing
dy_bt = y_young - y_comp on LA effects, year (or region-by-year) effects and D_b x year. Controls enter as
X_b x year (the differenced form of X_b x Y x year). Verified against the pilot's London results in s2.
"""
import numpy as np
import pandas as pd

from ext_config import PROJECT  # noqa: F401  (puts the pilot's scripts on sys.path)
from es_core import fit_cluster, rademacher  # noqa: E402

B, SEED, BASE = 9999, 20261028, 2019
PERIODS = {"C": [2020, 2021], "R": [2022]}


def year_dummies(t, years):
    return np.column_stack([(t == y).astype(float) for y in years])


def ddd_diff(df, controls=(), region_year=False, years=range(2016, 2026), w=None, extra_con=None, treat="D",
             boot=True):
    """df: one row per LA-year with la_code, region, year_ending_june, dy, treat column and controls."""
    years = list(years)
    df = df[df.year_ending_june.isin(years)].sort_values(["la_code", "year_ending_june"]).reset_index(drop=True)
    t = df.year_ending_june.values
    ev = [y for y in years if y != BASE]
    unit = pd.get_dummies(df.la_code, dtype=float)
    blocks, names = [unit.values], [f"fe_{c}" for c in unit.columns]
    if region_year:
        ry = pd.get_dummies(df.region + "_" + df.year_ending_june.astype(str), dtype=float)
        base_cols = [c for c in ry.columns if c.endswith(f"_{BASE}")]
        ry = ry.drop(columns=base_cols)              # region levels absorbed by LA effects
        blocks.append(ry.values); names += [f"ry_{c}" for c in ry.columns]
    else:
        blocks.append(year_dummies(t, ev)); names += [f"t_{y}" for y in ev]
    T = year_dummies(t, ev)
    blocks.append(T * df[treat].values[:, None]); names += [f"D:{y}" for y in ev]
    for c in controls:
        blocks.append(T * df[c].values[:, None]); names += [f"{c}:{y}" for y in ev]
    X = np.hstack(blocks)
    con = {"2022_minus_2020": {"D:2022": 1.0, "D:2020": -1.0}}
    if 2018 in years:
        con["pre_avg_2016_2018"] = {f"D:{y}": 1 / 3 for y in (2016, 2017, 2018)}
    con.update(extra_con or {})
    tested = [f"D:{y}" for y in ev] + [f"{c}:2020" for c in controls] + [f"{c}:2022" for c in controls]
    if w is None and boot:
        w = rademacher(B, df.la_code.nunique(), SEED)
    if not boot:
        w = None                                      # point estimates and CR1 only (leave-one-out loops)
    tab, _ = fit_cluster(X, df.dy.values, names, tested, cl_se=df.la_code.values, w=w, k_nested=unit.shape[1],
                         contrasts=con)
    tab["term"] = tab.name.str.replace("D:", "", regex=False)
    return tab.assign(n_obs=len(df), n_clusters=df.la_code.nunique())


def cross_section(df, y, regressors, fe=None, w=None, contrasts=None):
    """OLS of y on regressors (+ fixed effects in `fe`), each unit its own cluster (HC1-type CR1 and WCR)."""
    df = df.dropna(subset=[y] + list(regressors)).reset_index(drop=True)
    blocks, names = [np.ones((len(df), 1))], ["const"]
    k_nested = 0
    if fe is not None:
        d = pd.get_dummies(df[fe], dtype=float, drop_first=True)
        blocks.append(d.values); names += [f"fe_{c}" for c in d.columns]
    for r in regressors:
        blocks.append(df[[r]].values); names.append(r)
    X = np.hstack(blocks)
    cl = df[df.attrs.get("cluster", "la_code")].values if "la_code" in df else np.arange(len(df))
    if w is None:
        w = rademacher(B, len(np.unique(cl)), SEED)
    tab, _ = fit_cluster(X, df[y].values, names, list(regressors), cl_se=cl, w=w, k_nested=k_nested,
                         contrasts=contrasts)
    return tab.assign(n_obs=len(df), n_clusters=len(np.unique(cl)))


def cell(t, term, d=2):
    r = t.set_index("term" if "term" in t else "name").loc[term]
    return f"{r.coef:.{d}f} ({r.p_wcb:.3f})"
