"""B2: build MSOA and LA migrant inflow/outflow counts and rates from Census 2021 (address one year ago).

Inputs (raw, from b2_download_census_migration.py and b2_lookup_msoa_lad23.py):
- ODMG01EW (MSOA and LTLA origin-destination, all ages 1+), ODMG02EW (LTLA OD by 22 age bands)
- ONS census-observations API: migrant indicator x age at MSOA (23 bands; single year) and LTLA (single year)
- MSOA21 -> LAD23 best-fit lookup

Outputs: tidy long CSVs (see notes/B2_census_migration.md for the data dictionary). No regressions.
"""
import re

import numpy as np
import pandas as pd

from ext_config import CLEAN, RAW

SRC = RAW / "census2021_migration"
API = SRC / "ons_api"
BIG = RAW.parent / "clean"          # files over ~50 MB
BIG.mkdir(parents=True, exist_ok=True)

OUTSIDE_UK = "999999999"
# 22 age bands of ODMG02EW (RESIDENT_AGE_23B without the under-1 category).
BANDS22 = [(1, 2), (3, 4), (5, 7), (8, 9), (10, 14), (15, 15), (16, 17), (18, 19), (20, 24), (25, 29),
           (30, 34), (35, 39), (40, 44), (45, 49), (50, 54), (55, 59), (60, 64), (65, 69), (70, 74),
           (75, 79), (80, 84), (85, 120)]
ALL = (1, 120)


def blabel(lo, hi):
    if (lo, hi) == ALL:
        return "All ages 1+"
    if hi >= 120:
        return f"{lo}+"
    return f"{lo}" if lo == hi else f"{lo}-{hi}"


def parse_age(label):
    """'Aged 2 years and under' -> (0, 2); 'Aged 3 to 4 years' -> (3, 4); 'Aged 85 years and over' -> (85, 120)."""
    s = label.lower()
    if "under 1" in s:
        return 0, 0
    n = [int(x) for x in re.findall(r"\d+", s)]
    if "and under" in s:
        return 0, n[0]
    if "and over" in s:
        return n[0], 120
    return (n[0], n[1]) if len(n) == 2 else (n[0], n[0])


def to_band22(lo, hi):
    lo = max(lo, 1)
    for b in BANDS22:
        if b[0] <= lo <= b[1]:
            assert hi <= b[1], (lo, hi, b)
            return b
    raise ValueError((lo, hi))


# ---------------------------------------------------------------- geography
def geography():
    lk = pd.read_csv(SRC / "geography" / "MSOA21_LAD23_EW_LU.csv")
    ltla = pd.read_csv(SRC / "census2021-ts019" / "census2021-ts019-ltla.csv")[["geography", "geography code"]]
    ltla.columns = ["lad21_name", "lad21_code"]
    # Census 2021 MSOA names are '<LAD name> NNN' using the LAD in force at the census (2021/22 vintage).
    lk["lad21_name"] = lk.MSOA21NM.str.replace(r"\s\d{3}$", "", regex=True)
    lk = lk.merge(ltla, on="lad21_name", how="left")
    # Four LADs are named differently in MSOA names (e.g. 'Bristol' vs 'Bristol, City of'); none changed
    # between 2021 and 2023, so the 2023 code is the 2021 code.
    miss = lk.lad21_code.isna() & lk.LAD23CD.isin(ltla.lad21_code)
    lk.loc[miss, "lad21_code"] = lk.loc[miss, "LAD23CD"]
    lk = lk.drop(columns="lad21_name").merge(ltla, on="lad21_code", how="left")
    assert lk.lad21_code.notna().all(), lk[lk.lad21_code.isna()].head()
    m = lk.rename(columns={"MSOA21CD": "msoa21_code", "MSOA21NM": "msoa21_name",
                           "LAD23CD": "lad23_code", "LAD23NM": "lad23_name"})
    m = m[["msoa21_code", "msoa21_name", "lad21_code", "lad21_name", "lad23_code", "lad23_name"]]
    l21_23 = m[["lad21_code", "lad21_name", "lad23_code", "lad23_name"]].drop_duplicates()
    assert l21_23.lad21_code.is_unique, "a 2021 LAD splits across 2023 LADs"
    return m, l21_23


