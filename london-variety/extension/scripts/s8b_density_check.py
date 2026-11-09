"""Departure 8, final check (decided after the registered results): density controls for measure (c), and the
North Northamptonshire anomaly in measure (a).

1. Workplace job density = BRES 2019 employment (Nomis NM_189_1, employment status "Employment", LADs April 2023)
   per km2 of land; resident density = mid-2019 residents per km2 (land area as in s8_urban_measures.py). Both enter
   as standardised logs over the 316 LADs. Correlations with measures (b), (c), teleworkability and garden access.
2. Headline model (f) with measure (c) in place of D, adding job density and/or resident density x young x year
   alongside teleworkability and garden access; ages 20-29 and 25-29 against the family proxy; all 316 and outside
   London; WCR bootstrap clustered by LA (B = 9,999).
3. Measure (a) corrected: SIC subclass 93191 (activities of racehorse owners) is excluded for every LAD. North
   Northamptonshire records 1,845 such local units in 2019 against 15 in 2017; the next highest LAD has 200.
   Measure (a) models rerun; the registered D carries the same units, so one sensitivity run of the headline with
   D recomputed without 93191 is reported (the registered results are not replaced).
"""
import numpy as np
import pandas as pd

from e_core import B, SEED, cell, ddd_diff, rademacher
from ext_config import CLEAN, RAW, download
import s2_national_ddd as s2

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
HEAD = ("X_telework", "X_garden")
KEYS = ["2020", "2021", "2022", "2022_minus_2020"]
YOUNG = {"age20_29": "20-29", "age25_29": "25-29"}


def z(v):
    return (v - v.mean()) / v.std()


def inputs():
    c = pd.read_csv(CLEAN / "s8_urban_measures_la.csv")
    jobs = pd.read_csv(download(
        f"{NOMIS}/NM_189_1.data.csv?geography=TYPE424&date=2019&industry=37748736&employment_status=4&measure=1"
        "&measures=20100&select=date_name,geography_code,geography_name,employment_status_name,obs_value,"
        "obs_status_name", RAW / "nomis" / "bres2019_employment_lad.csv"))
    rh = pd.read_csv(download(
        f"{NOMIS}/NM_141_1.data.csv?geography=TYPE424&date=2019&industry=134310919&employment_sizeband=0"
        "&legal_status=0&measures=20100&select=geography_code,geography_name,obs_value",
        RAW / "nomis" / "ukbc2019_93191_lad.csv"))
    c = c.merge(jobs[["GEOGRAPHY_CODE", "OBS_VALUE"]].rename(columns={"GEOGRAPHY_CODE": "la_code", "OBS_VALUE": "jobs_2019"}),
                on="la_code", how="left")
    c = c.merge(rh[["GEOGRAPHY_CODE", "OBS_VALUE"]].rename(columns={"GEOGRAPHY_CODE": "la_code", "OBS_VALUE": "units_93191"}),
                on="la_code", how="left")
    assert c[["jobs_2019", "units_93191"]].notna().all().all(), "missing BRES or 93191 for some LADs"
    c["job_density"] = c.jobs_2019 / c.area_km2
    c["pop_density"] = c.pop_mid2019 / c.area_km2
    c["X_jobdens"] = z(np.log(c.job_density))
    c["X_popdens"] = z(np.log(c.pop_density))
    c["per1k_FA_corr"] = (c.units_FA - c.units_93191) / c.pop_mid2019 * 1000
    c["M_a_corr"] = z(np.log(c.per1k_FA_corr))
    c["D_corr"] = z(np.log((c.units_IR - c.units_93191) / c.pop_mid2019 * 1000))
    return c


