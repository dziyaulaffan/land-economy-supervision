"""Pre-period check: is the positive 2015 young-adult coefficient an early-year data issue?

1. Re-estimates the 20-29 event study and both triple differences (yearly and period models) on the sample
   starting in the year to June 2016, and compares them with the 2015-2025 sample.
2. Diagnostics on 2015: release vintage of the source files, London-wide young-adult flows by year, in- and
   out-flow components by amenity tercile, and leave-one-borough-out 2015 coefficients.
Uses the estimators of 96_age_ddd.py.
"""
import importlib.util

import numpy as np
import pandas as pd

from config import CLEAN, OUT, RAW, london_frame
from es_core import rademacher

ES = OUT / "event_study"
_spec = importlib.util.spec_from_file_location("m96", __file__.replace("97_preperiod_check.py", "96_age_ddd.py"))
m96 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m96)


def run_models(d, years, w):
    m96.YEARS = years
    out = []
    t = m96.es_fit(d[(d.group == "age20_29") & d.year_ending_june.isin(years)], w)
    out.append(t.assign(model="20-29 event study"))
    for comp, lab in (("family_0_15_30_49", "DDD vs family proxy"), ("age50plus", "DDD vs 50+")):
        st = d[d.group.isin(["age20_29", comp]) & d.year_ending_june.isin(years)].copy()
        st["Y"] = (st.group == "age20_29").astype(float)
        out.append(m96.ddd_fit(st, w).assign(model=f"{lab}, yearly"))
        out.append(m96.ddd_fit(st, w, period_model=True).assign(model=f"{lab}, periods"))
    return pd.concat(out, ignore_index=True)


