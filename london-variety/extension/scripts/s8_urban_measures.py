"""Departure 8 (decided after seeing the registered results): urban amenity measures.

Step 1. Three LA measures, 2023 LADs:
  (a) food and drink plus arts and leisure: Business Counts 2019 local units in SIC divisions 56 and 90-93
      (accommodation, 55, excluded) per 1,000 mid-2019 residents;
  (b) the same units per square kilometre of land (area = Census 2021 usual residents / TS006 population density,
      summed over 2021 MSOAs, which nest in 2023 LADs);
  (c) the Census-2021-population-weighted mean over the LAD's 2021 MSOAs of the FHRS access index, lambda = 1.5 km
      (restaurants/cafes + pubs/bars/clubs + takeaways, point-based).
  Each enters as the log, standardised over the 316 LADs (City of London and Isles of Scilly excluded).
Step 2. Headline specification (f) of the plan (teleworkability and garden x young x year, region x young x year)
  with each measure in place of D; ages 20-29 and 25-29 against the family proxy; all 316 and the 284 outside
  London; WCR bootstrap clustered by LA (B = 9,999). Leave-one-out of the 2020 coefficient for (c) outside London.
"""
import zipfile

import numpy as np
import pandas as pd

from e_core import B, SEED, cell, ddd_diff, rademacher
from ext_config import CLEAN, RAW
import s2_national_ddd as s2

DROP = {"E09000001", "E06000053"}
HEAD = ("X_telework", "X_garden")
KEYS = ["2020", "2021", "2022", "2022_minus_2020", "X_garden:2020"]
YOUNG = {"age20_29": "20-29", "age25_29": "25-29"}
MEAS = {"M_a": "(a) food, drink, arts and leisure per 1,000", "M_b": "(b) same units per km2",
        "M_c": "(c) pop-weighted FHRS access (1.5 km)"}


def z(v):
    return (v - v.mean()) / v.std()


def measures():
    c = pd.read_csv(CLEAN / "b3_la_crosssection.csv")
    c["units_FA"] = c[["units_div56", "units_div90", "units_div91", "units_div92", "units_div93"]].sum(axis=1)
    msoa = pd.read_csv(CLEAN / "s1_controls_msoa21.csv")[["msoa21cd", "lad23cd", "pop_2021", "telework_share",
                                                         "garden_share"]]
    with zipfile.ZipFile(RAW / "census2021_ts006" / "census2021-ts006.zip") as zf:
        dens = pd.read_csv(zf.open("census2021-ts006-msoa.csv"))
    dens = dens.rename(columns={"geography code": "msoa21cd",
                                "Population Density: Persons per square kilometre; measures: Value": "density"})
    msoa = msoa.merge(dens[["msoa21cd", "density"]], on="msoa21cd")
    msoa["area_km2"] = msoa.pop_2021 / msoa.density
    acc = pd.read_csv(CLEAN / "msoa21_amenity_access_ew.csv")
    acc["acc"] = acc[["access_pt_l15_fhrs_restaurant_cafe", "access_pt_l15_fhrs_pub_bar_club",
                      "access_pt_l15_fhrs_takeaway"]].sum(axis=1)
    msoa = msoa.merge(acc[["msoa21cd", "acc"]], on="msoa21cd")
    la = msoa.groupby("lad23cd").apply(lambda g: pd.Series({
        "area_km2": g.area_km2.sum(), "acc_popw": np.average(g.acc, weights=g.pop_2021),
        "pop_2021": g.pop_2021.sum()}), include_groups=False).reset_index().rename(columns={"lad23cd": "la_code"})
    c = c.merge(la, on="la_code")
    c["per1k_FA"] = c.units_FA / c.pop_mid2019 * 1000
    c["perkm2_FA"] = c.units_FA / c.area_km2
    c = c[~c.la_code.isin(DROP)].copy()
    c["M_a"] = z(np.log(c.per1k_FA))
    c["M_b"] = z(np.log(c.perkm2_FA))
    c["M_c"] = z(np.log(c.acc_popw))
    ctl = pd.read_csv(CLEAN / "s1_controls_la2023.csv")[["la_code", "telework_share", "garden_share"]]
    return c.drop(columns=["garden_share"]).merge(ctl, on="la_code")  # garden from S1, as in the models


