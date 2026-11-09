"""R2. Shock, recovery, pre-pandemic trend and closure exposure, by 2021 MSOA and by 2023 LAD (no regressions).

For each group g (25-34, 20-29, 50+), with P the mid-year population and logs natural:
  shock_g    = ln P(2021) - ln P(2019)
  recovery_g = ln P(latest) - ln P(2021); latest = 2024 for MSOAs (NM_2014_1), 2025 for LADs (MYE25; a 2024
               version is kept for comparison with the MSOAs)
  trend_g    = (ln P(2019) - ln P(2015)) / 4, annualised
  pseudo shock and recovery (Step 6): ln P(2017) - ln P(2015) and ln P(2019) - ln P(2017), with the trend
               (ln P(2015) - ln P(2011)) / 4
Exposure:
  measure (c), MSOA: log FHRS access (restaurants and cafes + pubs, bars and clubs + takeaways, lambda = 1.5 km,
               point-based; extension/data/clean/msoa21_amenity_access_ew.csv), standardised over the 7,264 MSOAs.
  measure (c), LAD: M_c from extension/data/clean/s8_urban_measures_la.csv (log of the population-weighted mean of
               the same index, standardised over 316 LADs).
  VDL: variety-days lost, 23 Mar 2020 to 22 Mar 2021 (venue_mix, FHRS, 1.5 km), divided by 10; LAD version is the
               population-weighted mean of the MSOA values.
Controls: teleworkability, garden access, student share (S1, MSOA and LAD versions); log population density (for
the Step 5 terciles).

Outputs (extension/recovery/data/): r2_msoa.csv, r2_la.csv, r2_summary.md
"""
import numpy as np
import pandas as pd

from rc_common import CLEAN, DATA, DROP_LA, VM_DATA

GROUPS = ["a2534", "a2029", "a50p"]


def changes(p, idx, latest):
    w = {g: p.pivot_table(index=idx, columns="year", values=g) for g in GROUPS}
    out = pd.DataFrame(index=w[GROUPS[0]].index)
    for g, x in w.items():
        L = np.log(x)
        out[f"shock_{g}"] = L[2021] - L[2019]
        out[f"recovery_{g}"] = L[latest] - L[2021]
        out[f"trend_{g}"] = (L[2019] - L[2015]) / 4
        out[f"pshock_{g}"] = L[2017] - L[2015]
        out[f"precovery_{g}"] = L[2019] - L[2017]
        out[f"ptrend_{g}"] = (L[2015] - L[2011]) / 4
        if latest == 2025:
            out[f"recovery24_{g}"] = L[2024] - L[2021]
        out[f"pop2019_{g}"] = x[2019]
    return out.reset_index()


def msoa():
    p = pd.read_csv(DATA / "r1_pop_msoa.csv")
    d = changes(p, "msoa21cd", 2024)
    acc = pd.read_csv(CLEAN / "msoa21_amenity_access_ew.csv", usecols=["msoa21cd", "lad23cd",
                      "access_pt_l15_fhrs_restaurant_cafe", "access_pt_l15_fhrs_pub_bar_club", "access_pt_l15_fhrs_takeaway"])
    acc["acc_c"] = acc.iloc[:, 2:].sum(axis=1)
    la_ = np.log(acc.acc_c)
    acc["Z_c"] = (la_ - la_.mean()) / la_.std()
    vm = pd.read_csv(VM_DATA / "v2_treatment_msoa.csv", usecols=["msoa21cd", "vdl_main_fhrs_l15"])
    vm["Z_vdl"] = vm.vdl_main_fhrs_l15 / 10
    s1 = pd.read_csv(CLEAN / "s1_controls_msoa21.csv", usecols=["msoa21cd", "region", "telework_share", "garden_share",
                                                                "student_share"])
    v3 = pd.read_csv(VM_DATA / "v3_controls_msoa.csv", usecols=["msoa21cd", "log_pop_density"])
    d = (d.merge(acc[["msoa21cd", "lad23cd", "acc_c", "Z_c"]], on="msoa21cd").merge(vm, on="msoa21cd")
         .merge(s1, on="msoa21cd").merge(v3, on="msoa21cd"))
    d["london"] = d.region == "London"
    d["nation"] = d.lad23cd.str[0]
    return d


