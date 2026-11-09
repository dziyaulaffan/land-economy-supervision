"""S1 task 3: correlations of each control with log amenity density (no regressions).

(a) 316 LAs (City of London and Isles of Scilly excluded), log_per1k_IR (Business Counts 2019 I+R per 1,000).
(b) the same after demeaning both variables by region.
(c) 7,262 MSOAs (the two MSOAs of City of London and Isles of Scilly excluded), main MSOA amenity measure
    log(1 + FHRS restaurant/cafe + pub/bar/club + takeaway access, lambda 1.5 km, point based), nationally and
    after demeaning both by lad23cd.
Also writes s1_validation_msoa_vs_la.csv: 2021 MSOA counts summed to 2023 LADs against the 2011 LA controls.
"""
import numpy as np
import pandas as pd

from ext_config import CLEAN, RAW

SMALL = {"E09000001", "E06000053"}
SHARES = ["telework_share", "garden_share", "flat_share", "private_rent_share", "age20_39_share", "student_share"]
AMEN = ["access_pt_l15_fhrs_restaurant_cafe", "access_pt_l15_fhrs_pub_bar_club", "access_pt_l15_fhrs_takeaway"]


def corr(a, b):
    return np.corrcoef(a, b)[0, 1]


def demean(d, cols, by):
    return d[cols] - d.groupby(by)[cols].transform("mean")


def tw2011_major() -> pd.DataFrame:
    """2011 LA teleworkability rebuilt at SOC major-group resolution (diagnostic for resolution loss)."""
    hw = pd.read_csv(CLEAN / "s1_homework_score_soc2010_major.csv").set_index("major")
    occ = pd.read_csv(RAW / "s1" / "census2011_la" / "qs606ew_occupation_la2011_ew.csv")
    occ["soc3"] = pd.to_numeric(occ.CELL_NAME.str.extract(r"^(\d{3})\.")[0], errors="coerce")
    occ = occ[occ.soc3.notna()].copy()
    occ["major"] = (occ.soc3 // 100).astype(int)
    lk = pd.read_csv(CLEAN / "s1_lookup_la2011_lad23.csv")
    occ = occ.merge(lk[["la2011_code", "la_code"]], left_on="GEOGRAPHY_CODE", right_on="la2011_code")
    occ["tw_a"] = occ.OBS_VALUE * occ.major.map(hw.teleworkable_major.astype(float))
    occ["tw_b"] = occ.OBS_VALUE * occ.major.map(hw.tw_frac)
    g = occ.groupby("la_code")[["OBS_VALUE", "tw_a", "tw_b"]].sum()
    return pd.DataFrame({"tw2011_major_rule": g.tw_a / g.OBS_VALUE, "tw2011_major_frac": g.tw_b / g.OBS_VALUE})


def main():
    la = pd.read_csv(CLEAN / "s1_controls_la2023.csv")
    la = la.merge(pd.read_csv(CLEAN / "b3_la_crosssection.csv", usecols=["la_code", "log_per1k_IR"]), on="la_code")
    la = la[~la.la_code.isin(SMALL)].copy()
    assert len(la) == 316

    ms = pd.read_csv(CLEAN / "s1_controls_msoa21.csv")
    acc = pd.read_csv(CLEAN / "msoa21_amenity_access_ew.csv", usecols=["msoa21cd"] + AMEN)
    acc["log_amenity_access"] = np.log1p(acc[AMEN].sum(axis=1))
    ms = ms.merge(acc[["msoa21cd", "log_amenity_access"]], on="msoa21cd")
    ms = ms[~ms.lad23cd.isin(SMALL)].dropna(subset=["log_amenity_access"]).copy()

    controls = SHARES + ["telework_share_frac"]
    la_dm = demean(la, SHARES + ["log_per1k_IR"], "region")
    ms_dm = demean(ms, controls + ["log_amenity_access"], "lad23cd")
    rows = []
    for v in controls:
        r = {"control": v}
        if v in la:
            r.update({"la_national": corr(la[v], la.log_per1k_IR),
                      "la_within_region": corr(la_dm[v], la_dm.log_per1k_IR), "n_la": len(la)})
        r.update({"msoa_national": corr(ms[v], ms.log_amenity_access),
                  "msoa_within_la": corr(ms_dm[v], ms_dm.log_amenity_access), "n_msoa": len(ms)})
        rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(CLEAN / "s1_control_correlations.csv", index=False)
    print(out.round(3).to_string(index=False))

    # 2021 MSOA counts summed to 2023 LADs vs the 2011 LA controls
    allms = pd.read_csv(CLEAN / "s1_controls_msoa21.csv")
    g = allms.groupby("lad23cd").sum(numeric_only=True)
    agg = pd.DataFrame({
        "telework_share": g.emp_teleworkable / g.employed_2021,
        "telework_share_frac": g.emp_teleworkable_frac / g.employed_2021,
        "garden_share": g.addresses_with_pos / g.addresses,
        "flat_share": g.hh_flats / g.households_2021,
        "private_rent_share": g.hh_private_rent / g.hh_total_tenure,
        "age20_39_share": g.pop_20_39 / g.pop_2021,
        "student_share": g.students_18plus / g.pop16plus_2021})
    m = la.set_index("la_code").join(agg, rsuffix="_2021msoa").join(tw2011_major())
    rows = []
    for v in SHARES:
        rows.append({"comparison": f"{v}: 2021 MSOA aggregate vs 2011 LA", "n_la": len(m),
                     "corr": corr(m[v], m[f"{v}_2021msoa"]),
                     "mean_2011_la": m[v].mean(), "mean_2021_msoa_agg": m[f"{v}_2021msoa"].mean(),
                     "max_abs_diff": (m[v] - m[f"{v}_2021msoa"]).abs().max()})
    for a, b, lab in [("telework_share", "telework_share_frac", "telework_share_frac (2021 MSOA agg) vs 2011 LA"),
                      ("telework_share", "tw2011_major_rule", "2011 LA at major-group resolution, threshold rule, vs 2011 LA minor-group"),
                      ("telework_share", "tw2011_major_frac", "2011 LA at major-group resolution, fractional rule, vs 2011 LA minor-group"),
                      ("tw2011_major_rule", "telework_share_2021msoa", "2021 MSOA agg threshold rule vs 2011 LA same rule"),
                      ("tw2011_major_frac", "telework_share_frac", "2021 MSOA agg fractional rule vs 2011 LA same rule")]:
        rows.append({"comparison": lab, "n_la": len(m), "corr": corr(m[a], m[b]),
                     "mean_2011_la": m[a].mean(), "mean_2021_msoa_agg": m[b].mean(),
                     "max_abs_diff": (m[a] - m[b]).abs().max()})
    val = pd.DataFrame(rows)
    val.to_csv(CLEAN / "s1_validation_msoa_vs_la.csv", index=False)
    print(val.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
