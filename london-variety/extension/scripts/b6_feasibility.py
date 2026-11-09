"""B6 feasibility: correlations across LAs between the new amenity measures, Business Counts 2019, the Google
retail-and-recreation fall and the legal hospitality closure intensity. Descriptive only, no regressions.

Sample: 2023 LADs in England and Wales excluding City of London and Isles of Scilly (small populations), with
complete data for each pair. Amenity measures enter as log(1 + units per 1,000 residents); population is Census
2021 usual residents for the new counts (as in la2023_amenity_counts_ew.csv) and mid-2019 for Business Counts.
"""
import numpy as np
import pandas as pd

from ext_config import CLEAN

DROP = {"E09000001", "E06000053"}  # City of London, Isles of Scilly


def main():
    a = pd.read_csv(CLEAN / "la2023_amenity_counts_ew.csv").rename(columns={"lad23cd": "la_code"})
    c = pd.read_csv(CLEAN / "b3_la_crosssection.csv")
    m = pd.read_csv(CLEAN / "b5_closure_intensity_la_quarter.csv")
    r = pd.read_csv(CLEAN / "b4_restrictions_quarterly_lad23.csv").rename(columns={"lad23_code": "la_code"})
    x = c[["la_code", "per1k_IR"]].merge(a, on="la_code")
    x = x[~x.la_code.isin(DROP)].set_index("la_code")
    v = {"Business Counts I+R per 1k (2019)": np.log1p(x.per1k_IR)}
    for col, lab in (("fhrs_restaurant_cafe", "FHRS restaurant/cafe"), ("fhrs_pub_bar_club", "FHRS pub/bar/club"),
                     ("fhrs_takeaway", "FHRS takeaway"), ("osm2019_restaurant_cafe", "OSM 2019 restaurant+cafe"),
                     ("osm2019_pub_bar_club", "OSM 2019 pub+bar+club"), ("osm2019_arts_venue", "OSM 2019 arts venue"),
                     ("osm2019_fitness_centre", "OSM 2019 fitness")):
        v[lab] = np.log1p(x[col] / x.pop_census2021 * 1000)
    mob = m[m.quarter.isin(["2020Q2", "2020Q4", "2021Q1"]) & ~m.low_coverage].pivot(
        index="la_code", columns="quarter", values="closure_rr_mean")
    res = r.pivot(index="la_code", columns="quarter", values="hosp_intensity_q")
    v = pd.DataFrame(v)
    for q in ["2020Q2", "2020Q4", "2021Q1"]:
        v[f"Google retail+rec change {q}"] = mob[q]
    for q in ["2020Q3", "2020Q4"]:
        v[f"Legal hospitality intensity {q}"] = res[q]
    corr = v.corr(min_periods=100).round(3)
    corr.to_csv(CLEAN / "b6_feasibility_correlations_la.csv")
    n = v.notna().sum().rename("n_las")
    n.to_csv(CLEAN / "b6_feasibility_n.csv")
    print(n.to_string())
    print(corr.iloc[:, :1].to_string())
    print(corr.loc[[k for k in corr.index if "Google" in k or "Legal" in k],
                   ["Business Counts I+R per 1k (2019)", "FHRS restaurant/cafe", "OSM 2019 restaurant+cafe"]].to_string())
    print(corr.loc[[k for k in corr.index if "Legal" in k], [k for k in corr.columns if "Google" in k]].to_string())


if __name__ == "__main__":
    main()
