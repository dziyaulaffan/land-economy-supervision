"""Departure 8, data correction: measures (a) and (b) with SIC 93191 (activities of racehorse owners) excluded for
every LAD, rerun in the headline model (f) and reported beside the uncorrected departure 8 figures.

North Northamptonshire records 1,845 local units in 93191 in 2019 (15 in 2017); the next highest LAD in 2019 is
North Yorkshire (200 in 2019, 160 in 2017). Counts from Nomis NM_141_1 (UK Business Counts, LADs April 2023).
"""
import numpy as np
import pandas as pd

from e_core import B, SEED, cell, ddd_diff, rademacher
from ext_config import CLEAN
import s2_national_ddd as s2

HEAD = ("X_telework", "X_garden")
KEYS = ["2020", "2021", "2022", "2022_minus_2020", "X_garden:2020"]
YOUNG = {"age20_29": "20-29", "age25_29": "25-29"}
MEAS = {"M_a": "(a) per 1,000", "M_b": "(b) per km2"}


def z(v):
    return (v - v.mean()) / v.std()


def main():
    c = pd.read_csv(CLEAN / "s8b_density_measures_la.csv")
    units = c.units_FA - c.units_93191
    c["M_a_corr"] = z(np.log(units / c.pop_mid2019 * 1000))
    c["M_b_corr"] = z(np.log(units / c.area_km2))
    nn = c[c.la_name == "North Northamptonshire"].iloc[0]
    L = [f"North Northamptonshire: measure (a) {nn.per1k_FA:.2f} -> {units[nn.name] / nn.pop_mid2019 * 1000:.2f} per "
         f"1,000; measure (b) {nn.perkm2_FA:.2f} -> {units[nn.name] / nn.area_km2:.2f} per km2. Correlation of corrected "
         f"with uncorrected: (a) {np.corrcoef(c.M_a, c.M_a_corr)[0, 1]:.4f}, (b) {np.corrcoef(c.M_b, c.M_b_corr)[0, 1]:.4f}.\n",
         "| Measure | Version | Sample | Young | 2020 | 2021 | 2022 | 2022 - 2020 | Garden x 2020 | LAs |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    prev = pd.read_csv(CLEAN / "s8_urban_ddd.csv", dtype={"term": str})
    p = s2.panel("internal").merge(c[["la_code", "M_a_corr", "M_b_corr"]], on="la_code")
    comp = "family_0_15_30_49"
    out = []
    for m, lab in MEAS.items():
        for sample in ("all 316", "outside London"):
            q0 = p if sample == "all 316" else p[~p.london.astype(bool)]
            w = rademacher(B, q0.la_code.nunique(), SEED)
            for young, yl in YOUNG.items():
                old = prev[(prev.measure == m) & (prev["sample"] == sample) & (prev.young == young)]
                L.append(f"| {lab} | as published | {sample} | {yl} | " + " | ".join(cell(old, k) for k in KEYS)
                         + f" | {int(old.n_clusters.iloc[0])} |")
                q = q0.assign(dy=q0[young] - q0[comp])
                t = ddd_diff(q, HEAD, True, w=w, treat=f"{m}_corr")
                out.append(t.assign(measure=f"{m}_corr", sample=sample, young=young))
                L.append(f"| {lab} | 93191 excluded | {sample} | {yl} | " + " | ".join(cell(t, k) for k in KEYS)
                         + f" | {int(t.n_clusters.iloc[0])} |")
                print(L[-1], flush=True)
    pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore").to_csv(
        CLEAN / "s8c_corrected_ab.csv", index=False)
    (CLEAN / "s8c_corrected_ab.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
