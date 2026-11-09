"""Amenity density: UK Business Counts 2019 local units (Nomis NM_141_1) per 1,000 residents.

Sections are built from SIC 2007 divisions because NM_141_1 exposes divisions, not sections:
  I  Accommodation and food services       = divisions 55 + 56
  R  Arts, entertainment and recreation    = divisions 90 + 91 + 92 + 93
Population: ONS mid-2019 estimates (Nomis NM_2002_1, rebased to Census 2021).
"""
import numpy as np
import pandas as pd

from config import CLEAN, RAW, london_frame, download

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
DIVISIONS = {
    "146800695": "55", "146800696": "56",
    "146800730": "90", "146800731": "91", "146800732": "92", "146800733": "93",
    "37748736": "total",
}
GEOG = "TYPE424"  # local authority districts / unitaries, April 2023 boundaries


def msoa_units():
    """2019 local units for sections I and R at MSOA level, London only.

    Nomis publishes UK Business Counts down to MSOA (no LSOA). For 2019 only the 2011 MSOA
    boundaries carry values; 2021 MSOAs (TYPE152) return "missing" for 2019.
    London region = Nomis code 2013265927. No matching to other data at this stage.
    """
    url = (f"{NOMIS}/NM_141_1.data.csv?geography=2013265927TYPE297&date=2019&industry={','.join(DIVISIONS)}"
           "&employment_sizeband=0&legal_status=0&measures=20100&recordlimit=1000000"
           "&select=date_name,geography_name,geography_code,industry,industry_name,obs_value,obs_status_name")
    f = download(url, RAW / "nomis" / "ukbc_local_units_2019_divisions_london_msoa2011.csv")
    u = pd.read_csv(f)
    assert (u.OBS_STATUS_NAME == "Normal Value").all(), u.OBS_STATUS_NAME.value_counts()
    u["div"] = u.INDUSTRY.astype(str).map(DIVISIONS)
    w = u.pivot_table(index=["GEOGRAPHY_CODE", "GEOGRAPHY_NAME"], columns="div", values="OBS_VALUE", aggfunc="sum")
    w.columns = [f"units_div{c}" if c != "total" else "units_all_industries" for c in w.columns]
    w = w.reset_index().rename(columns={"GEOGRAPHY_CODE": "msoa11_code", "GEOGRAPHY_NAME": "msoa11_name"})
    w["units_I_accom_food"] = w.units_div55 + w.units_div56
    w["units_R_arts_rec"] = w[["units_div90", "units_div91", "units_div92", "units_div93"]].sum(axis=1)
    w["units_IR"] = w.units_I_accom_food + w.units_R_arts_rec
    # MSOA names are "<LA name> NNN"
    w["la_name"] = w.msoa11_name.str.replace(r"\s+\d{3}$", "", regex=True)
    w.to_csv(CLEAN / "london_amenity_units_2019_msoa2011.csv", index=False)
    print(f"MSOA 2011: {len(w)} London MSOAs, I+R units = {w.units_IR.sum():.0f}")
    return w


def main():
    raw = RAW / "nomis"
    ukbc_url = (f"{NOMIS}/NM_141_1.data.csv?geography={GEOG}&date=2019&industry={','.join(DIVISIONS)}"
                "&employment_sizeband=0&legal_status=0&measures=20100"
                "&select=date_name,geography_name,geography_code,industry,industry_name,obs_value,obs_status_name")
    pop_url = (f"{NOMIS}/NM_2002_1.data.csv?geography={GEOG}&date=2019&gender=0&c_age=200&measures=20100"
               "&select=date_name,geography_name,geography_code,obs_value")
    download(ukbc_url, raw / "ukbc_local_units_2019_divisions.csv")
    download(pop_url, raw / "mye_population_mid2019.csv")

    u = pd.read_csv(raw / "ukbc_local_units_2019_divisions.csv")
    u["div"] = u.INDUSTRY.astype(str).map(DIVISIONS)
    wide = u.pivot_table(index=["GEOGRAPHY_CODE", "GEOGRAPHY_NAME"], columns="div", values="OBS_VALUE", aggfunc="sum")
    wide.columns = [f"units_div{c}" if c != "total" else "units_all_industries" for c in wide.columns]
    wide = wide.reset_index().rename(columns={"GEOGRAPHY_CODE": "la_code", "GEOGRAPHY_NAME": "la_name"})
    wide["units_I_accom_food"] = wide.units_div55 + wide.units_div56
    wide["units_R_arts_rec"] = wide[["units_div90", "units_div91", "units_div92", "units_div93"]].sum(axis=1)
    wide["units_IR"] = wide.units_I_accom_food + wide.units_R_arts_rec

    p = pd.read_csv(raw / "mye_population_mid2019.csv").rename(
        columns={"GEOGRAPHY_CODE": "la_code", "OBS_VALUE": "pop_mid2019"})[["la_code", "pop_mid2019"]]
    df = wide.merge(p, on="la_code", how="left")
    for c in ["units_I_accom_food", "units_R_arts_rec", "units_IR"]:
        df[c.replace("units_", "per1k_")] = df[c] / df.pop_mid2019 * 1000
    df.to_csv(CLEAN / "amenity_units_2019_all_las.csv", index=False)

    # analysis panel: 32 boroughs, City of London excluded (see config.ANALYSIS)
    lon = london_frame().merge(df.drop(columns="la_name"), on="la_code", how="left")
    assert len(lon) == 32 and lon.pop_mid2019.notna().all() and lon.units_IR.notna().all(), "missing borough"

    # continuous measures
    lon["log_per1k_IR"] = np.log(lon.per1k_IR)
    lon["z_log_per1k_IR"] = (lon.log_per1k_IR - lon.log_per1k_IR.mean()) / lon.log_per1k_IR.std()
    lon["amenity_rank"] = lon.per1k_IR.rank(ascending=False).astype(int)

    # binary split at the median of the 32 boroughs
    med = lon.per1k_IR.median()
    lon["amenity_high"] = lon.per1k_IR > med
    lon["amenity_group"] = lon.amenity_high.map({True: "High amenity", False: "Low amenity"})

    # split at the median within Inner and within Outer London separately. The London-wide median
    # leaves a single low-amenity Inner borough, so within-zone medians are used to separate the two
    # dimensions.
    zmed = lon.groupby("london_zone").per1k_IR.transform("median")
    lon["amenity_high_within_zone"] = lon.per1k_IR > zmed
    lon["zone_amenity_group"] = (lon.london_zone.str.replace(" London", "") + ", "
                                 + lon.amenity_high_within_zone.map({True: "high", False: "low"}) + " amenity")
    lon.sort_values("amenity_rank").to_csv(CLEAN / "london_amenity_density_2019.csv", index=False)

    m = msoa_units()
    chk = m.groupby("la_name").units_IR.sum()
    print("MSOA vs LA I+R totals, max abs gap:",
          (chk - df.set_index("la_name").units_IR.reindex(chk.index)).abs().max())

    print(f"London-wide median I+R per 1k = {med:.2f}")
    print(lon.groupby("london_zone").per1k_IR.median().round(2).to_string())
    print(pd.crosstab(lon.london_zone, lon.amenity_group))
    print(lon.zone_amenity_group.value_counts().to_string())
    print(lon.sort_values("amenity_rank")[["la_name", "london_zone", "per1k_IR", "amenity_group",
                                           "zone_amenity_group"]].to_string(index=False))


if __name__ == "__main__":
    main()
