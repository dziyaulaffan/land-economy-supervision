"""Borough and MSOA (2011) controls: garden access, teleworkability, age 20-39, private renting.

a. Garden access: ONS "Access to gardens and public green space in Great Britain", April 2020
   edition, private outdoor space reference tables (OS AddressBase Plus, epoch 74). Share of all
   residential addresses (houses + flats) with private outdoor space.
b. Teleworkability: 2011 Census QS606EW occupation (SOC 2010 minor groups) of usual residents
   aged 16-74 in employment, combined with the ONS 2020 occupation-level "ability to homework"
   score ("Which jobs can be done from home?", 21 July 2020, SOC 2010 unit groups, O*NET based).
   The score runs 0-5 and higher means LESS able to work from home. ONS publishes no cut-off; a unit
   group counts as teleworkable when its score is below TELEWORK_THRESHOLD. Unit groups are
   aggregated to minor groups with ONS's total-in-employment weights.
c. Age and tenure: 2011 Census QS103EW (single year of age) and KS402EW (tenure).
"""
import pandas as pd

from config import CLEAN, RAW, download, london_frame

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
GARDEN_URL = ("https://www.ons.gov.uk/file?uri=/economy/environmentalaccounts/datasets/"
              "accesstogardensandpublicgreenspaceingreatbritain/accesstogardenspacegreatbritainapril2020/"
              "osprivateoutdoorspacereferencetables.xlsx")
WFH_URL = "https://www.ons.gov.uk/visualisations/dvc890/chart1/data.xlsx"
TELEWORK_THRESHOLD = 1.5   # main definition; 2.0 kept as a sensitivity column
LONDON_MSOA = "2013265927TYPE297"  # all 2011 MSOAs in London (Nomis region code)
GEOGS = {"la": "TYPE464", "msoa": LONDON_MSOA}  # TYPE464: LA districts prior to April 2015


def nomis(table: str, geo: str, extra: str, fname: str) -> pd.DataFrame:
    """Nomis returns at most 25,000 rows per call without an API key, so page with recordoffset."""
    geography = GEOGS[geo] if geo == "msoa" else ",".join(london_frame().la_code)
    url = (f"{NOMIS}/{table}.data.csv?geography={geography}&rural_urban=0&{extra}&measures=20100"
           "&select=geography_code,geography_name,cell,cell_name,c_age,c_age_name,obs_value")
    out = RAW / "census2011" / f"{fname}_{geo}.csv"
    if not out.exists():
        pages, offset = [], 0
        while True:
            f = download(f"{url}&recordoffset={offset}", RAW / "census2011" / "pages" / f"{fname}_{geo}_{offset}.csv")
            page = pd.read_csv(f)
            pages.append(page)
            if len(page) < 25000:
                break
            offset += 25000
        pd.concat(pages, ignore_index=True).to_csv(out, index=False)
    return pd.read_csv(out)


def gardens() -> dict:
    f = download(GARDEN_URL, RAW / "ons_gardens" / "osprivateoutdoorspacereferencetables.xlsx")
    out = {}
    for geo, sheet, ncode in (("la", "LAD gardens", 4), ("msoa", "MSOA gardens", 6)):
        d = pd.read_excel(f, sheet_name=sheet, header=None, skiprows=2)
        tot = ncode + 2 + 6 + 7  # id columns, houses block (6), flats block (7), then total block
        d = d.iloc[:, [ncode, tot, tot + 1, tot + 3]]
        d.columns = ["code", "addresses", "addresses_with_pos", "pct_pos_published"]
        d = d[d.code.astype(str).str.match(r"^E0[29]")]
        d["garden_share"] = d.addresses_with_pos / d.addresses
        out[geo] = d.set_index("code")[["garden_share", "addresses"]]
    return out


