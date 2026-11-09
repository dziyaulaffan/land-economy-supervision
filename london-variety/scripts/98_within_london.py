"""Within-London moves: net migration of each borough with the other 31 boroughs (City of London excluded).

Outcome: net moves with the other 31 boroughs per 1,000 mid-2019 residents of the age group, years to June
2016-2025. Event study (20-29, family proxy, 50+) and triple difference of 20-29 against the family proxy and 50+,
with D = standardised log borough amenity density, as in 96_age_ddd.py. Also gross 20-29 flows between boroughs
above and below median amenity density, year to June 2020 against the 2016-2019 average.
All inference: CR1 clustered by borough, WCR bootstrap clustered by borough (Rademacher, B = 9,999).
"""
import importlib.util

import numpy as np
import pandas as pd

from config import CLEAN, OUT, RAW, london_frame
from es_core import rademacher

ES = OUT / "event_study"
_spec = importlib.util.spec_from_file_location("m96", __file__.replace("98_within_london.py", "96_age_ddd.py"))
m96 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m96)
GROUPS = {"age20_29": "20-29", "family_0_15_30_49": "family proxy", "age50plus": "ages 50+"}


def cell(t, term):
    r = t.set_index("term").loc[term]
    return f"{r.coef:.2f} ({r.p_wcb:.3f})"


def within_panel():
    b32 = set(london_frame().la_code)
    m = pd.concat([pd.read_parquet(f) for f in sorted((RAW / "ons_internal_migration")
                                                      .glob("detailedestimates*.london.parquet"))])
    w = m[m.inla.isin(b32) & m.outla.isin(b32) & (m.inla != m.outla)]
    pop = pd.read_csv(RAW / "nomis" / "mye_population_mid2019_single_age_london.csv")
    pop["age"] = pop.C_AGE - 101
    rows = []
    for g in GROUPS:
        x = w[m96.in_group(w.age, g)]
        inn = x.groupby(["inla", "year_ending_june"]).moves.sum().rename_axis(["la_code", "year_ending_june"])
        out = x.groupby(["outla", "year_ending_june"]).moves.sum().rename_axis(["la_code", "year_ending_june"])
        n = inn.sub(out, fill_value=0).rename("net_moves").reset_index()
        p = pop[m96.in_group(pop.age, g)].groupby("GEOGRAPHY_CODE").OBS_VALUE.sum().rename("pop_mid2019")
        n = n.merge(p, left_on="la_code", right_index=True)
        n["group"] = g
        rows.append(n)
    d = pd.concat(rows, ignore_index=True)
    d["y"] = d.net_moves / d.pop_mid2019 * 1000
    assert d.groupby(["la_code", "group"]).size().eq(11).all() and d.la_code.nunique() == 32
    return d, w


def main():
    w = rademacher(m96.B, 32, m96.SEED)
    d, flows = within_panel()
    bv = pd.read_csv(CLEAN / "event_study_borough_vars.csv")[["la_code", "D_cont"]].rename(columns={"D_cont": "D"})
    d = d.merge(bv, on="la_code")
    d.to_csv(CLEAN / "migration_within_london_by_age_group.csv", index=False)
    m96.YEARS = list(range(2016, 2026))
    d = d[d.year_ending_june.isin(m96.YEARS)]
    out = []
    for g, lab in GROUPS.items():
        out.append(m96.es_fit(d[d.group == g], w).assign(analysis="event study", group=g))
    for comp in ["family_0_15_30_49", "age50plus"]:
        st = d[d.group.isin(["age20_29", comp])].copy()
        st["Y"] = (st.group == "age20_29").astype(float)
        out.append(m96.ddd_fit(st, w).assign(analysis="triple difference", group=comp))
    res = pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"])
    res.to_csv(ES / "within_london.csv", index=False)
    m96.YEARS = list(range(2015, 2026))

    terms = ["2016", "2017", "2018", "2020", "2021", "2022", "2023", "2024", "2025", "reopening_minus_closure"]
    L = ["### Within-London net migration with the other 31 boroughs, per 1,000 group residents per SD of log amenity "
         "density (2016-2025, 2019 omitted; WCB p)\n",
         "| Model | " + " | ".join(terms) + " |", "|---|" + "---|" * len(terms)]
    for (an, g), t in res.groupby(["analysis", "group"], sort=False):
        lab = f"Event study, {GROUPS[g]}" if an == "event study" else f"Triple difference vs {GROUPS[g]}"
        L.append(f"| {lab} | " + " | ".join(cell(t, k) for k in terms) + " |")

    # gross 20-29 flows between amenity halves
    med = bv.D.median()
    hi = set(bv.la_code[bv.D > med])
    x = flows[m96.in_group(flows.age, "age20_29")].copy()
    x["o"] = np.where(x.outla.isin(hi), "high", "low")
    x["i"] = np.where(x.inla.isin(hi), "high", "low")
    gr = x.groupby(["o", "i", "year_ending_june"]).moves.sum().unstack("year_ending_june")
    gr["avg_2016_2019"] = gr[[2016, 2017, 2018, 2019]].mean(axis=1)
    gr["pct_2020_vs_avg"] = (gr[2020] / gr.avg_2016_2019 - 1) * 100
    gr.round(1).to_csv(ES / "within_london_gross_20_29.csv")
    L.append("\n### Gross 20-29 moves between boroughs above (high) and below (low) median amenity density\n")
    L.append("| From | To | 2016-2019 average | 2020 | 2020 vs average (%) | 2021 | 2022 |")
    L.append("|---|---|---|---|---|---|---|")
    for (o, i), r in gr.iterrows():
        L.append(f"| {o} | {i} | {r.avg_2016_2019:,.0f} | {r[2020]:,.0f} | {r.pct_2020_vs_avg:+.1f} | "
                 f"{r[2021]:,.0f} | {r[2022]:,.0f} |")
    net = gr.loc[("high", "low")] - gr.loc[("low", "high")]
    L.append(f"\nNet high-to-low 20-29 moves: 2016-2019 average {net.avg_2016_2019:,.0f}, 2020 {net[2020]:,.0f}, "
             f"2021 {net[2021]:,.0f}, 2022 {net[2022]:,.0f}.")
    (ES / "within_london.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
