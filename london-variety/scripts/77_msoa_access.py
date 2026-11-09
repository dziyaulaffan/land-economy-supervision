"""Consumption access: hospitality and leisure units reachable from each 2011 London MSOA, 2019.

Units: UK Business Counts 2019 local units (Nomis NM_141_1), sections I (divisions 55-56) and R
(divisions 90-93), for every 2011 MSOA in England and Wales. MSOA is the finest geography Nomis publishes
for this dataset (no LSOA or point data), so each MSOA's units are placed at its 2011 population-weighted
centroid (ONS PWC, British National Grid). All England and Wales MSOAs are sources, so access for outer
London MSOAs includes units across the GLA boundary.

For each of the 982 analysis MSOAs (City of London excluded), with d_ij the centroid distance in km:
    ring counts   R1 = sum_j units_j 1[0 <= d_ij < 1], R2 = ... 1[1 <= d < 2], R3 = ... 1[2 <= d < 5]
    access index  A(lambda) = sum_j units_j exp(-d_ij / lambda), lambda = 1.5 km (main), 1 km and 3 km
Own-MSOA units enter at d = 0 (ring 0-1 km, weight 1).
Regressors (written as X/D columns): standardised log A(lambda); standardised log(1 + R_k) for rings.
"""
import numpy as np
import pandas as pd

from config import CLEAN, OUT, RAW, download

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
DIVISIONS = {"146800695": "55", "146800696": "56", "146800730": "90", "146800731": "91",
             "146800732": "92", "146800733": "93"}
LAMBDAS = {"access_l15": 1.5, "access_l10": 1.0, "access_l30": 3.0}
RINGS = {"ring_0_1": (0, 1), "ring_1_2": (1, 2), "ring_2_5": (2, 5)}
FLAG = 0.7


def zscore(x: pd.Series) -> pd.Series:
    return (x - x.mean()) / x.std()


def ukbc_msoa() -> pd.DataFrame:
    """I+R local units 2019 for all 2011 MSOAs in England and Wales (paged: Nomis caps calls at 25,000 rows)."""
    out = RAW / "nomis" / "ukbc_local_units_2019_divisions_msoa2011_ew.csv"
    if not out.exists():
        url = (f"{NOMIS}/NM_141_1.data.csv?geography=TYPE297&date=2019&industry={','.join(DIVISIONS)}"
               "&employment_sizeband=0&legal_status=0&measures=20100"
               "&select=geography_code,industry,obs_value,obs_status_name")
        pages, offset = [], 0
        while True:
            f = download(f"{url}&recordoffset={offset}", RAW / "nomis" / "pages" / f"ukbc_msoa_ew_{offset}.csv")
            page = pd.read_csv(f)
            pages.append(page)
            if len(page) < 25000:
                break
            offset += 25000
        pd.concat(pages, ignore_index=True).to_csv(out, index=False)
    u = pd.read_csv(out)
    assert (u.OBS_STATUS_NAME == "Normal Value").all()
    assert len(u) == 7201 * len(DIVISIONS), len(u)
    return u.groupby("GEOGRAPHY_CODE").OBS_VALUE.sum().rename("units_IR").reset_index().rename(
        columns={"GEOGRAPHY_CODE": "msoa11_code"})


def main():
    units = ukbc_msoa()
    cent = pd.read_csv(CLEAN / "msoa_distance_charing_cross.csv")  # 982 analysis MSOAs, BNG
    import json
    allc = pd.DataFrame(json.loads((RAW / "ons_geography" / "msoa2011_pwc_bng.json").read_text()))
    src = allc.merge(units, on="msoa11_code", how="inner")
    assert len(src) == 7201
    # cross-check London units against the earlier London-only pull
    lon_units = pd.read_csv(CLEAN / "london_amenity_units_2019_msoa2011.csv")[["msoa11_code", "units_IR"]]
    chk = lon_units.merge(src, on="msoa11_code", suffixes=("_lon", "_ew"))
    assert (chk.units_IR_lon == chk.units_IR_ew).all(), "London MSOA counts differ between pulls"

    m = pd.read_csv(CLEAN / "msoa_amenity_controls.csv")[["msoa11_code", "la_code", "log_per1k_IR", "D_msoa",
                                                           "units_IR"]]
    d = m.merge(cent[["msoa11_code", "easting", "northing", "log_dist_cc", "X_log_dist_cc"]], on="msoa11_code")
    assert len(d) == 982
    D = np.hypot(d.easting.values[:, None] - src.easting.values[None, :],
                 d.northing.values[:, None] - src.northing.values[None, :]) / 1000  # 982 x 7201, km
    U = src.units_IR.values.astype(float)
    for k, (lo, hi) in RINGS.items():
        d[k] = ((D >= lo) & (D < hi)) @ U
        d[f"X_{k}"] = zscore(np.log1p(d[k]))
    for k, lam in LAMBDAS.items():
        d[k] = np.exp(-D / lam) @ U
        d[f"log_{k}"] = np.log(d[k])
        d[f"D_{k}"] = zscore(d[f"log_{k}"])
    d["n_msoa_within_1km"] = (D < 1).sum(axis=1)
    d["nearest_other_msoa_km"] = np.sort(D, axis=1)[:, 1]
    d.drop(columns=["easting", "northing"]).to_csv(CLEAN / "msoa_access_2019.csv", index=False)

    print(d[list(RINGS) + list(LAMBDAS) + ["n_msoa_within_1km", "nearest_other_msoa_km"]].describe()
          .round(2).to_string())

    # correlations: log access / ring logs vs log distance to Charing Cross and log own density
    rows = []
    vars_ = {f"log_{k}": f"log access index, lambda = {lam} km" for k, lam in LAMBDAS.items()}
    vars_.update({f"X_{k}": f"log(1 + units {lo}-{hi} km)" for k, (lo, hi) in RINGS.items()})
    for v, lab in vars_.items():
        for other, olab in (("log_dist_cc", "log distance to Charing Cross"),
                            ("log_per1k_IR", "log own-MSOA amenity density")):
            dm = d[[v, other]] - d.groupby("la_code")[[v, other]].transform("mean")
            rows.append(dict(measure=lab, against=olab, corr_overall=d[v].corr(d[other]),
                             corr_within_borough=dm[v].corr(dm[other])))
    r = pd.DataFrame(rows)
    r["flag_abs_within_above_0_7"] = r.corr_within_borough.abs() > FLAG
    r.to_csv(OUT / "event_study" / "msoa_access_correlations.csv", index=False)
    print(r.round(3).to_string(index=False))
    main_r = r[(r.measure.str.contains("1.5")) & (r.against.str.contains("distance"))].iloc[0]
    if abs(main_r.corr_within_borough) > FLAG:
        print(f"FLAG: within-borough correlation of the access index (1.5 km) with log distance to Charing Cross "
              f"is {main_r.corr_within_borough:.3f}, |r| > {FLAG}")
    else:
        print(f"Within-borough correlation of the access index (1.5 km) with log distance to Charing Cross is "
              f"{main_r.corr_within_borough:.3f} (|r| not above {FLAG})")


if __name__ == "__main__":
    main()
