"""B3 LA cross-section: UK Business Counts 2019 amenity density and cheap controls, all 318 LAs in England and Wales.

Amenity density exactly as scripts/40_amenity_density.py: 2019 local units (Nomis NM_141_1, TYPE424 = April 2023
LADs) in SIC divisions 55+56 (I) and 90-93 (R) per 1,000 mid-2019 residents (Nomis NM_2002_1, rebased to Census
2021). The pilot's own all-LA download (PILOT_RAW/nomis) is reused. Treatment = standardised log density.
Controls: region/country, mid-2019 population and age shares (single-year file from b3_migration.py), Centre for
Cities PUA urban flag (LAtoPUA2024, as in 10_migration.py), ONS private outdoor space share (April 2020 edition, as
in 70_controls.py, aggregated to 2023 LADs), Census 2021 private-renting share of households (TS054, NM_2072_1).
"""
import numpy as np
import pandas as pd

from b3_migration import lookup
from ext_config import CLEAN, PILOT_RAW, RAW, download

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
DIVISIONS = {"146800695": "55", "146800696": "56", "146800730": "90", "146800731": "91", "146800732": "92",
             "146800733": "93", "37748736": "total"}
SMALL = {"E09000001", "E06000053"}  # City of London, Isles of Scilly: resident population under 10,000
# pre-2023 districts (codes in the April 2020 garden tables) merged into 2023 unitaries
MERGED = {"E06000060": ["E07000004", "E07000005", "E07000006", "E07000007"],
          "E06000061": ["E07000150", "E07000152", "E07000153", "E07000156"],
          "E06000062": ["E07000151", "E07000154", "E07000155"],
          "E06000063": ["E07000026", "E07000028", "E07000029"],
          "E06000064": ["E07000027", "E07000030", "E07000031"],
          "E06000065": [f"E070001{i}" for i in range(63, 70)],
          "E06000066": ["E07000187", "E07000188", "E07000189", "E07000246"]}
OLD_TO_NEW = {o: n for n, olds in MERGED.items() for o in olds}


def z(s):
    return (s - s.mean()) / s.std()


def business_counts(lk):
    u = pd.read_csv(PILOT_RAW / "nomis" / "ukbc_local_units_2019_divisions.csv")
    u = u[u.GEOGRAPHY_CODE.isin(lk.la_code)]
    status = u.OBS_STATUS_NAME.value_counts().to_dict()
    u["div"] = u.INDUSTRY.astype(str).map(DIVISIONS)
    w = u.pivot_table(index="GEOGRAPHY_CODE", columns="div", values="OBS_VALUE", aggfunc="sum")
    w.columns = [f"units_div{c}" if c != "total" else "units_all_industries" for c in w.columns]
    w = w.rename_axis("la_code").reset_index()
    w["units_I_accom_food"] = w.units_div55 + w.units_div56
    w["units_R_arts_rec"] = w[["units_div90", "units_div91", "units_div92", "units_div93"]].sum(axis=1)
    w["units_IR"] = w.units_I_accom_food + w.units_R_arts_rec
    p = pd.read_csv(PILOT_RAW / "nomis" / "mye_population_mid2019.csv").rename(
        columns={"GEOGRAPHY_CODE": "la_code", "OBS_VALUE": "pop_mid2019"})[["la_code", "pop_mid2019"]]
    w = w.merge(p, on="la_code", how="left")
    for c in ["units_I_accom_food", "units_R_arts_rec", "units_IR"]:
        w[c.replace("units_", "per1k_")] = w[c] / w.pop_mid2019 * 1000
    w["log_per1k_IR"] = np.log(w.per1k_IR)
    main = ~w.la_code.isin(SMALL)
    w["z_log_per1k_IR"] = np.nan
    w.loc[main, "z_log_per1k_IR"] = z(w.loc[main, "log_per1k_IR"])
    w["z_log_per1k_IR_all318"] = z(w.log_per1k_IR)
    w["small_pop_excluded_from_z"] = ~main
    return w, status


