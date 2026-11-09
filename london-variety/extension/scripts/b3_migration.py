"""B3 migration: national LA x year internal migration by age group, England and Wales, 2023 LAD codes.

Source: ONS internal migration detailed estimates (origin-destination LA x single year of age x sex), years ending
June 2015-2025, 2023 LA boundaries; the same workbooks the pilot read (PILOT_RAW/ons_internal_migration).
Definitions follow scripts/10_migration.py, 94_migration_age.py and 96_age_ddd.py:
  - year t = year ending 30 June t; age = age at 30 June of year t (ONS definition);
  - groups 20-29, 20-24, 25-29, 30-39, family proxy (0-15 plus 30-49), 50+, all ages;
  - rates per 1,000 mid-2019 residents of the same group (ONS mid-2019 estimates rebased to Census 2021,
    Nomis NM_2002_1, single year of age, codes 101-191 = ages 0-89 and 90+).
National analogue of the pilot outcome: net moves with all other LAs (net_all). The London pilot measure (moves
crossing the Greater London boundary) is generalised as moves crossing the LA's own region boundary (net_xregion);
for London boroughs net_xregion is exactly the pilot's outcome. Scotland and Northern Ireland appear in the files
only as country-level counterparts (S92000003, N92000002); net_ew excludes them.
"""
import numpy as np
import pandas as pd

from ext_config import CLEAN, PILOT_RAW, RAW, download

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
YEARS = range(2015, 2026)
SCOT, NI = "S92000003", "N92000002"
GROUPS = {"all": [range(0, 200)], "age20_29": [range(20, 30)], "age20_24": [range(20, 25)],
          "age25_29": [range(25, 30)], "age30_39": [range(30, 40)],
          "family_0_15_30_49": [range(0, 16), range(30, 50)], "age50plus": [range(50, 200)]}
AGG = RAW / "ons_internal_migration_agg"
BIG = RAW.parent / "clean"  # large clean outputs live outside OneDrive
BIG.mkdir(parents=True, exist_ok=True)
AGG.mkdir(parents=True, exist_ok=True)


def lookup() -> pd.DataFrame:
    """ONS 2023-boundary LA to region lookup (318 E&W LAs), as in pilot config.la_region_lookup."""
    df = pd.read_excel(PILOT_RAW / "ons_internal_migration" / "lasregionew2023lookup.xlsx", header=None)
    hdr = df.index[df.apply(lambda r: r.astype(str).str.contains("LA code", case=False).any(), axis=1)][0]
    df.columns = df.iloc[hdr].astype(str).str.strip()
    df = df.iloc[hdr + 1:].dropna(how="all")
    code = next(c for c in df.columns if "LA code" in c)
    name = next(c for c in df.columns if "LA name" in c)
    reg = next(c for c in df.columns if "Region name" in c)
    df = df[[code, name, reg]].set_axis(["la_code", "la_name", "region"], axis=1).reset_index(drop=True)
    # two codes carry a trailing stray character in the ONS workbook (North and West Northamptonshire)
    df["la_code"] = df.la_code.astype(str).str.extract(r"([EW]\d{8})")[0]
    df["la_name"] = df.la_name.astype(str).str.replace(r"[^\w\s,.'&()-]", "", regex=True).str.strip()
    df["region"] = df.region.astype(str).str.strip().replace({"East": "East of England"})
    assert df.la_code.notna().all() and df.la_code.nunique() == 318
    df["country"] = np.where(df.la_code.str.startswith("W"), "Wales", "England")
    return df


def read_year(y: int, lk: pd.DataFrame) -> pd.DataFrame:
    """LA x direction x counterpart region x single year of age, summed over sex. Cached as parquet."""
    cache = AGG / f"agg{y}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    f = PILOT_RAW / "ons_internal_migration" / f"detailedestimates{y}.xlsx"
    xl = pd.ExcelFile(f, engine="calamine")
    sheet = next(s for s in xl.sheet_names if "2023" in s and "LA" in s)
    d = pd.read_excel(xl, sheet, header=None)
    probe = d.head(15)
    hdr = probe.index[probe.apply(lambda r: r.astype(str).str.lower().isin(["outla", "inla"]).any(), axis=1)][0]
    d.columns = [str(c).strip().lower() for c in d.iloc[hdr]]
    d = d.iloc[hdr + 1:].reset_index(drop=True).copy()
    ages = [c for c in d.columns if c.startswith("age_")]
    d[ages] = d[ages].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    reg = dict(zip(lk.la_code, lk.region)) | {SCOT: "Scotland", NI: "Northern Ireland"}
    codes = set(reg)
    info = {"year": y, "sheet": sheet, "rows": len(d), "n_age_cols": len(ages), "max_age_col": ages[-1],
            "self_moves": int((d.outla == d.inla).sum()),
            "unknown_codes": sorted((set(d.outla) | set(d.inla)) - codes),
            "scot_ni_rows": int((d.outla.isin([SCOT, NI]) | d.inla.isin([SCOT, NI])).sum()),
            "scot_ni_both_rows": int((d.outla.isin([SCOT, NI]) & d.inla.isin([SCOT, NI])).sum()),
            "total_moves": float(d[ages].to_numpy().sum())}
    print(info, flush=True)
    pd.DataFrame([info]).astype(str).to_csv(AGG / f"info{y}.csv", index=False)
    assert not info["unknown_codes"], info["unknown_codes"]
    d = d[d.outla != d.inla].copy()
    parts = []
    for direction, own, cp in (("out", "outla", "inla"), ("in", "inla", "outla")):
        x = d[d[own].isin(lk.la_code)]
        g = x.assign(cp_region=x[cp].map(reg)).groupby([own, "cp_region"])[ages].sum()
        g.index.names = ["la_code", "cp_region"]
        g = g.stack().rename("moves").reset_index().rename(columns={"level_2": "age"})
        g["direction"] = direction
        parts.append(g)
    a = pd.concat(parts, ignore_index=True)
    a["age"] = pd.to_numeric(a.age.str.removeprefix("age_").str.replace("+", "", regex=False)).astype(int)
    a["year_ending_june"] = y
    a = a[a.moves != 0]
    a.to_parquet(cache)
    return a


