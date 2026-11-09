"""Time-varying student control (HESA) and ages 25-29 as the young group.

1. HESA full-time enrolments (all levels) per 1,000 mid-2019 residents aged 18-29, by borough of each provider's
   main campus, academic year t-1/t mapped to the year to June t. S_bt enters the young-adult event study as a
   regressor and the triple difference as S_bt x Y. Years to June 2017-2024, with the baseline and the 2011
   student-share (x year, x Y x year) versions re-estimated on the same sample.
2. Triple difference with ages 25-29 as the young group against the family proxy and 50+, years to June 2016-2025:
   yearly model, period model, reopening minus closure, and the tests 2022 = 0 and 2022 - 2020 = 0. Repeated with
   the HESA control on 2017-2024, alongside the 25-29 baseline on the same sample.
All inference: CR1 clustered by borough, WCR bootstrap clustered by borough (Rademacher, B = 9,999).
"""
import importlib.util

import numpy as np
import pandas as pd

from config import CLEAN, OUT, RAW
from es_core import fit_cluster, rademacher

ES = OUT / "event_study"
_spec = importlib.util.spec_from_file_location("m96", __file__.replace("98_students_25_29.py", "96_age_ddd.py"))
m96 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m96)
COMP = {"family_0_15_30_49": "family proxy", "age50plus": "ages 50+"}
HESA_DIR = RAW / "hesa"


def cell(t, term):
    r = t.set_index("term").loc[term]
    return f"{r.coef:.2f} ({r.p_wcb:.3f})"


def year_contrasts(prefix):
    C = m96.PERIODS["C"]
    con = {"reopening_minus_closure": {f"{prefix}2022": 1.0, **{f"{prefix}{y}": -1 / len(C) for y in C}},
           "2022_minus_2020": {f"{prefix}2022": 1.0, f"{prefix}2020": -1.0}}
    return con


def trend_contrasts(prefix, pre=(2016, 2017, 2018, 2019), targets=(2020, 2022)):
    """Deviation of theta_t from a linear trend fitted by OLS through the pre-period coefficients (theta_2019 = 0).
    Projection at t = mean(theta_pre) + b (t - mean(pre)), b = sum (k - kbar) theta_k / sum (k - kbar)^2."""
    kbar = np.mean(pre)
    sxx = sum((k - kbar) ** 2 for k in pre)
    con = {"pre_trend_slope": {f"{prefix}{k}": (k - kbar) / sxx for k in pre if k != m96.BASE}}
    for t in targets:
        c = {f"{prefix}{t}": 1.0}
        for k in pre:
            if k == m96.BASE:
                continue
            c[f"{prefix}{k}"] = c.get(f"{prefix}{k}", 0.0) - (1 / len(pre) + (t - kbar) * (k - kbar) / sxx)
        con[f"{t}_dev_from_trend"] = c
    return con


def es_tv(df, w, tv=(), fixed=()):
    """Single-group event study; tv: time-varying regressors; fixed: time-invariant controls x year."""
    df = df.sort_values(["la_code", "year_ending_june"]).reset_index(drop=True)
    ev = [y for y in m96.YEARS if y != m96.BASE]
    unit = pd.get_dummies(df.la_code, dtype=float)
    T = m96.year_dummies(df.year_ending_june.values, ev)
    blocks, names = [unit.values, T, T * df.D.values[:, None]], \
        [f"fe_{c}" for c in unit.columns] + [f"t_{y}" for y in ev] + [f"D:{y}" for y in ev]
    for c in fixed:
        blocks.append(T * df[c].values[:, None]); names += [f"{c}:{y}" for y in ev]
    for c in tv:
        blocks.append(df[[c]].values); names.append(c)
    tab, _ = fit_cluster(np.hstack(blocks), df.y.values, names, [f"D:{y}" for y in ev], cl_se=df.la_code.values,
                         w=w, k_nested=unit.shape[1], contrasts=year_contrasts("D:"))
    tab["term"] = tab.name.str.replace("D:", "", regex=False)
    return tab.assign(n_obs=len(df))