def la():
    p = pd.read_csv(DATA / "r1_pop_la.csv")
    d = changes(p.rename(columns={"lad23cd": "la_code"}), "la_code", 2025)
    m = pd.read_csv(CLEAN / "s8_urban_measures_la.csv", usecols=["la_code", "la_name", "region", "M_c", "acc_popw",
                                                                  "pop_2021", "area_km2", "london"])
    s1 = pd.read_csv(CLEAN / "s1_controls_la2023.csv", usecols=["la_code", "telework_share", "garden_share",
                                                                 "student_share"])
    v = pd.read_csv(VM_DATA / "v2_treatment_lad.csv", usecols=["lad23cd", "vdl_main_fhrs_l15"]).rename(
        columns={"lad23cd": "la_code"})
    v["Z_vdl"] = v.vdl_main_fhrs_l15 / 10
    d = d[~d.la_code.isin(DROP_LA)].merge(m, on="la_code").merge(s1, on="la_code").merge(v, on="la_code")
    d["Z_c"] = d.M_c
    d["log_pop_density"] = np.log(d.pop_2021 / d.area_km2)
    d["london"] = d.london.astype(bool)
    return d


def describe(d, level, latest):
    L = [f"### {level} (n = {len(d)}; recovery to mid-{latest})", "",
         "| Group | Variable | Mean | SD | p10 | p50 | p90 |", "|---|---|---|---|---|---|---|"]
    for g, lab in [("a2534", "25-34"), ("a2029", "20-29"), ("a50p", "50+")]:
        for v, vl in [("shock", "shock 2019-21"), ("recovery", f"recovery 2021-{str(latest)[2:]}"),
                      ("trend", "trend 2015-19 (annual)"), ("pshock", "pseudo shock 2015-17"),
                      ("precovery", "pseudo recovery 2017-19")]:
            x = 100 * d[f"{v}_{g}"]
            L.append(f"| {lab} | {vl} (log points x 100) | {x.mean():.2f} | {x.std():.2f} | {x.quantile(.1):.2f} | "
                     f"{x.median():.2f} | {x.quantile(.9):.2f} |")
    for v, vl in [("Z_c", "measure (c), standardised"), ("Z_vdl", "VDL / 10 (days)")]:
        x = d[v]
        L.append(f"| all | {vl} | {x.mean():.2f} | {x.std():.2f} | {x.quantile(.1):.2f} | {x.median():.2f} | {x.quantile(.9):.2f} |")
    fe = "lad23cd" if "lad23cd" in d else "region"
    L += ["", f"Correlations of the shock with exposure (raw; and within {'LA' if fe == 'lad23cd' else 'region'}):", "",
          "| Group | Exposure | Raw | Within |", "|---|---|---|---|"]
    for g, lab in [("a2534", "25-34"), ("a2029", "20-29"), ("a50p", "50+")]:
        for z, zl in [("Z_c", "measure (c)"), ("Z_vdl", "VDL")]:
            raw = d[f"shock_{g}"].corr(d[z])
            dm = lambda c: d[c] - d.groupby(fe)[c].transform("mean")
            wi = dm(f"shock_{g}").corr(dm(z))
            L.append(f"| {lab} | {zl} | {raw:.3f} | {wi:.3f} |")
    L += ["", f"Correlation of measure (c) with VDL: {d.Z_c.corr(d.Z_vdl):.3f}. Correlation of shock and recovery "
          f"(25-34) is not reported here, because it is the OLS recovery regression in another form.", ""]
    return L


def main():
    m = msoa()
    m.to_csv(DATA / "r2_msoa.csv", index=False)
    a = la()
    a.to_csv(DATA / "r2_la.csv", index=False)
    L = ["# Step 2: shock, recovery and exposure (descriptive only)", ""]
    L += describe(m, "2021 MSOAs, England and Wales", 2024)
    L += describe(a, "2023 LADs, England and Wales, excluding City of London and Isles of Scilly", 2025)
    (DATA / "r2_summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