def age_shares(lk):
    p = pd.read_csv(RAW / "nomis" / "mye_population_mid2019_single_age_all_las.csv")
    p = p[p.GEOGRAPHY_CODE.isin(lk.la_code)]
    p["age"] = p.C_AGE - 101
    tot = p.groupby("GEOGRAPHY_CODE").OBS_VALUE.sum()
    sh = lambda lo, hi: p[p.age.between(lo, hi)].groupby("GEOGRAPHY_CODE").OBS_VALUE.sum() / tot
    return pd.DataFrame({"pop_mid2019_sya_sum": tot, "age20_29_share": sh(20, 29), "age20_39_share": sh(20, 39),
                         "age65plus_share": sh(65, 200)}).rename_axis("la_code").reset_index()


def urban():
    g = pd.read_excel(PILOT_RAW / "cfc_migration" / "Input workbooks" / "LAtoPUA2024.xlsx").iloc[:, :8]
    g.columns = ["la_code", "la_name", "region", "country", "pua", "combined_authority", "super_region",
                 "urban_region"]
    g = g.dropna(subset=["la_code"]).drop_duplicates("la_code")
    g["urban_pua"] = g.pua.astype(str).str.strip() != ":"
    return g[["la_code", "pua", "urban_pua", "combined_authority"]]


def gardens():
    f = PILOT_RAW / "ons_gardens" / "osprivateoutdoorspacereferencetables.xlsx"
    d = pd.read_excel(f, sheet_name="LAD gardens", header=None, skiprows=2)
    ncode = 4
    tot = ncode + 2 + 6 + 7  # id columns, houses block (6), flats block (7), then total block (as 70_controls.py)
    d = d.iloc[:, [ncode, tot, tot + 1]]
    d.columns = ["code", "addresses", "addresses_with_pos"]
    d = d[d.code.astype(str).str.match(r"^[EW]0[6789]")].copy()
    d["la_code"] = d.code.replace(OLD_TO_NEW)
    d["garden_merged_from_districts"] = d.code != d.la_code
    g = d.groupby("la_code").agg(addresses=("addresses", "sum"), addresses_with_pos=("addresses_with_pos", "sum"),
                                 garden_merged_from_districts=("garden_merged_from_districts", "any"))
    g["garden_share"] = g.addresses_with_pos / g.addresses
    return g.reset_index()[["la_code", "garden_share", "garden_merged_from_districts"]]


def private_rent():
    url = (f"{NOMIS}/NM_2072_1.data.csv?geography=TYPE424&c2021_tenure_9=0,1004&measures=20100"
           "&select=geography_code,c2021_tenure_9,obs_value")
    t = pd.read_csv(download(url, RAW / "nomis" / "census2021_ts054_tenure_TYPE424.csv"))
    t = t.pivot(index="GEOGRAPHY_CODE", columns="C2021_TENURE_9", values="OBS_VALUE")
    return pd.DataFrame({"households_2021": t[0], "private_rent_share_2021": t[1004] / t[0]}).rename_axis(
        "la_code").reset_index()


def main():
    lk = lookup()
    bc, status = business_counts(lk)
    x = (lk.merge(bc, on="la_code", how="left").merge(age_shares(lk), on="la_code", how="left")
         .merge(urban(), on="la_code", how="left").merge(gardens(), on="la_code", how="left")
         .merge(private_rent(), on="la_code", how="left"))
    x["london"] = x.region == "London"
    x["city_of_london"] = x.la_code == "E09000001"
    assert len(x) == 318
    assert np.allclose(x.pop_mid2019, x.pop_mid2019_sya_sum), "single-age population does not sum to total"
    x = x.drop(columns="pop_mid2019_sya_sum")
    x.to_csv(CLEAN / "b3_la_crosssection.csv", index=False)
    print("UKBC status:", status)
    print(x.isna().sum()[x.isna().sum() > 0].to_string())
    print(x[["per1k_IR", "log_per1k_IR", "z_log_per1k_IR", "garden_share", "private_rent_share_2021"]].describe()
          .round(3).to_string())
    print(x.nlargest(5, "per1k_IR")[["la_name", "per1k_IR", "z_log_per1k_IR"]].to_string(index=False))


if __name__ == "__main__":
    main()
