"""S1 task 1: LA controls on April 2023 LAD boundaries (318 LAs in England and Wales).

Definitions are the pilot's (scripts/70_controls.py and scripts/96_age_ddd.py census_controls), applied to
all 348 England and Wales LAs of the 2011 Census (Nomis TYPE464, post-2013 codes) and then aggregated to
2023 LADs by summing counts (never averaging shares):
  telework_share     QS606EW minor groups x ONS 2020 homeworking score: employment-weighted share of each
                     SOC 2010 minor group in unit groups scoring below 1.5, weighted by residents in employment
  garden_share       ONS April 2020 private outdoor space, all addresses (houses + flats)
  flat_share         QS402EW households in purpose-built flats, converted/shared houses, commercial buildings
  private_rent_share KS402EW private rented (cell 300) / all households
  age20_39_share     QS103EW ages 20-39 / all usual residents
  student_share      KS501EW schoolchildren and full-time students aged 18+ (cell 9) / residents aged 16+
X_* are standardised across the 316 LAs excluding City of London and the Isles of Scilly.
"""
import numpy as np
import pandas as pd

from ext_config import CLEAN, PILOT_RAW, PROJECT, RAW

IN11 = RAW / "s1" / "census2011_la"
SMALL = {"E09000001", "E06000053"}
TELEWORK_THRESHOLD = 1.5

# Every 2011 Census LA (post-2013 codes) that is not itself a 2023 LAD, with its successor. Chains are
# followed (Taunton Deane -> Somerset West and Taunton -> Somerset). All are whole-district unions.
SUCCESSOR = {
    # 2019: Dorset, Suffolk, Somerset West and Taunton
    "E06000028": "E06000058", "E06000029": "E06000058", "E07000048": "E06000058",
    "E07000049": "E06000059", "E07000050": "E06000059", "E07000051": "E06000059", "E07000052": "E06000059",
    "E07000053": "E06000059",
    "E07000201": "E07000245", "E07000204": "E07000245", "E07000205": "E07000244", "E07000206": "E07000244",
    "E07000190": "E07000246", "E07000191": "E07000246",
    # 2020: Buckinghamshire
    "E07000004": "E06000060", "E07000005": "E06000060", "E07000006": "E06000060", "E07000007": "E06000060",
    # 2021: Northamptonshire
    "E07000150": "E06000061", "E07000152": "E06000061", "E07000153": "E06000061", "E07000156": "E06000061",
    "E07000151": "E06000062", "E07000154": "E06000062", "E07000155": "E06000062",
    # 2023: Cumbria, North Yorkshire, Somerset
    "E07000026": "E06000063", "E07000028": "E06000063", "E07000029": "E06000063",
    "E07000027": "E06000064", "E07000030": "E06000064", "E07000031": "E06000064",
    **{f"E070001{i}": "E06000065" for i in range(63, 70)},
    "E07000187": "E06000066", "E07000188": "E06000066", "E07000189": "E06000066", "E07000246": "E06000066",
}


def to_lad23(code: str) -> str:
    while code in SUCCESSOR:
        code = SUCCESSOR[code]
    return code


def frame() -> pd.DataFrame:
    x = pd.read_csv(CLEAN / "b3_la_crosssection.csv", usecols=["la_code", "la_name", "region", "log_per1k_IR"])
    assert len(x) == 318
    return x


def lookup(la2011: pd.Series, lad23: set) -> pd.DataFrame:
    lk = pd.DataFrame({"la2011_code": sorted(la2011.unique())})
    lk["la_code"] = lk.la2011_code.map(to_lad23)
    bad = set(lk.la_code) - lad23
    assert not bad, f"2011 LAs with no 2023 successor: {bad}"
    assert set(lk.la_code) == lad23, f"2023 LADs with no 2011 parent: {lad23 - set(lk.la_code)}"
    return lk