# ---------------------------------------------------------------- OD measures
def od_measures(od, keys):
    """od: columns o, d, n (+ keys other than geo). Returns long in/out measures per destination area."""
    o = od.o.astype(str)
    od = od.assign(
        kind=np.select(
            [o == "-8", o == OUTSIDE_UK, o == od.d, o.str[0].isin(["E", "W"]), o.str[0] == "S", o.str[0] == "N"],
            ["nonmigrant", "in_outside_uk", "in_same_area", "in_other_ew", "in_scotland", "in_ni"], "unknown"))
    assert (od.kind != "unknown").all(), od[od.kind == "unknown"].o.unique()[:10]
    wide = od.pivot_table(index=["d"] + keys, columns="kind", values="n", aggfunc="sum", fill_value=0)
    for c in ["nonmigrant", "in_outside_uk", "in_same_area", "in_other_ew", "in_scotland", "in_ni"]:
        if c not in wide:
            wide[c] = 0
    wide["denom_pop"] = wide[["nonmigrant", "in_outside_uk", "in_same_area", "in_other_ew",
                              "in_scotland", "in_ni"]].sum(axis=1)
    wide["in_elsewhere_uk"] = wide.in_other_ew + wide.in_scotland + wide.in_ni
    wide["in_from_uk"] = wide.in_same_area + wide.in_elsewhere_uk
    wide["in_total"] = wide.in_from_uk + wide.in_outside_uk
    # Outflows: people now resident elsewhere in England and Wales whose address a year ago was in this area.
    ew = od[(od.kind == "in_other_ew")]
    out = ew.groupby(["o"] + keys).n.sum().rename("out_other_ew")
    out.index = out.index.set_names(["d"] + keys)
    wide = wide.join(out, how="left").fillna({"out_other_ew": 0})
    wide["out_same_area"] = wide.in_same_area
    wide["net_other_ew"] = wide.in_other_ew - wide.out_other_ew
    wide = wide.drop(columns="nonmigrant").reset_index()
    long = wide.melt(id_vars=["d"] + keys + ["denom_pop"], var_name="measure", value_name="count")
    long["rate_per_1000"] = 1000 * long["count"] / long["denom_pop"].where(long.denom_pop > 0)
    return long.rename(columns={"d": "geo_code"})


def la_od(lad_map):
    """ODMG02EW (22 bands) + ODMG01EW LTLA (all ages 1+), at LAD21 and LAD23."""
    a = pd.read_csv(SRC / "odmg02ew" / "ODMG02EW_LTLA.csv")
    a.columns = ["o", "ol", "d", "dl", "age_code", "age_label", "n"]
    lab = a[["age_code", "age_label"]].drop_duplicates().sort_values("age_code")
    assert [parse_age(x) for x in lab.age_label] == [b if b[1] < 120 else (85, 120) for b in BANDS22], lab
    a["band"] = a.age_code.map(lambda k: blabel(*BANDS22[k - 1]))
    b = pd.read_csv(SRC / "odmg01ew" / "ODMG01EW_LTLA.csv")
    b.columns = ["o", "ol", "d", "dl", "n"]
    b["band"] = blabel(*ALL)
    od = pd.concat([a[["o", "d", "band", "n"]], b[["o", "d", "band", "n"]]])
    od["o"] = od.o.astype(str)
    out = []
    for vint in ["lad21", "lad23"]:
        x = od.copy()
        if vint == "lad23":
            m = dict(zip(lad_map.lad21_code, lad_map.lad23_code))
            x["o"] = x.o.map(lambda c: m.get(c, c))
            x["d"] = x.d.map(m)
            x = x.groupby(["o", "d", "band"], as_index=False).n.sum()
        r = od_measures(x, ["band"])
        r["geo_level"] = vint
        r["source"] = np.where(r.band == blabel(*ALL), "ODMG01EW_LTLA", "ODMG02EW_LTLA")
        out.append(r)
    r = pd.concat(out)
    names = pd.concat([lad_map[["lad21_code", "lad21_name"]].set_axis(["geo_code", "geo_name"], axis=1),
                       lad_map[["lad23_code", "lad23_name"]].drop_duplicates().set_axis(["geo_code", "geo_name"], axis=1)]
                      ).drop_duplicates("geo_code")   # one name per code (2021 Census name kept)
    r = r.merge(names, on="geo_code", how="left", validate="many_to_one")
    r = r.rename(columns={"band": "age_band"})
    order = {blabel(*b): i for i, b in enumerate(BANDS22)} | {blabel(*ALL): 99}
    r["age_order"] = r.age_band.map(order)
    return r.sort_values(["geo_level", "geo_code", "age_order", "measure"])


