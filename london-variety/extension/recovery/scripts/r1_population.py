"""R1. Population stocks by age, 2023 local authorities and 2021 MSOAs, England and Wales.

Local authorities: ONS "Population estimates and components of change, detailed time series 2011 to 2025"
  (MYE25, published 29 July 2026), sheet MYEB1, single year of age 0-90+, by sex, mid-2011 to mid-2025, April 2023
  LADs, consistent with Census 2021 (mid-2012 to mid-2020 rebased; mid-2022 to mid-2024 revised for international
  migration). URL in MYE below; the copy already downloaded for the national extension is reused.
MSOAs: Nomis NM_2014_1 "Population estimates - small area (2021 based) by single year of age", 2021 MSOAs
  (geography TYPE152), persons, mid-2011 to mid-2024 (latest available; first released 20 Jun 2024, last updated
  7 Nov 2025). Single years 20-34 (codes 121-135) and the bands 50-64 (208) and 65+ (209), plus all ages (200).
Groups: 25-34, 20-29, 50 and over.
Check: MSOA sums by LA against the LA series, every year and group.

Outputs (extension/recovery/data/): r1_pop_la.csv, r1_pop_msoa.csv, r1_check_msoa_vs_la.csv
"""
import time

import numpy as np
import pandas as pd
import requests

from rc_common import CLEAN, DATA, GROUPS, PILOT_RAW, RAW, RRAW, UA

MYE = ("https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/populationandmigration/populationestimates/"
       "datasets/estimatesofthepopulationforenglandandwales/mid2011tomid2025detailedtimeseries/"
       "myebtablesenglandwales20112025.xlsx")
NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset/NM_2014_1.data.csv"
AGES = list(range(121, 136)) + [208, 209, 200]
YEARS_MSOA = range(2011, 2025)


def la_series():
    f = PILOT_RAW / "ons_mye" / "myebtablesenglandwales20112025.xlsx"
    if not f.exists():
        from ext_config import download
        f = download(MYE, RAW / "ons_mye" / "myebtablesenglandwales20112025.xlsx")
    x = pd.read_excel(f, sheet_name="MYEB1", header=1)
    pc = [c for c in x.columns if str(c).startswith("population_")]
    long = x.melt(id_vars=["ladcode23", "laname23", "country", "sex", "age"], value_vars=pc, var_name="v", value_name="n")
    long["year"] = long.v.str[-4:].astype(int)
    rows = []
    for g, ages in GROUPS.items():
        s = long[long.age.isin(list(ages))].groupby(["ladcode23", "laname23", "country", "year"]).n.sum().rename(g)
        rows.append(s)
    tot = long.groupby(["ladcode23", "laname23", "country", "year"]).n.sum().rename("all_ages")
    out = pd.concat(rows + [tot], axis=1).reset_index().rename(columns={"ladcode23": "lad23cd", "laname23": "la_name"})
    return out


def fetch_year(y):
    dest = RRAW / f"nm2014_msoa21_{y}.csv"
    if dest.exists() and dest.stat().st_size > 1000:
        return pd.read_csv(dest)
    parts, off = [], 0
    while True:
        url = (f"{NOMIS}?geography=TYPE152&date={y}&gender=0&c_age={','.join(map(str, AGES))}&measures=20100"
               f"&select=date_name,geography_code,c_age,obs_value&recordoffset={off}&recordlimit=25000")
        for k in range(5):
            try:
                r = requests.get(url, headers=UA, timeout=300)
                r.raise_for_status()
                break
            except requests.RequestException:
                time.sleep(5 * (k + 1))
        else:
            raise SystemExit(f"Nomis blocked for {y} offset {off}")
        from io import StringIO
        p = pd.read_csv(StringIO(r.text))
        parts.append(p)
        if len(p) < 25000:
            break
        off += 25000
    d = pd.concat(parts, ignore_index=True)
    d.to_csv(dest, index=False)
    return d


def msoa_series():
    rows = []
    for y in YEARS_MSOA:
        d = fetch_year(y)
        assert d.GEOGRAPHY_CODE.nunique() == 7264 and len(d) == 7264 * len(AGES), (y, len(d))
        w = d.pivot_table(index="GEOGRAPHY_CODE", columns="C_AGE", values="OBS_VALUE")
        o = pd.DataFrame({"msoa21cd": w.index, "year": y,
                          "a2534": w[[100 + 1 + a for a in range(25, 35)]].sum(axis=1).values,
                          "a2029": w[[100 + 1 + a for a in range(20, 30)]].sum(axis=1).values,
                          "a50p": (w[208] + w[209]).values, "all_ages": w[200].values})
        rows.append(o)
        print(y, "ok", flush=True)
    m = pd.concat(rows, ignore_index=True)
    lk = pd.read_csv(CLEAN / "msoa21_ew_lookup_pwc.csv")[["msoa21cd", "lad23cd"]]
    return m.merge(lk, on="msoa21cd", how="left")


def main():
    la = la_series()
    la.to_csv(DATA / "r1_pop_la.csv", index=False)
    m = msoa_series()
    assert m.lad23cd.notna().all()
    m.to_csv(DATA / "r1_pop_msoa.csv", index=False)
    s = m.groupby(["lad23cd", "year"])[["a2534", "a2029", "a50p", "all_ages"]].sum()
    j = s.join(la.set_index(["lad23cd", "year"])[["a2534", "a2029", "a50p", "all_ages"]], rsuffix="_la", how="inner")
    rows = []
    for g in ["a2534", "a2029", "a50p", "all_ages"]:
        rel = (j[g] / j[f"{g}_la"] - 1).abs()
        for y, rr in rel.groupby(level="year"):
            rows.append(dict(group=g, year=y, n_la=len(rr), max_abs_rel_diff=rr.max(), mean_abs_rel_diff=rr.mean()))
    c = pd.DataFrame(rows)
    c.to_csv(DATA / "r1_check_msoa_vs_la.csv", index=False)
    pd.set_option("display.width", 200)
    print(c.groupby("group")[["max_abs_rel_diff", "mean_abs_rel_diff"]].max().to_string())
    print(f"LA series: {la.lad23cd.nunique()} LADs, years {la.year.min()}-{la.year.max()}; "
          f"MSOA series: {m.msoa21cd.nunique()} MSOAs, years {m.year.min()}-{m.year.max()}")
    ew = la.groupby("year")[["a2534", "a2029", "a50p"]].sum() / 1e6
    print("England and Wales totals (millions)\n", ew.round(3).to_string())


if __name__ == "__main__":
    main()