def telework_minor_groups() -> pd.DataFrame:
    f = download(WFH_URL, RAW / "ons_homeworking" / "ons_whichjobscanbedonefromhome_2020_data.xlsx")
    d = pd.read_excel(f, header=2).iloc[:, 1:]
    d.columns = ["soc4", "title", "exposure", "interaction", "location", "physical", "tools", "score",
                 "median_pay", "emp", "pct_female", "pct_55plus", "pct_bame"]
    d = d[pd.to_numeric(d.soc4, errors="coerce").notna()].copy()
    d["soc4"] = d.soc4.astype(int)
    d[["score", "emp"]] = d[["score", "emp"]].apply(pd.to_numeric, errors="coerce")
    d["soc3"] = d.soc4 // 10
    d.to_csv(CLEAN / "telework_ons2020_soc4.csv", index=False)
    g = d.groupby("soc3").apply(lambda x: pd.Series({
        "n_unit_groups": len(x),
        "emp_weight": x.emp.sum(),
        "tw_share_main": (x.emp * (x.score < TELEWORK_THRESHOLD)).sum() / x.emp.sum(),
        "tw_share_alt": (x.emp * (x.score < 2.0)).sum() / x.emp.sum(),
        "mean_score": (x.emp * x.score).sum() / x.emp.sum()}), include_groups=False)
    return g.reset_index()


def census_controls(geo: str, tw: pd.DataFrame) -> pd.DataFrame:
    age = nomis("NM_503_1", geo, "c_age=0,21...40", "qs103ew_age")
    tot = age[age.C_AGE == 0].set_index("GEOGRAPHY_CODE").OBS_VALUE
    a2039 = age[age.C_AGE.between(21, 40)].groupby("GEOGRAPHY_CODE").OBS_VALUE.sum()  # codes 21..40 = ages 20..39

    ten = nomis("NM_619_1", geo, "cell=0,300", "ks402ew_tenure")
    ten = ten.pivot_table(index="GEOGRAPHY_CODE", columns="CELL", values="OBS_VALUE")

    occ = nomis("NM_561_1", geo, "cell=0...124", "qs606ew_occupation")
    occ["soc3"] = pd.to_numeric(occ.CELL_NAME.str.extract(r"^(\d{3})\.")[0], errors="coerce")
    minor = occ[occ.soc3.notna()].merge(tw, on="soc3", how="left")
    assert minor.tw_share_main.notna().all(), f"minor groups without ONS score: {minor[minor.tw_share_main.isna()].soc3.unique()}"
    emp = minor.groupby("GEOGRAPHY_CODE").OBS_VALUE.sum()
    check = occ[occ.CELL == 0].set_index("GEOGRAPHY_CODE").OBS_VALUE
    assert ((emp - check).abs() <= 0).all(), "minor groups do not sum to total employed"
    wsum = lambda col: minor.assign(v=minor.OBS_VALUE * minor[col]).groupby("GEOGRAPHY_CODE").v.sum() / emp

    out = pd.DataFrame({
        "pop_2011": tot, "age20_39_share": a2039 / tot,
        "households_2011": ten[0], "private_rent_share": ten[300] / ten[0],
        "employed_residents_2011": emp, "telework_share": wsum("tw_share_main"),
        "telework_share_alt2": wsum("tw_share_alt"), "homework_score_mean": wsum("mean_score")})
    out.index.name = "code"
    return out


def main():
    tw = telework_minor_groups()
    tw.to_csv(CLEAN / "telework_ons2020_soc3.csv", index=False)
    g = gardens()

    la = census_controls("la", tw).join(g["la"][["garden_share"]])
    lon = london_frame().set_index("la_code").join(la).reset_index()
    assert lon[["garden_share", "telework_share", "age20_39_share", "private_rent_share"]].notna().all().all()
    lon.to_csv(CLEAN / "controls_borough.csv", index=False)

    ms = census_controls("msoa", tw).join(g["msoa"][["garden_share"]]).reset_index().rename(columns={"code": "msoa11_code"})
    ms.to_csv(CLEAN / "controls_msoa2011.csv", index=False)
    print(f"MSOAs: {len(ms)}, missing garden: {ms.garden_share.isna().sum()}")
    print(lon[["la_name", "london_zone", "garden_share", "telework_share", "age20_39_share",
               "private_rent_share"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