def main():
    c = inputs()
    nn = c[c.la_name == "North Northamptonshire"].iloc[0]
    L = ["### North Northamptonshire, measure (a)\n",
         f"Division 93 units in 2019: {int(nn.units_div93)}, of which SIC 93191 (racehorse owners) "
         f"{int(nn.units_93191)}. Measure (a) is {nn.per1k_FA:.2f} per 1,000 as published and "
         f"{nn.per1k_FA_corr:.2f} without 93191. National median of measure (a): {c.per1k_FA.median():.2f}. "
         f"Correlation of corrected with uncorrected (a): {np.corrcoef(c.M_a, c.M_a_corr)[0, 1]:.4f}; "
         f"of registered D with D without 93191: {np.corrcoef(c.z_log_per1k_IR, c.D_corr)[0, 1]:.4f}.\n",
         "### Density measures (316 LADs, standardised logs)\n",
         f"Job density median {c.job_density.median():,.0f} jobs per km2 (max {c.job_density.max():,.0f}, "
         f"{c.loc[c.job_density.idxmax(), 'la_name']}); resident density median {c.pop_density.median():,.0f} per km2.\n",
         "| | Measure (b) | Measure (c) | Teleworkability | Garden access | Job density | Resident density |",
         "|---|---|---|---|---|---|---|"]
    cols = {"M_b": "Measure (b)", "M_c": "Measure (c)", "telework_share": "Teleworkability",
            "garden_share": "Garden access", "X_jobdens": "Job density", "X_popdens": "Resident density"}
    corr = c[list(cols)].corr()
    for r in ("X_jobdens", "X_popdens"):
        L.append(f"| {cols[r]} | " + " | ".join(f"{corr.loc[r, k]:.3f}" for k in cols) + " |")
    c.to_csv(CLEAN / "s8b_density_measures_la.csv", index=False)

    p = s2.panel("internal").merge(c[["la_code", "M_a_corr", "M_c", "D_corr", "X_jobdens", "X_popdens"]], on="la_code")
    comp = "family_0_15_30_49"
    out = []
    L.append("\n### Measure (c) with density controls, headline (f), against the family proxy (WCB p)\n")
    L.append("| Sample | Young | Controls added to teleworkability and garden | 2020 | 2021 | 2022 | 2022 - 2020 | LAs |")
    L.append("|---|---|---|---|---|---|---|---|")
    specs = {"none (departure 8 model)": (), "job density": ("X_jobdens",), "resident density": ("X_popdens",),
             "job and resident density": ("X_jobdens", "X_popdens")}
    for sample in ("all 316", "outside London"):
        q0 = p if sample == "all 316" else p[~p.london.astype(bool)]
        w = rademacher(B, q0.la_code.nunique(), SEED)
        for young, yl in YOUNG.items():
            q = q0.assign(dy=q0[young] - q0[comp])
            for lab, extra in specs.items():
                t = ddd_diff(q, HEAD + extra, True, w=w, treat="M_c")
                out.append(t.assign(part="M_c density", sample=sample, young=young, spec=lab))
                L.append(f"| {sample} | {yl} | {lab} | " + " | ".join(cell(t, k) for k in KEYS)
                         + f" | {int(t.n_clusters.iloc[0])} |")
                print(L[-1], flush=True)
    L.append("\n### Measure (a) corrected (SIC 93191 excluded), headline (f), against the family proxy\n")
    L.append("| Sample | Young | 2020 | 2021 | 2022 | 2022 - 2020 | Garden x 2020 | LAs |")
    L.append("|---|---|---|---|---|---|---|---|")
    for sample in ("all 316", "outside London"):
        q0 = p if sample == "all 316" else p[~p.london.astype(bool)]
        w = rademacher(B, q0.la_code.nunique(), SEED)
        for young, yl in YOUNG.items():
            q = q0.assign(dy=q0[young] - q0[comp])
            t = ddd_diff(q, HEAD, True, w=w, treat="M_a_corr")
            out.append(t.assign(part="M_a corrected", sample=sample, young=young, spec="(f)"))
            L.append(f"| {sample} | {yl} | " + " | ".join(cell(t, k) for k in KEYS + ["X_garden:2020"])
                     + f" | {int(t.n_clusters.iloc[0])} |")
        if sample == "all 316":
            q = q0.assign(dy=q0.age20_29 - q0[comp])
            t = ddd_diff(q, HEAD, True, w=w, treat="D_corr")
            out.append(t.assign(part="registered D without 93191 (sensitivity)", sample=sample, young="age20_29",
                                spec="(f)"))
            L.append(f"| all 316, registered D without 93191 (sensitivity) | 20-29 | "
                     + " | ".join(cell(t, k) for k in KEYS + ["X_garden:2020"]) + " | 316 |")
    res = pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore")
    res.to_csv(CLEAN / "s8b_density_check.csv", index=False)
    (CLEAN / "s8b_density_check.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