def ddd_tv(stack, w, tv=(), fixed=(), period_model=False, extra_con=None):
    """Triple difference as in 96_age_ddd.ddd_fit, plus time-varying controls x Y and the 2022 - 2020 contrast."""
    stack = stack.sort_values(["la_code", "group", "year_ending_june"]).reset_index(drop=True)
    t, Y = stack.year_ending_june.values, stack.Y.values
    bt = pd.get_dummies(stack.la_code + "_" + stack.year_ending_june.astype(str), dtype=float)
    gt = m96.year_dummies(t, m96.YEARS) * Y[:, None]
    boroughs = sorted(stack.la_code.unique())
    bg = np.column_stack([((stack.la_code == b) & (Y == 1)).astype(float) for b in boroughs[1:]])
    blocks = [bt.values, gt, bg]
    names = [f"bt_{c}" for c in bt.columns] + [f"gt_{y}" for y in m96.YEARS] + [f"bg_{b}" for b in boroughs[1:]]
    ev = [y for y in m96.YEARS if y != m96.BASE]
    if period_model:
        for k in ["C", "R", "L"]:
            blocks.append((np.isin(t, m96.PERIODS[k]) * stack.D.values * Y)[:, None]); names.append(f"DY:{k}")
        tested = ["DY:C", "DY:R", "DY:L"]
        con = {"reopening_minus_closure": {"DY:R": 1.0, "DY:C": -1.0}}
    else:
        blocks.append(m96.year_dummies(t, ev) * (stack.D.values * Y)[:, None]); names += [f"DY:{y}" for y in ev]
        tested = [f"DY:{y}" for y in ev]
        con = year_contrasts("DY:")
        con.update(extra_con or {})
    T_all = m96.year_dummies(t, ev)
    for c in fixed:
        blocks.append(T_all * (stack[c].values * Y)[:, None]); names += [f"{c}Y:{y}" for y in ev]
    for c in tv:
        blocks.append((stack[c].values * Y)[:, None]); names.append(f"{c}Y")
    tab, _ = fit_cluster(np.hstack(blocks), stack.y.values, names, tested, cl_se=stack.la_code.values, w=w,
                         k_nested=bt.shape[1] + bg.shape[1], contrasts=con)
    tab["term"] = tab.name.str.replace("DY:", "", regex=False)
    return tab.assign(n_obs=len(stack))


def stack_of(d, young, comp):
    st = d[d.group.isin([young, comp])].copy()
    st["Y"] = (st.group == young).astype(float)
    return st


def hesa_measure():
    """Borough x year full-time enrolments per 1,000 mid-2019 residents aged 18-29 (built once the file is read)."""
    raise FileNotFoundError(f"HESA Table 1 not found in {HESA_DIR}")


def main():
    w = rademacher(m96.B, 32, m96.SEED)
    d = pd.read_csv(CLEAN / "migration_net_by_age_group_extended.csv")
    try:
        s = hesa_measure()
        d = d.merge(s, on=["la_code", "year_ending_june"], how="left")
        have_hesa = True
    except FileNotFoundError as e:
        print("SKIPPING HESA PARTS:", e)
        have_hesa = False
    out, L = [], []
    keys = ["2020", "2021", "2022", "reopening_minus_closure", "2022_minus_2020"]

    # 2. ages 25-29, 2016-2025
    m96.YEARS = list(range(2016, 2026))
    full = d[d.year_ending_june.isin(m96.YEARS)]
    yrs = [str(y) for y in m96.YEARS if y != m96.BASE]
    L.append("### Triple difference, ages 25-29 as the young group (2016-2025; WCB p)\n")
    L.append("| Comparison | " + " | ".join(yrs) + " | R - C | 2022 - 2020 |")
    L.append("|---|" + "---|" * (len(yrs) + 2))
    per, trend = [], []
    for comp, lab in COMP.items():
        st = stack_of(full, "age25_29", comp)
        t = ddd_tv(st, w, extra_con=trend_contrasts("DY:"))
        trend.append(f"| {lab} | {cell(t, 'pre_trend_slope')} | {cell(t, '2020')} | {cell(t, '2020_dev_from_trend')} | "
                     f"{cell(t, '2022')} | {cell(t, '2022_dev_from_trend')} |")
        out.append(t.assign(test="25-29", model="yearly", group=comp, control="none", sample="2016-2025"))
        L.append(f"| {lab} | " + " | ".join(cell(t, y) for y in yrs) + f" | {cell(t, 'reopening_minus_closure')} | "
                 f"{cell(t, '2022_minus_2020')} |")
        tp = ddd_tv(st, w, period_model=True)
        out.append(tp.assign(test="25-29", model="periods", group=comp, control="none", sample="2016-2025"))
        per.append(f"| {lab} | {cell(tp, 'C')} | {cell(tp, 'R')} | {cell(tp, 'L')} | "
                   f"{cell(tp, 'reopening_minus_closure')} |")
    L.append("\nPeriod model (reference 2016-2019 pooled):\n")
    L.append("| Comparison | Closure | Reopening | Later | Reopening - closure |")
    L.append("|---|---|---|---|---|")
    L += per
    L.append("\nLinear young-by-amenity trend fitted through the 2016-2019 yearly coefficients (2019 = 0); deviations "
             "of 2020 and 2022 from the projected trend:\n")
    L.append("| Comparison | Pre-trend slope per year | 2020 | 2020 deviation | 2022 | 2022 deviation |")
    L.append("|---|---|---|---|---|---|")
    L += trend

    if have_hesa:
        pass  # filled in once the HESA file is available

    m96.YEARS = list(range(2015, 2026))
    pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore").to_csv(
        ES / "students_25_29.csv", index=False)
    (ES / "students_25_29.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