def msoa_od_all_ages(geo):
    a = pd.read_csv(SRC / "odmg01ew" / "ODMG01EW_MSOA.csv")
    a.columns = ["o", "ol", "d", "dl", "n"]
    a["o"] = a.o.astype(str)
    r = od_measures(a[["o", "d", "n"]], [])
    r["geo_level"] = "msoa21"
    r["age_band"] = blabel(*ALL)
    r["source"] = "ODMG01EW_MSOA"
    r = r.merge(geo[["msoa21_code", "msoa21_name", "lad21_code", "lad23_code"]],
                left_on="geo_code", right_on="msoa21_code", how="left").drop(columns="msoa21_code")
    return r.rename(columns={"msoa21_name": "geo_name"})


# ---------------------------------------------------------------- API (migrant indicator x age)
MIG = {"0": "nonmigrant", "1": "in_student_termtime", "2": "in_uk_nonstudent", "3": "in_outside_uk", "-8": "under1"}


def api_labels():
    import json
    js = json.load(open(API / "categories_resident_age_101a.json", encoding="utf8"))
    return {x["id"]: {c["id"]: c["label"] for c in x["categories"]} for x in js["items"]}


def api_measures(df, keys):
    """df: area_code, kind, keys..., count -> long inflow measures (age 1+ population as denominator)."""
    w = df.pivot_table(index=["area_code"] + keys, columns="kind", values="count", aggfunc="sum", fill_value=0)
    for c in MIG.values():
        if c not in w:
            w[c] = 0
    w["denom_pop"] = w[["nonmigrant", "in_student_termtime", "in_uk_nonstudent", "in_outside_uk"]].sum(axis=1)
    w["in_from_uk"] = w.in_student_termtime + w.in_uk_nonstudent
    w["in_total"] = w.in_from_uk + w.in_outside_uk
    w = w.drop(columns=["nonmigrant", "under1"]).reset_index()
    long = w.melt(id_vars=["area_code"] + keys + ["denom_pop"], var_name="measure", value_name="count")
    long["rate_per_1000"] = 1000 * long["count"] / long.denom_pop.where(long.denom_pop > 0)
    return long.rename(columns={"area_code": "geo_code"})


def load_api(area, dim, labels):
    f = API / f"{area}_migrant_ind_{dim}.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f, dtype=str)
    if d.empty:
        return None
    d["count"] = d["count"].astype(int)
    d["kind"] = d.migrant_ind.map(MIG)
    lab = labels[dim]
    d["lo"], d["hi"] = zip(*d.age_code.map(lambda c: parse_age(lab[c])))
    d["age_classification"] = dim
    return d


def api_banded(d, to22=True):
    """Collapse to the 22 ODMG bands (to22) or keep native bands; drop the under-1 'does not apply' cells."""
    d = d[(d.kind != "under1") & (d.hi >= 1)].copy()
    if to22:
        d[["lo", "hi"]] = [to_band22(lo, hi) for lo, hi in zip(d.lo, d.hi)]
    d["lo"] = d.lo.clip(lower=1)
    d["age_band"] = [blabel(lo, hi) for lo, hi in zip(d.lo, d.hi)]
    d = d.groupby(["area_code", "kind", "age_band", "lo", "hi", "age_classification"], as_index=False)["count"].sum()
    return api_measures(d, ["age_band", "lo", "hi", "age_classification"])


