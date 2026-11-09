"""S1 task 2: controls for the 7,264 2021 MSOAs of England and Wales, from Census 2021 and ONS April 2020
garden data. Closest available analogues of the pilot's 2011 definitions:
  telework_share      TS063 SOC 2020 major groups. Main rule: share of residents in employment in major
                      groups whose employment-weighted mean ONS 2020 homeworking score (SOC 2010 unit groups,
                      ONS employment weights) is below 1.5. Alternative (telework_share_frac): each major
                      group weighted by its share of employment in unit groups scoring below 1.5 (the pilot's
                      formula at major-group resolution).
  garden_share        ONS April 2020 MSOA (2011) private outdoor space, all addresses, moved to 2021 MSOAs
                      with postcode weights from the NSPL (2011 MSOA x 2021 MSOA of each small-user postcode
                      live in April 2020); counts are apportioned, then the share is formed.
  flat_share          TS044: purpose-built flats + converted/shared house + other converted building +
                      commercial building, over all households
  private_rent_share  TS054: private rented (landlord/agency + other) over all households
  age20_39_share      TS007A: ages 20-39 over all usual residents
  student_share       ONS custom API, economic activity (7a) x age (7a): full-time students aged 18+
                      (economically active or inactive) over usual residents aged 16+
"""
import zipfile

import numpy as np
import pandas as pd

from ext_config import CLEAN, PILOT_RAW, RAW

IN21 = RAW / "s1" / "census2021_bulk"
API = RAW / "s1" / "ons_api"
MIG = RAW / "census2021_migration"
SHARES = ["telework_share", "garden_share", "flat_share", "private_rent_share", "age20_39_share", "student_share"]
THRESH = 1.5
APRIL_2020 = 202004


def ts(t: str) -> pd.DataFrame:
    d = pd.read_csv(IN21 / f"census2021-{t}" / f"census2021-{t}-msoa.csv")
    return d.rename(columns={"geography code": "msoa21cd"}).set_index("msoa21cd")