def telework_minor_groups() -> pd.DataFrame:
    """Identical to the pilot (scripts/70_controls.py telework_minor_groups)."""
    f = PILOT_RAW / "ons_homeworking" / "ons_whichjobscanbedonefromhome_2020_data.xlsx"
    d = pd.read_excel(f, header=2).iloc[:, 1:]
    d.columns = ["soc4", "title", "exposure", "interaction", "location", "physical", "tools", "score",
                 "median_pay", "emp", "pct_female", "pct_55plus", "pct_bame"]
    d = d[pd.to_numeric(d.soc4, errors="coerce").notna()].copy()
    d["soc4"] = d.soc4.astype(int)
    d[["score", "emp"]] = d[["score", "emp"]].apply(pd.to_numeric, errors="coerce")
    d["soc3"] = d.soc4 // 10
    g = d.groupby("soc3").apply(lambda x: pd.Series({
        "tw_share_main": (x.emp * (x.score < TELEWORK_THRESHOLD)).sum() / x.emp.sum(),
        "tw_share_alt": (x.emp * (x.score < 2.0)).sum() / x.emp.sum(),
        "mean_score": (x.emp * x.score).sum() / x.emp.sum()}), include_groups=False)
    return g.reset_index()


def counts_2011() -> pd.DataFrame:
    """Numerators and denominators for each 2011 LA (pilot cell definitions)."""
    age = pd.read_csv(IN11 / "qs103ew_age_la2011_ew.csv")
    tot = age[age.C_AGE == 0].set_index("GEOGRAPHY_CODE").OBS_VALUE
    a2039 = age[age.C_AGE.between(21, 40)].groupby("GEOGRAPHY_CODE").OBS_VALUE.sum()  # codes 21..40 = ages 20..39

    ten = pd.read_csv(IN11 / "ks402ew_tenure_la2011_ew.csv").pivot_table(
        index="GEOGRAPHY_CODE", columns="CELL", values="OBS_VALUE")
    stu = pd.read_csv(IN11 / "ks501ew_students_la2011_ew.csv").pivot_table(
        index="GEOGRAPHY_CODE", columns="CELL", values="OBS_VALUE")
    acc = pd.read_csv(IN11 / "qs402ew_accommodation_la2011_ew.csv").pivot_table(
        index="GEOGRAPHY_CODE", columns="DWELLING_TYPE", values="OBS_VALUE")
    assert ((acc[[7, 8, 9]].sum(axis=1) - acc[6]).abs() == 0).all(), "flat subtypes do not sum to flats total"

    tw = telework_minor_groups()
    occ = pd.read_csv(IN11 / "qs606ew_occupation_la2011_ew.csv")
    occ["soc3"] = pd.to_numeric(occ.CELL_NAME.str.extract(r"^(\d{3})\.")[0], errors="coerce")
    minor = occ[occ.soc3.notna()].merge(tw, on="soc3", how="left")
    assert minor.tw_share_main.notna().all()
    emp = minor.groupby("GEOGRAPHY_CODE").OBS_VALUE.sum()
    check = occ[occ.CELL == 0].set_index("GEOGRAPHY_CODE").OBS_VALUE
    assert ((emp - check).abs() == 0).all(), "minor groups do not sum to total employed"
    wsum = lambda col: minor.assign(v=minor.OBS_VALUE * minor[col]).groupby("GEOGRAPHY_CODE").v.sum()

    c = pd.DataFrame({
        "pop_2011": tot, "pop_20_39": a2039,
        "households_2011": ten[0], "hh_private_rent": ten[300],
        "hh_accom_total": acc[0], "hh_flats": acc[[7, 8, 9]].sum(axis=1),
        "pop16plus_2011": stu[0], "students_18plus": stu[9],
        "employed_2011": emp, "emp_teleworkable": wsum("tw_share_main"),
        "emp_teleworkable_alt2": wsum("tw_share_alt"), "emp_x_score": wsum("mean_score")})
    assert len(c) == 348 and c.notna().all().all()
    c.index.name = "la2011_code"
    return c.reset_index()