def main():
    w = rademacher(m96.B, 32, m96.SEED)
    d = pd.read_csv(CLEAN / "migration_net_by_age_group_extended.csv")
    full = run_models(d, list(range(2015, 2026)), w).assign(sample="2015-2025")
    late = run_models(d, list(range(2016, 2026)), w).assign(sample="2016-2025")
    m96.YEARS = list(range(2015, 2026))
    res = pd.concat([full, late], ignore_index=True).drop(columns=["t_bootcluster"])
    res.to_csv(ES / "preperiod_check.csv", index=False)
    terms = ["2015", "2016", "2017", "2018", "2020", "2021", "2022", "2023", "C", "R", "L", "closure_avg",
             "reopening_minus_closure"]
    piv = res[res.term.isin(terms)].assign(cell=lambda x: x.coef.round(2).astype(str) + " (" +
                                           x.p_wcb.round(3).astype(str) + ")")
    print(piv.pivot_table(index=["model", "term"], columns="sample", values="cell", aggfunc="first").to_string())

    # single-group period decomposition (95_reversal.py model) for every age group, 2015 vs 2016 start
    spec = importlib.util.spec_from_file_location("m95", __file__.replace("97_preperiod_check.py", "95_reversal.py"))
    m95 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m95)
    mig = pd.read_csv(CLEAN / "migration_net_by_age_group.csv")
    bvd = pd.read_csv(CLEAN / "event_study_borough_vars.csv")[["la_code", "D_cont"]].rename(columns={"D_cont": "D"})
    dec = []
    for start in (2015, 2016):
        for g, lab in m95.GROUP_LABELS.items():
            df = mig[(mig.group == g) & (mig.year_ending_june >= start)].merge(bvd, on="la_code")
            df["period"] = df.year_ending_june.astype(str)
            df["y"] = df.net_per1k_group
            df["P"] = "ref"
            for P, yrs in m95.MIG.items():
                df.loc[df.period.isin(yrs), "P"] = P
            t = m95.borough_fit(df, "P", w)
            dec.append(t.assign(outcome=lab, sample=f"{start}-2025"))
    dec = pd.concat(dec, ignore_index=True).drop(columns=["t_bootcluster"])
    dec.to_csv(ES / "preperiod_check_decomposition.csv", index=False)
    print(dec.assign(cell=dec.coef.round(2).astype(str) + " (" + dec.p_wcb.round(3).astype(str) + ")")
          .pivot_table(index=["outcome", "name"], columns="sample", values="cell", aggfunc="first").to_string())

    # every migration model cited in the report, on the 2016-2025 sample (age-group event studies, student and
    # hospitality variants, triple differences with the hospitality control)
    yrs = list(range(2016, 2026))
    m96.YEARS = yrs
    ext = d[d.year_ending_june.isin(yrs)]
    allg = mig[mig.year_ending_june.isin(yrs)].merge(bvd, on="la_code").rename(columns={"net_per1k_group": "y"})
    ctl = pd.read_csv(CLEAN / "borough_student_hospitality_2011.csv")
    top5 = ctl.nlargest(5, "student_share").la_code.tolist()
    rep = []
    for g in ["all", "age20_29", "age30_39", "family_0_15_30_49", "age50plus"]:
        rep.append(m96.es_fit(allg[allg.group == g], w).assign(analysis="event study", group=g, control="none",
                                                              sample="32 boroughs"))
    for g in ["age20_29", "age20_24", "age25_29"]:
        base = ext[ext.group == g]
        rep.append(m96.es_fit(base, w, ("X_student_share",)).assign(analysis="event study", group=g,
                                                                    control="student share", sample="32 boroughs"))
        rest = base[~base.la_code.isin(top5)]
        rep.append(m96.es_fit(rest, rademacher(m96.B, rest.la_code.nunique(), m96.SEED)).assign(
            analysis="event study", group=g, control="none", sample="drop top-5 student boroughs"))
        if g != "age20_29":
            rep.append(m96.es_fit(base, w).assign(analysis="event study", group=g, control="none", sample="32 boroughs"))
    rep.append(m96.es_fit(ext[ext.group == "age20_29"], w, ("X_hosp_share_I_RSTU",)).assign(
        analysis="event study", group="age20_29", control="hospitality I+RSTU", sample="32 boroughs"))
    for comp in ["family_0_15_30_49", "age50plus"]:
        st = ext[ext.group.isin(["age20_29", comp])].copy()
        st["Y"] = (st.group == "age20_29").astype(float)
        for c, cl in (((), "none"), (("X_hosp_share_I_RSTU",), "hospitality I+RSTU"),
                      (("X_student_share",), "student share")):
            rep.append(m96.ddd_fit(st, w, c).assign(analysis="triple difference", group=comp, control=cl,
                                                    sample="32 boroughs"))
        rest = st[~st.la_code.isin(top5)]
        rep.append(m96.ddd_fit(rest, rademacher(m96.B, rest.la_code.nunique(), m96.SEED)).assign(
            analysis="triple difference", group=comp, control="none", sample="drop top-5 student boroughs"))
    rep = pd.concat(rep, ignore_index=True).drop(columns=["t_bootcluster"])
    rep.to_csv(ES / "report_migration_2016.csv", index=False)
    m96.YEARS = list(range(2015, 2026))

    # diagnostics
    rows = []
    # (a) source vintage: sheet names and cover text of the 2015 and 2016 workbooks are recorded in the notes
    # (b) London-wide young-adult flows by year (all 32 boroughs, per 1,000 group residents)
    y = d[d.group == "age20_29"].groupby("year_ending_june").agg(net=("net_moves", "sum"), pop=("pop_mid2019", "sum"))
    y["net_per1k"] = y.net / y["pop"] * 1000
    print("\nLondon-wide 20-29 net moves with rest of UK per 1,000:\n", y.net_per1k.round(2).to_string())
    # (c) in and out components by amenity tercile of the borough (within-zone terciles from 80)
    m = pd.concat([pd.read_parquet(f) for f in sorted((RAW / "ons_internal_migration")
                                                      .glob("detailedestimates*.london.parquet"))])
    from config import LONDON
    gla = set(LONDON)
    a = m[m.age.between(20, 29)]
    inn = a[a.inla.isin(gla) & ~a.outla.isin(gla)].groupby(["inla", "year_ending_june"]).moves.sum().rename("in_")
    out = a[a.outla.isin(gla) & ~a.inla.isin(gla)].groupby(["outla", "year_ending_june"]).moves.sum().rename("out_")
    io = pd.concat([inn.rename_axis(["la_code", "year"]), out.rename_axis(["la_code", "year"])], axis=1).reset_index()
    bv = pd.read_csv(CLEAN / "event_study_borough_vars.csv")[["la_code", "D_cont", "per1k_IR"]]
    io = io.merge(bv, on="la_code")
    io["amenity_half"] = np.where(io.D_cont > io.D_cont.median(), "high", "low")
    comp = io.groupby(["amenity_half", "year"])[["in_", "out_"]].sum().round(0)
    print("\n20-29 in- and out-moves with rest of UK, boroughs above/below median amenity:\n", comp.to_string())
    comp.to_csv(ES / "preperiod_2015_components.csv")
    # (d) leave-one-borough-out 2015 coefficient, 20-29 event study, 2015-2025
    m96.YEARS = list(range(2015, 2026))
    yg = d[d.group == "age20_29"]
    names = dict(zip(london_frame().la_code, london_frame().la_name))
    loo = []
    for b in sorted(yg.la_code.unique()):
        t = m96.es_fit(yg[yg.la_code != b], rademacher(199, 31, m96.SEED))
        loo.append((names[b], t.set_index("term").loc["2015", "coef"]))
    loo = pd.DataFrame(loo, columns=["dropped_borough", "coef_2015"]).sort_values("coef_2015")
    loo.to_csv(ES / "preperiod_2015_leave_one_out.csv", index=False)
    print("\nLeave-one-borough-out 2015 coefficient (20-29):\n", loo.head(3).to_string(index=False), "\n...\n",
          loo.tail(3).to_string(index=False))


if __name__ == "__main__":
    main()