def population(lk: pd.DataFrame) -> pd.DataFrame:
    """Mid-2019 population by single year of age, all LAs (Nomis NM_2002_1, TYPE424 = April 2023 LADs)."""
    url = (f"{NOMIS}/NM_2002_1.data.csv?geography=TYPE424&date=2019&gender=0"
           f"&c_age={','.join(str(c) for c in range(101, 192))}&measures=20100"
           "&select=geography_code,geography_name,c_age,obs_value")
    pages, off = [], 0
    while True:
        f = download(f"{url}&recordoffset={off}", RAW / "nomis" / "pages" / f"mye2019_single_age_TYPE424_{off}.csv")
        p = pd.read_csv(f)
        pages.append(p)
        if len(p) < 25000:
            break
        off += 25000
    p = pd.concat(pages, ignore_index=True).drop_duplicates()
    p.to_csv(RAW / "nomis" / "mye_population_mid2019_single_age_all_las.csv", index=False)
    p["age"] = p.C_AGE - 101  # 90 means 90+
    p = p[p.GEOGRAPHY_CODE.isin(lk.la_code)]
    assert p.GEOGRAPHY_CODE.nunique() == 318 and len(p) == 318 * 91, "population file incomplete"
    return p.rename(columns={"GEOGRAPHY_CODE": "la_code", "OBS_VALUE": "pop"})[["la_code", "age", "pop"]]


def in_group(age: pd.Series, g: str) -> np.ndarray:
    return np.logical_or.reduce([age.isin(list(r)) for r in GROUPS[g]])


def main():
    lk = lookup()
    a = pd.concat([read_year(y, lk) for y in YEARS], ignore_index=True)
    a = a.merge(lk[["la_code", "region"]], on="la_code")
    a["xregion"] = a.cp_region != a.region
    a["scotni"] = a.cp_region.isin(["Scotland", "Northern Ireland"])

    # single year of age file
    def comp(mask, name):
        return (a[mask].pivot_table(index=["la_code", "year_ending_june", "age"], columns="direction", values="moves",
                                    aggfunc="sum").add_prefix(name + "_"))
    sya = pd.concat([comp(slice(None), "all"), comp(~a.scotni, "ew"), comp(a.xregion, "xregion"),
                     comp(a.scotni, "scotni")], axis=1).fillna(0.0).reset_index()
    for c in ["all", "ew", "xregion", "scotni"]:
        sya[f"{c}_net"] = sya[f"{c}_in"] - sya[f"{c}_out"]
    sya.to_parquet(BIG / "b3_migration_la_year_single_age.parquet", index=False)

    pop = population(lk)
    rows = []
    full = pd.MultiIndex.from_product([lk.la_code, YEARS], names=["la_code", "year_ending_june"])
    for g in GROUPS:
        s = sya[in_group(sya.age, g)].groupby(["la_code", "year_ending_june"]).sum(numeric_only=True)
        s = s.drop(columns="age").reindex(full, fill_value=0.0).reset_index()
        s["group"] = g
        s["pop_mid2019"] = s.la_code.map(pop[in_group(pop.age, g)].groupby("la_code")["pop"].sum())
        rows.append(s)
    d = pd.concat(rows, ignore_index=True)
    for c in ["all", "ew", "xregion", "scotni"]:
        for k in ["in", "out", "net"]:
            d[f"{c}_{k}_per1k"] = d[f"{c}_{k}"] / d.pop_mid2019 * 1000
    d = lk.merge(d, on="la_code")
    d.insert(d.columns.get_loc("year_ending_june") + 1, "period",
             (d.year_ending_june - 1).map("mid-{}".format) + " to mid-" + d.year_ending_june.astype(str))
    d = d.sort_values(["group", "la_code", "year_ending_june"])
    d.to_csv(CLEAN / "b3_migration_la_year_by_age_group.csv", index=False)
    print(d.groupby("group")[["all_net", "ew_net", "scotni_net"]].sum().round(0))
    print(f"rows {len(d)}, LAs {d.la_code.nunique()}, years {d.year_ending_june.nunique()}")


if __name__ == "__main__":
    main()