def gardens() -> pd.DataFrame:
    """April 2020 LAD sheet: address counts summed to 2023 LADs (as in b3_crosssection.py)."""
    f = PILOT_RAW / "ons_gardens" / "osprivateoutdoorspacereferencetables.xlsx"
    d = pd.read_excel(f, sheet_name="LAD gardens", header=None, skiprows=2)
    tot = 4 + 2 + 6 + 7  # id columns, houses block (6), flats block (7), then total block (as 70_controls.py)
    d = d.iloc[:, [4, tot, tot + 1]]
    d.columns = ["code", "addresses", "addresses_with_pos"]
    d = d[d.code.astype(str).str.match(r"^[EW]0[6789]")].copy()
    d["la_code"] = d.code.map(to_lad23)
    g = d.groupby("la_code").agg(addresses=("addresses", "sum"), addresses_with_pos=("addresses_with_pos", "sum"),
                                 n_garden_districts=("code", "size"))
    return g.reset_index()


def zscore(s: pd.Series, mask: pd.Series) -> pd.Series:
    return (s - s[mask].mean()) / s[mask].std()


SHARES = ["telework_share", "garden_share", "flat_share", "private_rent_share", "age20_39_share", "student_share"]


def main():
    fr = frame()
    c11 = counts_2011()
    lk = lookup(c11.la2011_code, set(fr.la_code))
    lk = lk.merge(c11[["la2011_code", "pop_2011"]], on="la2011_code")
    lk.to_csv(CLEAN / "s1_lookup_la2011_lad23.csv", index=False)

    agg = c11.merge(lk[["la2011_code", "la_code"]], on="la2011_code").drop(columns="la2011_code")
    n11 = agg.groupby("la_code").size().rename("n_la2011")
    agg = agg.groupby("la_code").sum().join(n11)
    agg = agg.join(gardens().set_index("la_code"))
    agg["telework_share"] = agg.emp_teleworkable / agg.employed_2011
    agg["telework_share_alt2"] = agg.emp_teleworkable_alt2 / agg.employed_2011
    agg["homework_score_mean"] = agg.emp_x_score / agg.employed_2011
    agg["garden_share"] = agg.addresses_with_pos / agg.addresses
    agg["flat_share"] = agg.hh_flats / agg.hh_accom_total
    agg["private_rent_share"] = agg.hh_private_rent / agg.households_2011
    agg["age20_39_share"] = agg.pop_20_39 / agg.pop_2011
    agg["student_share"] = agg.students_18plus / agg.pop16plus_2011

    out = fr.drop(columns="log_per1k_IR").merge(agg.reset_index(), on="la_code", how="left")
    assert len(out) == 318 and out[SHARES].notna().all().all()
    mask = ~out.la_code.isin(SMALL)
    for v in SHARES:
        out[f"X_{v}"] = zscore(out[v], mask)
    out["excluded_from_z"] = ~mask
    keep = (["la_code", "la_name", "region"] + SHARES + [f"X_{v}" for v in SHARES]
            + ["telework_share_alt2", "homework_score_mean", "excluded_from_z", "n_la2011", "n_garden_districts",
               "pop_2011", "households_2011", "employed_2011", "pop16plus_2011", "addresses"])
    out = out[keep]
    out.to_csv(CLEAN / "s1_controls_la2023.csv", index=False)

    # London validation against the pilot's files
    pv = pd.read_csv(PROJECT / "data" / "clean" / "event_study_borough_vars.csv")
    ps = pd.read_csv(PROJECT / "data" / "clean" / "borough_student_hospitality_2011.csv")
    pil = pv[["la_code", "telework_share", "garden_share", "private_rent_share", "age20_39_share"]].merge(
        ps[["la_code", "student_share"]], on="la_code")
    m = pil.merge(out, on="la_code", suffixes=("_pilot", ""))
    rows = []
    for v in ["telework_share", "garden_share", "private_rent_share", "age20_39_share", "student_share"]:
        diff = (m[v] - m[f"{v}_pilot"]).abs()
        rows.append({"variable": v, "n_boroughs": len(m), "max_abs_diff": diff.max(),
                     "corr": np.corrcoef(m[v], m[f"{v}_pilot"])[0, 1]})
    val = pd.DataFrame(rows)
    val.to_csv(CLEAN / "s1_validation_london.csv", index=False)
    print(val.to_string(index=False))
    print(out.loc[mask, SHARES].describe().round(3).to_string())
    print("2023 LADs built from >1 2011 LA:", (out.n_la2011 > 1).sum())


if __name__ == "__main__":
    main()
