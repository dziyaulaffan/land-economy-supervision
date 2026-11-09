"""Step 4: Census MSOA design (pre-analysis plan, Design 3).

Outcome: movers in the band (usual address one year before was different, excluding "no usual address", which only
2001 records) per 1,000 residents of the band, all censuses on 2021 MSOAs (s4_msoa_inflows_on_msoa21.csv).
Main: dR = R2021 - R2011. Placebo: R2011 - R2001 (2001 MSOA by-age figures are a model estimate from ward rates).
Bands: 20-34 (main: the common band closest to 20-29 that contains it), 20-24 and 25-34.
Amenity: standardised log(1 + FHRS access, lambda = 1.5 km, restaurants/cafes + pubs/bars/clubs + takeaways);
check: OSM 2019 restaurants/cafes + fast food + pubs/bars/clubs, same lambda. LA fixed effects, six 2021 MSOA
controls added one at a time and together. CR1 and WCR bootstrap clustered by LA (B = 9,999).
"""
import numpy as np
import pandas as pd

from e_core import B, SEED, fit_cluster, rademacher
from ext_config import CLEAN

DROP_LA = {"E09000001", "E06000053"}
CTRL = ["X_telework_share", "X_garden_share", "X_flat_share", "X_private_rent_share", "X_age20_39_share",
        "X_student_share"]
BANDS = ["20-34", "20-24", "25-34"]


def std(v):
    return (v - v.mean()) / v.std()


def fit(df, y, a, controls, w):
    df = df.dropna(subset=[y, a] + list(controls)).sort_values("lad23cd").reset_index(drop=True)
    la = pd.get_dummies(df.lad23cd, dtype=float)
    X = np.hstack([la.values, df[[a] + list(controls)].values])
    names = [f"fe_{c}" for c in la.columns] + [a] + list(controls)
    tab, _ = fit_cluster(X, df[y].values, names, [a], cl_se=df.lad23cd.values, w=w, k_nested=la.shape[1])
    return tab.assign(n_obs=len(df), n_clusters=df.lad23cd.nunique())


def main():
    r = pd.read_csv(CLEAN / "s4_msoa_inflows_on_msoa21.csv")
    r = r[r.age_band.isin(BANDS)].pivot_table(index=["msoa21cd", "lad23cd", "age_band"], columns="census_year",
                                              values="rate_excl_nua_per_1000").reset_index()
    r["d2111"] = r[2021] - r[2011]
    r["d1101"] = r[2011] - r[2001]
    acc = pd.read_csv(CLEAN / "msoa21_amenity_access_ew.csv")
    acc["A_fhrs"] = np.log1p(acc[["access_pt_l15_fhrs_restaurant_cafe", "access_pt_l15_fhrs_pub_bar_club",
                                  "access_pt_l15_fhrs_takeaway"]].sum(axis=1))
    acc["A_osm"] = np.log1p(acc[["access_pt_l15_osm2019_restaurant_cafe", "access_pt_l15_osm2019_fast_food",
                                 "access_pt_l15_osm2019_pub_bar_club"]].sum(axis=1))
    acc = acc[~acc.lad23cd.isin(DROP_LA)]
    for c in ("A_fhrs", "A_osm"):
        acc[c] = std(acc[c])
    s = pd.read_csv(CLEAN / "s1_controls_msoa21.csv")[["msoa21cd"] + CTRL]
    df = r.merge(acc[["msoa21cd", "A_fhrs", "A_osm"]], on="msoa21cd").merge(s, on="msoa21cd")
    df = df[~df.lad23cd.isin(DROP_LA)]
    G = df.lad23cd.nunique()
    w = rademacher(B, G, SEED)
    specs = {"LA FE only": ()} | {f"+ {c[2:]}": (c,) for c in CTRL} | {"all six (headline)": tuple(CTRL)}
    out, L = [], []
    L.append("| Outcome | Band | Amenity | Spec | Coefficient (WCB p) | 95% CI | MSOAs | LAs |")
    L.append("|---|---|---|---|---|---|---|---|")
    for y, ylab in (("d2111", "2021 - 2011"), ("d1101", "placebo 2011 - 2001")):
        for band in BANDS:
            sub = df[df.age_band == band]
            for a in ("A_fhrs", "A_osm"):
                for spec, ctrl in specs.items():
                    if y == "d1101" and spec not in ("LA FE only", "all six (headline)"):
                        continue
                    if a == "A_osm" and spec not in ("LA FE only", "all six (headline)"):
                        continue
                    t = fit(sub, y, a, ctrl, w)
                    rr = t.iloc[0]
                    out.append(t.assign(outcome=ylab, band=band, amenity=a, spec=spec))
                    L.append(f"| {ylab} | {band} | {a} | {spec} | {rr.coef:.2f} ({rr.p_wcb:.3f}) | "
                             f"[{rr.ci_low:.2f}, {rr.ci_high:.2f}] | {int(rr.n_obs)} | {int(rr.n_clusters)} |")
                    print(L[-1], flush=True)
    desc = df.groupby("age_band")[[2001, 2011, 2021, "d2111", "d1101"]].mean().round(1)
    L += ["", "Mean rates per 1,000 across MSOAs:", "", desc.to_string()]
    res = pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore")
    res.to_csv(CLEAN / "s4_census_msoa.csv", index=False)
    (CLEAN / "s4_census_msoa.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
