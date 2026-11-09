"""Departure 8, pre-trend check (decided after the registered results): measures (b) and (c) carry large positive
2016-2018 coefficients. Deviations of the 2020 and 2022 coefficients from a linear trend fitted by OLS through the
2016-2019 yearly coefficients (2019 = 0), headline model (f), ages 20-29 and 25-29 against the family proxy,
with and without London; also with both density controls for measure (c). WCR bootstrap clustered by LA.
"""
import numpy as np
import pandas as pd

from e_core import B, SEED, cell, ddd_diff, rademacher
from ext_config import CLEAN
import s2_national_ddd as s2

HEAD = ("X_telework", "X_garden")
PRE = (2016, 2017, 2018, 2019)


def trend_con():
    kbar = np.mean(PRE)
    sxx = sum((k - kbar) ** 2 for k in PRE)
    con = {"pre_trend_slope": {f"D:{k}": (k - kbar) / sxx for k in PRE if k != 2019}}
    for t in (2020, 2021, 2022):
        c = {f"D:{t}": 1.0}
        for k in PRE:
            if k != 2019:
                c[f"D:{k}"] = -(1 / len(PRE) + (t - kbar) * (k - kbar) / sxx)
        con[f"{t}_dev"] = c
    return con


def main():
    c = pd.read_csv(CLEAN / "s8b_density_measures_la.csv")
    units = c.units_FA - c.units_93191
    c["M_b_corr"] = (np.log(units / c.area_km2) - np.log(units / c.area_km2).mean()) / np.log(units / c.area_km2).std()
    p = s2.panel("internal").merge(c[["la_code", "M_b_corr", "M_c", "X_jobdens", "X_popdens"]], on="la_code")
    comp = "family_0_15_30_49"
    keys = ["2016", "2017", "2018", "2020", "2022", "pre_trend_slope", "2020_dev", "2021_dev", "2022_dev"]
    L = ["| Measure | Sample | Young | Density controls | " + " | ".join(keys) + " | LAs |",
         "|---|---|---|---|" + "---|" * (len(keys) + 1)]
    out = []
    for m, extra_sets in (("M_b_corr", [()]), ("M_c", [(), ("X_jobdens", "X_popdens")])):
        for sample in ("all 316", "outside London"):
            q0 = p if sample == "all 316" else p[~p.london.astype(bool)]
            w = rademacher(B, q0.la_code.nunique(), SEED)
            for young in ("age20_29", "age25_29"):
                q = q0.assign(dy=q0[young] - q0[comp])
                for extra in extra_sets:
                    t = ddd_diff(q, HEAD + extra, True, w=w, treat=m, extra_con=trend_con())
                    lab = "both" if extra else "none"
                    out.append(t.assign(measure=m, sample=sample, young=young, density=lab))
                    L.append(f"| {m} | {sample} | {young} | {lab} | " + " | ".join(cell(t, k) for k in keys)
                             + f" | {int(t.n_clusters.iloc[0])} |")
                    print(L[-1], flush=True)
    pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore").to_csv(
        CLEAN / "s8d_pretrend_check.csv", index=False)
    (CLEAN / "s8d_pretrend_check.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
