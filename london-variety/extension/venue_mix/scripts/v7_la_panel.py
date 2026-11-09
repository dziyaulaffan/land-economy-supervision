"""V7. Local authority panel triple difference and reopening test (plan Sections 4.4-4.5).

Panel: s2_national_ddd.panel() (net internal migration per 1,000 mid-2019 residents, years ending June 2016-2025,
316 LADs). Young 20-29 against the family proxy, differenced form (e_core.ddd_diff), region-by-year effects,
teleworkability x year and garden x year. Treatments (divided by 10):
  D = variety-days lost over the year to June 2021 (LA population-weighted mean of MSOA values, FHRS, 1.5 km)
  R = variety-days lost over 1 April to 31 July 2021 (reopening window, scaled to 365 days)
WCR bootstrap p-values clustered by LA (Rademacher, B = 9,999, seed 20261028).

Output: extension/venue_mix/data/v7_la_panel.csv and .md
"""
import pandas as pd

from vm_common import DATA
from e_core import ddd_diff, rademacher, B, SEED
from s2_national_ddd import panel

CON = {"2022_minus_2021": {"D:2022": 1.0, "D:2021": -1.0}}


def main():
    p = panel("internal")
    t = pd.read_csv(DATA / "v2_treatment_lad.csv")
    t = t.rename(columns={"lad23cd": "la_code"})
    t["T_D"] = t.vdl_yr_jun2021_fhrs_l15 / 10
    t["T_R"] = t.vdl_reopen_fhrs_l15 / 10
    t["T_D_osm"] = t.vdl_yr_jun2021_osm_l15 / 10
    p = p.merge(t[["la_code", "T_D", "T_R", "T_D_osm"]], on="la_code", how="left")
    assert p[["T_D", "T_R"]].notna().all().all() and p.la_code.nunique() == 316
    p = p.assign(dy=p.age20_29 - p.family_0_15_30_49)
    w = rademacher(B, p.la_code.nunique(), SEED)
    ctrl = ("X_telework", "X_garden")
    out = []
    specs = [
        ("D: variety-days lost, year to June 2021", "T_D", ctrl, CON),
        ("R: reopening, share of variety closed Apr-Jul 2021", "T_R", ctrl, CON),
        ("D (OSM version)", "T_D_osm", ctrl, CON),
    ]
    for lab, tr, c, con in specs:
        q = p.assign(D=p[tr])
        r = ddd_diff(q, c, region_year=True, w=w, extra_con=con)
        out.append(r.assign(model=lab, treatment=tr))
        print(lab, flush=True)
        print(r[["term", "coef", "se_cluster", "ci_low", "ci_high", "p_wcb"]].round(3).to_string(index=False), flush=True)
    # joint model: D x year and R x year together (R enters as a control interacted with year)
    q = p.assign(D=p.T_D)
    r = ddd_diff(q, ctrl + ("T_R",), region_year=True, w=w,
                 extra_con={**CON, "R_2022_minus_2021": {"T_R:2022": 1.0, "T_R:2021": -1.0}})
    out.append(r.assign(model="Joint: D and R together", treatment="T_D+T_R"))
    print(r[r.term.str.contains("2021|2022")][["term", "coef", "se_cluster", "p_wcb"]].round(3).to_string(index=False))
    res = pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore")
    res.to_csv(DATA / "v7_la_panel.csv", index=False)
    sd = t.set_index("la_code").loc[p.la_code.unique(), ["T_D", "T_R"]].std() * 10
    L = ["# Step 7 local authority panel (316 LADs; 20-29 minus family proxy; coefficient per 10 variety-days lost)",
         "", f"Treatment SD across LADs: D {sd.T_D:.1f} days, R {sd.T_R:.1f} days.", "",
         "| Model | Term | Coef | 95% CI | p (CR1) | p (WCB) |", "|---|---|---|---|---|---|"]
    for _, x in res.iterrows():
        if x.term in ("2016", "2017", "2018", "2020", "2021", "2022", "2023", "2024", "2025", "2022_minus_2021",
                      "pre_avg_2016_2018", "T_R:2021", "T_R:2022", "R_2022_minus_2021"):
            L.append(f"| {x.model} | {x.term} | {x.coef:.2f} | [{x.ci_low:.2f}, {x.ci_high:.2f}] | "
                     f"{x.p_cluster:.3f} | {x.p_wcb:.3f} |")
    (DATA / "v7_la_panel.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
