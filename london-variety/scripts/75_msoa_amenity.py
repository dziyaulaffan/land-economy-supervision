"""MSOA (2011) amenity density and its correlation with the controls, overall and within boroughs.

Amenity density = I+R local units 2019 (UK Business Counts, 40_amenity_density.py) per 1,000
residents, mid-2019 small-area population estimates on 2011 MSOAs (Nomis NM_2010_1, 2011-based
series). Nomis rounds unit counts to the nearest 5, so a published 0 means 0-2 units; the 3 MSOAs
with 0 are set to 1 unit before taking logs. City of London's MSOA is excluded (982 MSOAs).
Within-borough correlations use variables demeaned by borough.
"""
import numpy as np
import pandas as pd

from config import CITY, CLEAN, OUT, RAW, download, london_frame

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
CONTROLS = {"telework_share": "Teleworkability", "garden_share": "Garden access",
            "age20_39_share": "Share aged 20-39", "private_rent_share": "Private renting share"}
FLAG = 0.6


def main():
    url = (f"{NOMIS}/NM_2010_1.data.csv?geography=TYPE297&date=2019&gender=0&c_age=200&measures=20100"
           "&select=geography_code,obs_value")
    pop = pd.read_csv(download(url, RAW / "nomis" / "sape_mid2019_msoa2011_ew.csv"))
    pop = pop.rename(columns={"GEOGRAPHY_CODE": "msoa11_code", "OBS_VALUE": "pop_mid2019"})

    u = pd.read_csv(CLEAN / "london_amenity_units_2019_msoa2011.csv")
    names = london_frame()[["la_code", "la_name", "london_zone"]]
    d = u.merge(pop, on="msoa11_code").merge(names, on="la_name", how="left")
    d = d[d.la_name != "City of London"]
    assert d.la_code.notna().all() and len(d) == 982, (len(d), d.la_code.isna().sum())
    d["units_IR_adj"] = d.units_IR.clip(lower=1)
    d["per1k_IR"] = d.units_IR_adj / d.pop_mid2019 * 1000
    d["log_per1k_IR"] = np.log(d.per1k_IR)
    d["D_msoa"] = (d.log_per1k_IR - d.log_per1k_IR.mean()) / d.log_per1k_IR.std()
    c = pd.read_csv(CLEAN / "controls_msoa2011.csv")
    d = d.merge(c, on="msoa11_code", how="left")
    assert d[list(CONTROLS)].notna().all().all()
    for k in CONTROLS:
        d[f"X_{k}"] = (d[k] - d[k].mean()) / d[k].std()
    d.to_csv(CLEAN / "msoa_amenity_controls.csv", index=False)

    rows = []
    for k, lab in CONTROLS.items():
        overall = d.log_per1k_IR.corr(d[k])
        dm = d[["log_per1k_IR", k]] - d.groupby("la_code")[["log_per1k_IR", k]].transform("mean")
        within = dm.log_per1k_IR.corr(dm[k])
        rows.append(dict(control=lab, variable=k, corr_overall=overall, corr_within_borough=within,
                         flag_within_above_0_6=abs(within) > FLAG))
    r = pd.DataFrame(rows)
    r["n_msoa"] = len(d)
    r.to_csv(OUT / "event_study" / "msoa_correlations.csv", index=False)
    print(r.round(3).to_string(index=False))
    tw = r.set_index("variable").loc["telework_share", "corr_within_borough"]
    msg = (f"FLAG: within-borough correlation between amenity density and teleworkability is {tw:.2f} (> {FLAG})"
           if abs(tw) > FLAG else
           f"Within-borough correlation between amenity density and teleworkability is {tw:.2f} (not above {FLAG})")
    print(msg)


if __name__ == "__main__":
    main()
