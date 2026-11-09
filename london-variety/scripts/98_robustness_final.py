"""Final robustness round for the triple difference (years to June 2016-2025, 2019 omitted).

A1. Teleworkability and garden access (2011/2020 borough shares, standardised as in 70_controls.py), each x young x
    year, alone and together, for ages 20-29 and 25-29 against the family proxy and 50+.
A2. The 2022 minus 2020 contrast for every existing triple-difference specification: 20-29 with no control, the
    hospitality controls, the 2011 student share, the top-5 student boroughs dropped and the 2019Q4-2021Q4 rent
    change; 25-29 with no control; within-London 20-29.
All inference: CR1 clustered by borough, WCR bootstrap clustered by borough (Rademacher, B = 9,999).
"""
import importlib.util

import numpy as np
import pandas as pd

from config import CLEAN, OUT
from es_core import rademacher

ES = OUT / "event_study"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, __file__.replace("98_robustness_final.py", file))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


m98s = load("m98s", "98_students_25_29.py")
m98r = load("m98r", "98_rent_tests.py")
m96 = m98s.m96
COMP = {"family_0_15_30_49": "family proxy", "age50plus": "ages 50+"}
YOUNG = {"age20_29": "20-29", "age25_29": "25-29"}
KEYS = ["2020", "2021", "2022", "reopening_minus_closure", "2022_minus_2020"]


def cell(t, term):
    r = t.set_index("term").loc[term]
    return f"{r.coef:.2f} ({r.p_wcb:.3f})"


def main():
    w = rademacher(m96.B, 32, m96.SEED)
    d = pd.read_csv(CLEAN / "migration_net_by_age_group_extended.csv")
    bv = pd.read_csv(CLEAN / "event_study_borough_vars.csv")[["la_code", "X_telework", "X_garden", "telework_share",
                                                              "garden_share"]]
    d = d.merge(bv, on="la_code").merge(m98r.rent_change_1921(), on="la_code")
    m96.YEARS = list(range(2016, 2026))
    d = d[d.year_ending_june.isin(m96.YEARS)]
    b = d.drop_duplicates("la_code")
    corr = {v: np.corrcoef(b.D, b[v])[0, 1] for v in ["telework_share", "garden_share"]}
    out, L = [], []

    # A1
    L.append("### A1. Teleworkability and garden access x young x year (2016-2025; WCB p)\n")
    L.append(f"Correlation with standardised log amenity density across the 32 boroughs: teleworkability "
             f"{corr['telework_share']:.3f}, garden access {corr['garden_share']:.3f}.\n")
    L.append("| Young | Comparison | Control | 2020 | 2021 | 2022 | R - C | 2022 - 2020 |")
    L.append("|---|---|---|---|---|---|---|---|")
    ctrls = {"none": (), "teleworkability": ("X_telework",), "garden access": ("X_garden",),
             "both": ("X_telework", "X_garden")}
    for young, yl in YOUNG.items():
        for comp, cl in COMP.items():
            st = m98s.stack_of(d, young, comp)
            for lab, c in ctrls.items():
                t = m98s.ddd_tv(st, w, fixed=c)
                out.append(t.assign(part="A1", young=young, group=comp, control=lab, sample="32 boroughs"))
                L.append(f"| {yl} | {cl} | {lab} | " + " | ".join(cell(t, k) for k in KEYS) + " |")

    # A2
    ctl = pd.read_csv(CLEAN / "borough_student_hospitality_2011.csv")
    top5 = ctl.nlargest(5, "student_share").la_code.tolist()
    L.append("\n### A2. 2022 minus 2020 for every triple-difference specification (2016-2025; WCB p)\n")
    L.append("| Young | Comparison | Specification | 2020 | 2022 | 2022 - 2020 | Clusters |")
    L.append("|---|---|---|---|---|---|---|")
    specs = [("age20_29", "none", (), None), ("age20_29", "hospitality I+RSTU", ("X_hosp_share_I_RSTU",), None),
             ("age20_29", "hospitality I only", ("X_hosp_share_I",), None),
             ("age20_29", "2011 student share", ("X_student_share",), None),
             ("age20_29", "drop top-5 student boroughs", (), top5),
             ("age20_29", "rent change 2019Q4-2021Q4", ("X_rent_chg_1921",), None),
             ("age25_29", "none", (), None)]
    for young, lab, c, drop in specs:
        for comp, cl in COMP.items():
            st = m98s.stack_of(d, young, comp)
            ww = w
            if drop:
                st = st[~st.la_code.isin(drop)]
                ww = rademacher(m96.B, st.la_code.nunique(), m96.SEED)
            t = m98s.ddd_tv(st, ww, fixed=c)
            out.append(t.assign(part="A2", young=young, group=comp, control=lab,
                                sample="drop top-5" if drop else "32 boroughs"))
            L.append(f"| {YOUNG[young]} | {cl} | {lab} | {cell(t, '2020')} | {cell(t, '2022')} | "
                     f"{cell(t, '2022_minus_2020')} | {st.la_code.nunique()} |")
    wl = pd.read_csv(CLEAN / "migration_within_london_by_age_group.csv")
    wl = wl[wl.year_ending_june.isin(m96.YEARS)]
    for comp, cl in COMP.items():
        t = m98s.ddd_tv(m98s.stack_of(wl, "age20_29", comp), w)
        out.append(t.assign(part="A2", young="age20_29", group=comp, control="within-London outcome",
                            sample="32 boroughs"))
        L.append(f"| 20-29 | {cl} | within-London moves | {cell(t, '2020')} | {cell(t, '2022')} | "
                 f"{cell(t, '2022_minus_2020')} | 32 |")
    m96.YEARS = list(range(2015, 2026))

    pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore").to_csv(
        ES / "robustness_final.csv", index=False)
    (ES / "robustness_final.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