def main():
    geo, lad_map = geography()
    geo.to_csv(CLEAN / "b2_lookup_msoa21_lad21_lad23.csv", index=False)
    labels = api_labels()

    # ---- LA: OD-based by 22 age bands + all ages
    la = la_od(lad_map)
    cols = ["geo_level", "geo_code", "geo_name", "age_band", "measure", "count", "denom_pop", "rate_per_1000", "source"]
    la[cols].to_csv(CLEAN / "b2_la_migration_by_age.csv", index=False)
    print("LA OD file", len(la), la.groupby("geo_level").geo_code.nunique().to_dict())

    # ---- LA: single-year inflows (API, finest)
    d = load_api("ltla", "resident_age_101a", labels)
    sy = []
    for vint in ["lad21", "lad23"]:
        x = d.copy()
        if vint == "lad23":
            x["area_code"] = x.area_code.map(dict(zip(lad_map.lad21_code, lad_map.lad23_code)))
        r = api_banded(x, to22=False)
        r["geo_level"] = vint
        sy.append(r)
    sy = pd.concat(sy)
    sy["source"] = "ONS API migrant_ind x resident_age_101a"
    sy["age"] = np.where(sy.hi >= 120, sy.lo.astype(str) + "+", sy.lo.astype(str))
    sy = sy.drop(columns=["lo", "hi", "age_band", "age_classification"])
    sy[["geo_level", "geo_code", "age", "measure", "count", "denom_pop", "rate_per_1000", "source"]].to_csv(
        CLEAN / "b2_la_inflows_single_year.csv", index=False)
    print("LA single-year file", len(sy))

    # ---- MSOA: OD-based, all ages 1+
    ma = msoa_od_all_ages(geo)
    ma[["geo_level", "geo_code", "geo_name", "lad21_code", "lad23_code", "age_band", "measure", "count",
        "denom_pop", "rate_per_1000", "source"]].to_csv(CLEAN / "b2_msoa_migration_all_ages.csv", index=False)
    print("MSOA all-ages file", len(ma), ma.geo_code.nunique())

    # ---- MSOA: inflows by 22 age bands (API resident_age_23a), coarser fallbacks for blocked MSOAs
    # Priority: 23 bands; else single year collapsed to the same 22 bands; else coarser native bands.
    parts, done = [], set()
    for dim, to22 in [("resident_age_23a", True), ("resident_age_86a", True), ("resident_age_18b", False),
                      ("resident_age_11a", False), ("resident_age_8c", False), ("resident_age_6a", False)]:
        x = load_api("msoa", dim, labels)
        if x is None or not len(x):
            continue
        x = x[~x.area_code.isin(done)]
        if not len(x):
            continue
        parts.append(api_banded(x, to22=to22))
        done |= set(x.area_code)
    mb = pd.concat(parts)
    mb.loc[mb.age_classification == "resident_age_86a", "age_classification"] = "resident_age_86a collapsed to 22 bands"
    mb["geo_level"] = "msoa21"
    mb["source"] = "ONS API migrant_ind x " + mb.age_classification
    mb = mb.merge(geo[["msoa21_code", "lad23_code"]], left_on="geo_code", right_on="msoa21_code").drop(columns="msoa21_code")
    mcols = ["geo_level", "geo_code", "lad23_code", "age_band", "measure", "count", "denom_pop", "rate_per_1000",
             "age_classification"]
    mb = mb.sort_values(["geo_code", "lo", "measure"])
    p = CLEAN / "b2_msoa_inflows_by_age.csv"
    mb[mcols].to_csv(p, index=False)
    if p.stat().st_size > 50e6:
        p.replace(BIG / p.name)
        p = BIG / p.name
    print("MSOA by-age file", len(mb), mb.geo_code.nunique(), p)

    # ---- MSOA: single-year inflows (API resident_age_86a), finest; some MSOAs blocked by the API
    d = load_api("msoa", "resident_age_86a", labels)
    ms = api_banded(d, to22=False)
    ms = ms.rename(columns={"lo": "age"})
    ms["age"] = np.where(ms.hi >= 120, "85+", ms.age.astype(str))
    ms["geo_level"] = "msoa21"
    ms = ms.merge(geo[["msoa21_code", "lad23_code"]], left_on="geo_code", right_on="msoa21_code").drop(columns="msoa21_code")
    p = BIG / "b2_msoa_inflows_single_year.csv.gz"
    ms[["geo_level", "geo_code", "lad23_code", "age", "measure", "count", "denom_pop", "rate_per_1000"]].to_csv(
        p, index=False, compression="gzip")
    print("MSOA single-year file", len(ms), ms.geo_code.nunique(), p)


if __name__ == "__main__":
    main()