def main():
    c = measures()
    L = ["### Step 1. Urban amenity measures (316 LADs)\n",
         f"Land area check: total {c.area_km2.sum():,.0f} km2 (England and Wales land area is about 151,000 km2).\n",
         "| Measure | Corr. with registered D | Corr. with teleworkability | Corr. with garden access |",
         "|---|---|---|---|"]
    for m, lab in MEAS.items():
        L.append(f"| {lab} | {np.corrcoef(c[m], c.z_log_per1k_IR)[0, 1]:.3f} | "
                 f"{np.corrcoef(c[m], c.telework_share)[0, 1]:.3f} | {np.corrcoef(c[m], c.garden_share)[0, 1]:.3f} |")
    L.append(f"| registered D (I+R per 1,000) | 1 | {np.corrcoef(c.z_log_per1k_IR, c.telework_share)[0, 1]:.3f} | "
             f"{np.corrcoef(c.z_log_per1k_IR, c.garden_share)[0, 1]:.3f} |")
    L.append(f"\nCorrelations among the new measures: a-b {np.corrcoef(c.M_a, c.M_b)[0, 1]:.3f}, "
             f"a-c {np.corrcoef(c.M_a, c.M_c)[0, 1]:.3f}, b-c {np.corrcoef(c.M_b, c.M_c)[0, 1]:.3f}.\n")
    for m, raw, unit in (("M_a", "per1k_FA", "units per 1,000"), ("M_b", "perkm2_FA", "units per km2"),
                         ("M_c", "acc_popw", "access index")):
        top = c.nlargest(20, m)
        L.append(f"Top 20 on {MEAS[m]} ({unit}): " + "; ".join(f"{r.la_name} {getattr(r, raw):,.1f}"
                                                                for r in top.itertuples()) + ".\n")
    c.to_csv(CLEAN / "s8_urban_measures_la.csv", index=False)

    p = s2.panel("internal").merge(c[["la_code", "la_name", "M_a", "M_b", "M_c"]], on="la_code")
    comp = "family_0_15_30_49"
    out = []
    L.append("### Step 2. Headline (f) with each urban measure in place of D, against the family proxy (WCB p)\n")
    L.append("| Measure | Sample | Young | 2020 | 2021 | 2022 | 2022 - 2020 | Garden x 2020 | LAs |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for m, lab in MEAS.items():
        for sample in ("all 316", "outside London"):
            q = p if sample == "all 316" else p[~p.london.astype(bool)]
            w = rademacher(B, q.la_code.nunique(), SEED)
            for young, yl in YOUNG.items():
                q = q.assign(dy=q[young] - q[comp])
                t = ddd_diff(q, HEAD, True, w=w, treat=m)
                out.append(t.assign(measure=m, sample=sample, young=young))
                L.append(f"| {lab} | {sample} | {yl} | " + " | ".join(cell(t, k) for k in KEYS)
                         + f" | {int(t.n_clusters.iloc[0])} |")
                print(L[-1], flush=True)

    q = p[~p.london.astype(bool)].assign(dy=lambda x: x.age20_29 - x[comp])
    full = ddd_diff(q, HEAD, True, treat="M_c", boot=False).set_index("term").loc["2020", "coef"]
    loo = []
    for b in sorted(q.la_code.unique()):
        e = ddd_diff(q[q.la_code != b], HEAD, True, treat="M_c", boot=False).set_index("term").loc["2020", "coef"]
        loo.append((b, e, full - e))
    loo = pd.DataFrame(loo, columns=["la_code", "coef_2020_without", "contribution"]).merge(
        c[["la_code", "la_name", "region", "M_c", "acc_popw"]], on="la_code")
    loo = loo.reindex(loo.contribution.abs().sort_values(ascending=False).index)
    loo.to_csv(CLEAN / "s8_loo_2020_measure_c_outside_london.csv", index=False)
    L.append(f"\n### Leave-one-out, 2020 coefficient for measure (c) outside London (20-29 vs family proxy)\n")
    L.append(f"Full estimate {full:.3f}; range {loo.coef_2020_without.min():.3f} to {loo.coef_2020_without.max():.3f} "
             f"over {len(loo)} LADs. Ten largest absolute contributions:\n")
    L.append("| LAD | Region | Measure (c), z | 2020 without it | Contribution |")
    L.append("|---|---|---|---|---|")
    for r in loo.head(10).itertuples():
        L.append(f"| {r.la_name} | {r.region} | {r.M_c:.2f} | {r.coef_2020_without:.3f} | {r.contribution:+.3f} |")
    res = pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore")
    res.to_csv(CLEAN / "s8_urban_ddd.csv", index=False)
    (CLEAN / "s8_urban_measures.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