def homework_major() -> pd.DataFrame:
    f = PILOT_RAW / "ons_homeworking" / "ons_whichjobscanbedonefromhome_2020_data.xlsx"
    d = pd.read_excel(f, header=2).iloc[:, [1, 8, 10]]
    d.columns = ["soc4", "score", "emp"]
    d = d.apply(pd.to_numeric, errors="coerce").dropna(subset=["soc4"])
    d["major"] = (d.soc4 // 1000).astype(int)
    g = d.groupby("major").apply(lambda x: pd.Series({
        "n_unit_groups": len(x), "emp": x.emp.sum(),
        "mean_score": (x.emp * x.score).sum() / x.emp.sum(),
        "tw_frac": (x.emp * (x.score < THRESH)).sum() / x.emp.sum()}), include_groups=False)
    g["teleworkable_major"] = g.mean_score < THRESH
    return g


def telework(hw: pd.DataFrame) -> pd.DataFrame:
    o = ts("ts063")
    tot = o.iloc[:, 2]
    groups = o.iloc[:, 3:12]
    assert [int(c.split(": ")[1].split(".")[0]) for c in groups.columns] == list(range(1, 10))
    groups.columns = range(1, 10)
    tw_major = [m for m in range(1, 10) if hw.loc[m, "teleworkable_major"]]
    return pd.DataFrame({"employed_2021": tot,
                         "emp_teleworkable": groups[tw_major].sum(axis=1),
                         "emp_teleworkable_frac": groups.mul(hw.tw_frac, axis=1).sum(axis=1)})


def students() -> pd.DataFrame:
    d = pd.read_csv(API / "msoa_economic_activity_status_7a_resident_age_7a.csv")
    # econ7: -8 does not apply, 1/2 active excl. FT students, 3/4 active FT students, 5 inactive excl. FT
    # students, 6 inactive FT students. age7: 1 <=4, 2 5-15, 3 16-17, 4 18-20, 5 21-24, 6 25-29, 7 30+
    p16 = d[d.age7 >= 3].groupby("msoa21cd").obs.sum()
    s18 = d[(d.age7 >= 4) & d.econ7.isin([3, 4, 6])].groupby("msoa21cd").obs.sum()
    s16 = d[(d.age7 >= 3) & d.econ7.isin([3, 4, 6])].groupby("msoa21cd").obs.sum()
    na16 = d[(d.age7 >= 3) & (d.econ7 == -8)].obs.sum()
    assert na16 == 0, f"'does not apply' among residents aged 16+: {na16}"
    return pd.DataFrame({"pop16plus_2021": p16, "students_18plus": s18, "students_16plus_api": s16})


def nspl_weights() -> pd.DataFrame:
    """2011 MSOA -> 2021 MSOA weights: shares of each 2011 MSOA's small-user postcodes live in April 2020."""
    out = RAW / "s1" / "nspl_msoa11_msoa21_postcodes.csv"
    if not out.exists():
        z11 = zipfile.ZipFile(PILOT_RAW / "nspl" / "NSPL_2011CENSUS_AUG_2024.zip")
        with z11.open("Data/NSPL_AUG_2024_UK.csv") as fh:
            a = pd.read_csv(fh, usecols=["pcd", "dointr", "doterm", "usertype", "msoa11"], dtype=str)
        z21 = zipfile.ZipFile(PILOT_RAW / "nspl" / "NSPL_AUG_2026.zip")
        with z21.open("Data/NSPL_AUG_2026_UK.csv") as fh:
            b = pd.read_csv(fh, usecols=["pcd7", "msoa21cd"], dtype=str)
        a = a[a.msoa11.str.match(r"^[EW]02", na=False) & (a.usertype == "0")]
        a = a[(a.dointr.astype(int) <= APRIL_2020) & (a.doterm.isna() | (a.doterm.fillna("0").astype(int) > APRIL_2020))]
        m = a.merge(b.rename(columns={"pcd7": "pcd"}), on="pcd", how="left")
        print("postcodes:", len(m), "without 2021 MSOA:", m.msoa21cd.isna().sum())
        m = m[m.msoa21cd.str.match(r"^[EW]02", na=False)]
        w = m.groupby(["msoa11", "msoa21cd"]).size().rename("n_postcodes").reset_index()
        w.to_csv(out, index=False)
    w = pd.read_csv(out)
    w["w"] = w.n_postcodes / w.groupby("msoa11").n_postcodes.transform("sum")
    return w


def gardens() -> pd.DataFrame:
    f = PILOT_RAW / "ons_gardens" / "osprivateoutdoorspacereferencetables.xlsx"
    g = pd.read_excel(f, sheet_name="MSOA gardens", header=None, skiprows=2).iloc[:, [6, 21, 22]]
    g.columns = ["msoa11", "addresses", "addresses_with_pos"]
    g = g[g.msoa11.astype(str).str.match(r"^[EW]02")].dropna()
    w = nspl_weights()
    miss = set(g.msoa11) - set(w.msoa11)
    assert not miss, f"2011 MSOAs without postcodes: {miss}"
    m = w.merge(g, on="msoa11")
    m["addr"] = m.addresses * m.w
    m["pos"] = m.addresses_with_pos * m.w
    m["main"] = m.groupby("msoa21cd").addr.transform("max") == m.addr
    out = m.groupby("msoa21cd").agg(addresses=("addr", "sum"), addresses_with_pos=("pos", "sum"),
                                    n_msoa11=("msoa11", "size"))
    out["garden_share"] = out.addresses_with_pos / out.addresses
    # share of the 2021 MSOA's apportioned addresses that comes from 2011 MSOAs it fully contains or equals
    m["whole"] = m.w > 0.999
    out["garden_share_whole_msoa11"] = m.assign(a=m.addr * m.whole).groupby("msoa21cd").a.sum() / out.addresses
    return out


def zscore(s):
    return (s - s.mean()) / s.std()


def main():
    base = pd.read_csv(CLEAN / "msoa21_amenity_access_ew.csv", usecols=["msoa21cd", "lad23cd"])
    reg = pd.read_csv(CLEAN / "b3_la_crosssection.csv", usecols=["la_code", "region"]).rename(
        columns={"la_code": "lad23cd"})
    base = base.merge(reg, on="lad23cd", how="left").set_index("msoa21cd")
    assert len(base) == 7264 and base.region.notna().all()

    hw = homework_major()
    hw.to_csv(CLEAN / "s1_homework_score_soc2010_major.csv")
    print(hw.round(3).to_string())

    acc = ts("ts044")
    flats = [c for c in acc.columns if any(k in c for k in ["purpose-built", "converted", "commercial"])]
    assert len(flats) == 4, flats
    ten = ts("ts054")
    age =pd.read_csv(MIG / "census2021-ts007a" / "census2021-ts007a-msoa.csv").rename(
        columns={"geography code": "msoa21cd"}).set_index("msoa21cd")
    a2039 = [f"Age: Aged {a} to {a + 4} years" for a in (20, 25, 30, 35)]

    c = pd.DataFrame({
        "households_2021": acc["Accommodation type: Total: All households"],
        "hh_flats": acc[flats].sum(axis=1),
        "hh_total_tenure": ten["Tenure of household: Total: All households"],
        "hh_private_rent": ten["Tenure of household: Private rented"],
        "pop_2021": age["Age: Total"], "pop_20_39": age[a2039].sum(axis=1)})
    c = c.join(telework(hw)).join(students()).join(gardens())
    c["students_16plus_ts066"] = ts("ts066")[["Economic activity status: Economically active and a full-time student",
                                             "Economic activity status: Economically inactive: Student"]].sum(axis=1)

    c["telework_share"] = c.emp_teleworkable / c.employed_2021
    c["telework_share_frac"] = c.emp_teleworkable_frac / c.employed_2021
    c["flat_share"] = c.hh_flats / c.households_2021
    c["private_rent_share"] = c.hh_private_rent / c.hh_total_tenure
    c["age20_39_share"] = c.pop_20_39 / c.pop_2021
    c["student_share"] = c.students_18plus / c.pop16plus_2021

    out = base.join(c, how="left")
    print("missing by share:", out[SHARES].isna().sum().to_dict())
    for v in SHARES + ["telework_share_frac"]:
        out[f"X_{v}"] = zscore(out[v])
    keep = (["lad23cd", "region"] + SHARES + [f"X_{v}" for v in SHARES]
            + ["telework_share_frac", "X_telework_share_frac", "garden_share_whole_msoa11", "n_msoa11",
               "employed_2021", "emp_teleworkable", "emp_teleworkable_frac", "addresses", "addresses_with_pos",
               "households_2021", "hh_flats", "hh_total_tenure", "hh_private_rent", "pop_2021", "pop_20_39",
               "pop16plus_2021", "students_18plus", "students_16plus_api", "students_16plus_ts066"])
    out = out[keep].reset_index()
    out.to_csv(CLEAN / "s1_controls_msoa21.csv", index=False)
    print(out[SHARES + ["telework_share_frac"]].describe().round(3).to_string())
    print("API vs TS066 FT students 16+: total ratio", round(out.students_16plus_api.sum() / out.students_16plus_ts066.sum(), 4),
          "corr", round(np.corrcoef(out.students_16plus_api, out.students_16plus_ts066)[0, 1], 4))


if __name__ == "__main__":
    main()
