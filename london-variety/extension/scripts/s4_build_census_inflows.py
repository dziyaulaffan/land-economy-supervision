"""S4: Census 2011 and 2001 MSOA one-year-ago migrants by age, and all three censuses on 2021 MSOAs.

Definition used throughout ("all movers", matching B2's in_total): usual residents on census day whose
usual address one year before was different, including moves within the same MSOA and arrivals from abroad.
It equals residents minus those at the same address, so it does not depend on the area level and can be
summed from smaller areas.

2011: UKMIG001 (Migration by sex by age), 2011 MSOA, published counts.
      migrants = 'within same area' + 'Inflow: Total'; residents = migrants + 'same address'.
2001: no public table gives migration by detailed age at MSOA or at an area that nests in MSOAs
      (CS008 at OA has only 0-9/10-19/20-64/65+, and cannot separate same-OA moves; ST008 has detailed age
      but only for 2003 ST wards and above). The 2001 MSOA file is therefore an ESTIMATE:
        migrants_mb = P_mb * rbar_mb, scaled so that sum_b equals the MSOA's published all-age migrants;
        P_mb  = UV004 usual residents by age at 2001 MSOA (published);
        rbar_mb = population-weighted mean over the ST wards overlapping MSOA m (via 2001 OAs) of the ST008
                  age-specific all-mover rate (ward rate; district rate for the 50 CAS wards merged in ST wards);
        all-age migrants per MSOA = sum over OAs of KS024 'People who are migrants' (published).
2021: B2 file b2_msoa_inflows_by_age.csv (measure in_total, denom_pop) and, for All ages,
      b2_msoa_migration_all_ages.csv (ODMG01EW in_total).

Lookups: OA-level chains with ONS Open Geography Portal lookups (see s4_download_lookups.py):
  OA01 -> OA11 (OA01_OA11_LAD11_EW_LU), OA11 -> OA21 (OA11_OA21_LAD22_EW_LU exact fit),
  OA -> MSOA for each year. Each old MSOA's counts are shared out to new MSOAs in proportion to the
  old-census population of its OAs that fall in each new MSOA; an OA split between several new OAs is
  divided by the new-census populations of those OAs. Where the official MSOA lookup says unchanged (U) or
  merged (M), the official one-to-one assignment is used.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ext_config import CLEAN, RAW  # noqa: E402

NOM = RAW / "nomis" / "s4"
LKP = RAW / "ons_geography" / "s4_lookups"
C21 = RAW / "census2021_migration"
EXT_CLEAN = Path.home() / "research-data" / "london-variety-extension" / "clean"

HARM = ["0-4", "5-15", "16-19", "20-24", "25-34", "35-49", "50-64", "65-74", "75+"]
B11 = {1: "0-4", 2: "5-15", 3: "16-19", 4: "20-24", 5: "25-34", 6: "35-49", 7: "50-64", 8: "65-74", 9: "75+"}
# ST008 bands (C_AGE code -> label, lower age, upper age)
B01 = {1: ("0", 0, 0), 2: ("1-3", 1, 3), 3: ("4", 4, 4), 4: ("5-9", 5, 9), 5: ("10-14", 10, 14), 6: ("15", 15, 15),
       7: ("16-17", 16, 17), 8: ("18-19", 18, 19), 9: ("20-24", 20, 24), 10: ("25-29", 25, 29),
       11: ("30-34", 30, 34), 12: ("35-39", 35, 39), 13: ("40-44", 40, 44), 14: ("45-49", 45, 49),
       15: ("50-54", 50, 54), 16: ("55-59", 55, 59), 17: ("60-64", 60, 64), 18: ("65-69", 65, 69),
       19: ("70-74", 70, 74), 20: ("75-79", 75, 79), 21: ("80-84", 80, 84), 22: ("85-89", 85, 89),
       23: ("90+", 90, 200)}
B01_ORDER = [v[0] for v in B01.values()]


def harm_of(lo):
    for lab, a, b in [("0-4", 0, 4), ("5-15", 5, 15), ("16-19", 16, 19), ("20-24", 20, 24), ("25-34", 25, 34),
                      ("35-49", 35, 49), ("50-64", 50, 64), ("65-74", 65, 74), ("75+", 75, 200)]:
        if a <= lo <= b:
            return lab


H01 = {lab: harm_of(lo) for lab, lo, hi in B01.values()}
H21 = {"1-2": "0-4", "3-4": "0-4", "5-7": "5-15", "8-9": "5-15", "10-14": "5-15", "15": "5-15", "16-17": "16-19",
       "18-19": "16-19", "20-24": "20-24", "25-29": "25-34", "30-34": "25-34", "35-39": "35-49", "40-44": "35-49",
       "45-49": "35-49", "50-54": "50-64", "55-59": "50-64", "60-64": "50-64", "65-69": "65-74", "70-74": "65-74",
       "75-79": "75+", "80-84": "75+", "85+": "75+"}


# ---------------------------------------------------------------- 2011
def census2011():
    d = pd.read_csv(NOM / "ukmig001_msoa11.csv")
    p = d.pivot_table(index=["GEOGRAPHY_CODE", "C_AGE"], columns="C_MIGR", values="OBS_VALUE", aggfunc="sum")
    assert (p[2] - p[3] - p[4] - p[5]).abs().max() == 0
    out = pd.DataFrame({"migrants": p[1] + p[2], "residents": p[0] + p[1] + p[2],
                        "moved_within_msoa": p[1], "inflow_from_outside_msoa": p[2],
                        "inflow_from_outside_uk": p[5]}).reset_index()
    out["age_band"] = out.C_AGE.map(B11).fillna("All ages")
    out = out.rename(columns={"GEOGRAPHY_CODE": "msoa11cd"}).drop(columns="C_AGE")
    out["rate_per_1000"] = 1000 * out.migrants / out.residents
    out["source"] = "Census 2011 UKMIG001 (Nomis NM_1280_1)"
    order = {b: i for i, b in enumerate(["All ages"] + HARM)}
    out = out.sort_values(["msoa11cd", "age_band"], key=lambda s: s.map(order) if s.name == "age_band" else s)
    cols = ["msoa11cd", "age_band", "migrants", "residents", "rate_per_1000", "moved_within_msoa",
            "inflow_from_outside_msoa", "inflow_from_outside_uk", "source"]
    return out[cols]


# ---------------------------------------------------------------- 2001
def census2001():
    lk = pd.read_csv(LKP / "OA01_LSOA01_MSOA01_EW_LU.csv", dtype=str)
    oa0111 = pd.read_csv(LKP / "OA01_OA11_LAD11_EW_LU.csv", dtype=str)
    ks = pd.read_csv(NOM / "ks024_oa01.csv", dtype={"GEOGRAPHY_CODE": str})
    ks = ks.pivot_table(index="GEOGRAPHY_CODE", columns="C_MIGR", values="OBS_VALUE", aggfunc="sum")
    oa = pd.DataFrame({"pop": ks[0], "mig": ks[1], "nua": ks[4]})   # 4 = no usual address one year before
    # KS024 OA codes may be old-style (00AAFA0001) or GSS (E00000001)
    if oa.index.str.match(r"^[EW]00").all():
        old = dict(zip(oa0111.OA01CD, oa0111.OA01CDO))
        oa.index = oa.index.map(old)
    oa.index.name = "oa01_old"
    oa = oa.reset_index()
    oa["casward"] = oa.oa01_old.str[:6]
    msoa_of = dict(zip(lk.OA01CD, lk.MSOA01CD))  # OA01CD in this lookup is old style
    if not pd.Series(list(msoa_of)).str.match(r"^\d\d[A-Z]{2}").all():
        raise RuntimeError("unexpected OA code style in OA01_LSOA01_MSOA01")
    oa["msoa01cd"] = oa.oa01_old.map(msoa_of)
    lad_of = oa0111.drop_duplicates("OA01CDO").set_index("OA01CDO").LAD11CD
    # Nomis holds ST008 districts under the codes in use until April 2015 (six were recoded in 2013-14)
    recode = {"E08000020": "E08000037", "E07000097": "E07000242", "E07000100": "E07000240",
              "E07000101": "E07000243", "E07000104": "E07000241", "E06000048": "E06000057"}
    oa["lad"] = oa.oa01_old.map(lad_of).replace(recode)
    assert oa.msoa01cd.notna().all() and oa.lad.notna().all()

    stw = pd.read_csv(NOM / "st008_stward03.csv", dtype={"GEOGRAPHY_CODE": str})
    stl = pd.read_csv(NOM / "st008_lad.csv", dtype={"GEOGRAPHY_CODE": str})

    def rates(s, excl_nua):
        s = s[s.C_AGE > 0]
        p = s.pivot_table(index=["GEOGRAPHY_CODE", "C_AGE"], columns="C_MIGR", values="OBS_VALUE", aggfunc="sum")
        tot = p[[0, 1, 2, 3, 4, 5]].sum(axis=1)
        movers = tot - p[0] - (p[2] if excl_nua else 0)    # ST008 code 2 = no usual address one year ago
        r = (movers / tot).rename("rate").reset_index()
        r["tot"] = tot.values
        return r

    rw = rates(stw, False)
    rl = rates(stl, False)
    st_wards = set(rw.GEOGRAPHY_CODE)
    oa["rate_geo"] = np.where(oa.casward.isin(st_wards), oa.casward, oa.lad)
    oa["rate_level"] = np.where(oa.casward.isin(st_wards), "ST ward", "district")
    if not set(oa.lad).issubset(set(rl.GEOGRAPHY_CODE)):
        raise RuntimeError("district codes in ST008 do not match LAD11 codes: "
                           + str(sorted(set(oa.lad) - set(rl.GEOGRAPHY_CODE))[:5]))
    uv = pd.read_csv(NOM / "uv004_msoa01.csv", dtype={"GEOGRAPHY_CODE": str})
    uv = uv[uv.C_AGE > 0].copy()
    # code 1 = under 1, codes 2-75 = ages 1-74, then 75-79, 80-84, 85-89, 90-94, 95-99, 100+
    top = {76: 75, 77: 80, 78: 85, 79: 90, 80: 95, 81: 100}
    uv["age"] = uv.C_AGE.map(lambda c: top.get(c, c - 1))
    lab = {}
    for code, (l, lo, hi) in B01.items():
        for a in range(lo, min(hi, 120) + 1):
            lab[a] = code
    uv["band"] = uv.age.map(lambda a: lab[min(a, 90)])
    P0 = uv.pivot_table(index="GEOGRAPHY_CODE", columns="band", values="OBS_VALUE", aggfunc="sum")

    def estimate(excl_nua):
        rw_, rl_ = rates(stw, excl_nua), rates(stl, excl_nua)
        rmat = pd.concat([rw_, rl_]).pivot_table(index="GEOGRAPHY_CODE", columns="C_AGE", values="rate")
        lmat = rl_.pivot_table(index="GEOGRAPHY_CODE", columns="C_AGE", values="rate")
        # MSOA x rate-geography population weights
        wgt = oa.groupby(["msoa01cd", "rate_geo", "lad"])["pop"].sum().reset_index()
        wgt["v"] = wgt["pop"] / wgt.groupby("msoa01cd")["pop"].transform("sum")
        R = rmat.reindex(wgt.rate_geo).values
        L = lmat.reindex(wgt.lad).values
        R = np.where(np.isnan(R), L, R)
        rbar = pd.DataFrame(R * wgt.v.values[:, None], columns=rmat.columns).assign(msoa01cd=wgt.msoa01cd.values)
        rbar = rbar.groupby("msoa01cd").sum()
        P = P0.reindex(rbar.index)
        Mt = (P * rbar[P.columns]).fillna(0)
        tgt = oa.assign(m=oa.mig - (oa.nua if excl_nua else 0)).groupby("msoa01cd").m.sum().reindex(P.index)
        k = tgt / Mt.sum(axis=1)
        capped = int((Mt.mul(k, axis=0) > P).sum().sum())
        M = np.minimum(Mt.mul(k, axis=0), P)
        return M, P, tgt, k, capped

    M, P, target, k, capped = estimate(False)
    M2, _, target2, k2, capped2 = estimate(True)
    long = (M.stack().rename("migrants").to_frame()
            .join(M2.stack().rename("migrants_excl_no_usual_address"))
            .join(P.stack().rename("residents")).reset_index())
    long.columns = ["msoa01cd", "band", "migrants", "migrants_excl_no_usual_address", "residents"]
    long["age_band"] = long.band.map(lambda c: B01[c][0])
    allages = pd.DataFrame({"msoa01cd": P.index, "age_band": "All ages",
                            "migrants": target.values, "migrants_excl_no_usual_address": target2.values, "residents": oa.groupby("msoa01cd")["pop"].sum().reindex(P.index).values})
    out = pd.concat([allages, long.drop(columns="band")], ignore_index=True)
    out["rate_per_1000"] = 1000 * out.migrants / out.residents
    out["estimated"] = out.age_band != "All ages"
    out["source"] = np.where(out.estimated,
                             "ESTIMATE: UV004 residents x ST008 ward all-mover rate, raked to KS024 MSOA total",
                             "Census 2001 KS024 summed over OAs (published)")
    share_district = oa.assign(d=oa.rate_level.eq("district") * oa["pop"]).groupby("msoa01cd").d.sum() / oa.groupby("msoa01cd")["pop"].sum()
    out["share_pop_district_rate"] = out.msoa01cd.map(share_district).round(4)
    out["rake_factor"] = out.msoa01cd.map(k).round(4)
    order = {b: i for i, b in enumerate(["All ages"] + B01_ORDER)}
    out = out.sort_values(["msoa01cd", "age_band"], key=lambda s: s.map(order) if s.name == "age_band" else s)
    diag = dict(n_oa=len(oa), n_msoa=P.shape[0], oa_on_district_rate=int((oa.rate_level == "district").sum()),
                pop_on_district_rate=int(oa.loc[oa.rate_level == "district", "pop"].sum()),
                rake_min=float(k.min()), rake_p05=float(k.quantile(.05)), rake_med=float(k.median()),
                rake_p95=float(k.quantile(.95)), rake_max=float(k.max()), capped_cells=capped, capped_cells_excl_nua=capped2,
                rake_excl_nua_p05=float(k2.quantile(.05)), rake_excl_nua_p95=float(k2.quantile(.95)))
    return out, oa, diag


# ---------------------------------------------------------------- lookups
def oa_chain():
    """Return OA01->OA11 and OA11->OA21 fractional maps and OA->MSOA maps."""
    o0111 = pd.read_csv(LKP / "OA01_OA11_LAD11_EW_LU.csv", dtype=str)
    o1121 = pd.read_csv(LKP / "OA11_OA21_LAD22_EW_LU_Exact_fit.csv", dtype=str)
    l11 = pd.read_csv(LKP / "OA11_LSOA11_MSOA11_LAD11_EW_LU.csv", dtype=str)
    l21 = pd.read_csv(LKP / "OA21_LSOA21_MSOA21_EW_LU.csv", dtype=str)
    pop11 = pd.read_csv(NOM / "ks101ew_oa11.csv").set_index("GEOGRAPHY_CODE").OBS_VALUE
    t21 = pd.read_csv(C21 / "census2021-ts007a" / "census2021-ts007a-oa.csv")
    tcol = [c for c in t21.columns if "Total" in c][0]
    pop21 = t21.set_index("geography code")[tcol]

    def frac(df, src, dst, popdst):
        df = df[[src, dst, df.columns[df.columns.str.startswith("CH")][0]]].drop_duplicates([src, dst]).copy()
        df.columns = ["src", "dst", "chg"]
        df["pd"] = df.dst.map(popdst).fillna(0).astype(float)
        n = df.groupby("src").dst.transform("size")
        s = df.groupby("src").pd.transform("sum")
        df["f"] = np.where(s > 0, df.pd / s.replace(0, np.nan), 1 / n)
        df["f"] = df.f.fillna(1 / n)
        return df[["src", "dst", "chg", "f"]]

    f0111 = frac(o0111.rename(columns={"OA01CDO": "OA01OLD"}), "OA01OLD", "OA11CD", pop11)
    f1121 = frac(o1121, "OA11CD", "OA21CD", pop21)
    m11 = dict(zip(l11.OA11CD, l11.MSOA11CD))
    m21 = dict(zip(l21[[c for c in l21.columns if c.upper().startswith("OA21")][0]],
                   l21[[c for c in l21.columns if c.upper().startswith("MSOA21CD")][0]]))
    return f0111, f1121, m11, m21, pop11


def msoa_weights(oa_old_pop, frac_steps, msoa_old_of, msoa_new_of):
    """Share of each old MSOA's population in each new MSOA, chaining fractional OA maps."""
    cur = oa_old_pop.rename("w").reset_index()
    cur.columns = ["oa", "w"]
    cur["msoa_old"] = cur.oa.map(msoa_old_of)
    for f in frac_steps:
        cur = cur.merge(f[["src", "dst", "f"]], left_on="oa", right_on="src", how="left")
        miss = cur.dst.isna()
        if miss.any():
            print("  OAs without onward link:", int(miss.sum()), "pop", int(cur.loc[miss, "w"].sum()))
        cur = cur[~miss]
        cur["w"] = cur.w * cur.f
        cur = cur[["dst", "w", "msoa_old"]].rename(columns={"dst": "oa"})
    cur["msoa_new"] = cur.oa.map(msoa_new_of)
    w = cur.groupby(["msoa_old", "msoa_new"]).w.sum().reset_index()
    w["share"] = w.w / w.groupby("msoa_old").w.transform("sum")
    return w


def apply_official(w, official, old, new):
    """Use the official one-to-one assignment for MSOAs the ONS lookup flags as unchanged or merged."""
    chg = [c for c in official.columns if c.upper().startswith("CH")][0]   # CHGIND or CHNGIND
    off = official[official[chg].str.upper().isin(["U", "M"])][[old, new]].drop_duplicates()
    one = off.groupby(old)[new].nunique()
    off = off[off[old].isin(one[one == 1].index)]
    keep = w[~w.msoa_old.isin(off[old])]
    add = pd.DataFrame({"msoa_old": off[old], "msoa_new": off[new], "w": np.nan, "share": 1.0})
    # diagnostic: how much OA-based weight fell outside the official target for U/M MSOAs
    chk = w[w.msoa_old.isin(off[old])].merge(off, left_on="msoa_old", right_on=old)
    leak = chk[chk.msoa_new != chk[new]].share.sum()
    res = pd.concat([keep, add], ignore_index=True)
    res["exact"] = res.msoa_old.isin(off[old])
    return res, float(leak), int(off[old].nunique())


def main():
    print("2011 ...")
    c11 = census2011()
    c11.to_csv(CLEAN / "s4_census2011_msoa_inflows_by_age.csv", index=False)
    print("2001 ...")
    c01, oa01, diag01 = census2001()
    c01.to_csv(CLEAN / "s4_census2001_msoa_inflows_by_age.csv", index=False)
    print(diag01)

    print("lookups ...")
    f0111, f1121, m11, m21, pop11 = oa_chain()
    lk01 = pd.read_csv(LKP / "OA01_LSOA01_MSOA01_EW_LU.csv", dtype=str)
    msoa01_of = dict(zip(lk01.OA01CD, lk01.MSOA01CD))
    off0111 = pd.read_csv(LKP / "MSOA01_MSOA11_LAD11_EW_LU.csv", dtype=str)
    off1121 = pd.read_csv(LKP / "MSOA11_MSOA21_LAD22_EW_LU.csv", dtype=str)

    oa01pop = oa01.set_index("oa01_old")["pop"].astype(float)
    w0111 = msoa_weights(oa01pop, [f0111], msoa01_of, m11)
    w0111, leak0111, n0111 = apply_official(w0111, off0111, "MSOA01CD", "MSOA11CD")
    w1121 = msoa_weights(pop11.astype(float), [f1121], m11, m21)
    w1121, leak1121, n1121 = apply_official(w1121, off1121, "MSOA11CD", "MSOA21CD")
    # 2001 -> 2021 through the 2011 MSOA shares
    w0121 = (w0111[["msoa_old", "msoa_new", "share"]].rename(columns={"msoa_new": "m11", "share": "s1"})
             .merge(w1121[["msoa_old", "msoa_new", "share", "exact"]].rename(columns={"msoa_old": "m11", "share": "s2", "exact": "e2"}), on="m11"))
    w0121 = w0121.merge(w0111[["msoa_old", "msoa_new", "exact"]].rename(columns={"msoa_new": "m11", "exact": "e1"}), on=["msoa_old", "m11"])
    w0121["share"] = w0121.s1 * w0121.s2
    w0121["exact"] = w0121.e1 & w0121.e2
    w0121 = w0121.groupby(["msoa_old", "msoa_new"]).agg(share=("share", "sum"), exact=("exact", "all")).reset_index()

    for w, name, a, b in [(w0111, "s4_lookup_msoa01_msoa11.csv", "msoa01cd", "msoa11cd"),
                          (w1121, "s4_lookup_msoa11_msoa21.csv", "msoa11cd", "msoa21cd"),
                          (w0121, "s4_lookup_msoa01_msoa21.csv", "msoa01cd", "msoa21cd")]:
        o = w[["msoa_old", "msoa_new", "share", "exact"]].rename(columns={"msoa_old": a, "msoa_new": b})
        o["share"] = o.share.round(6)
        o = o[o.share > 0]
        o.to_csv(CLEAN / name, index=False)
    print("leak 01-11", leak0111, n0111, "leak 11-21", leak1121, n1121)

    # ---------- harmonise to common bands and map to 2021 MSOAs
    lad = pd.read_csv(CLEAN / "b2_lookup_msoa21_lad21_lad23.csv").set_index("msoa21_code").lad23_code

    def to21(df, code, w, year, bandmap):
        d = df.copy()
        d["age_band"] = d.age_band.map(lambda b: "All ages" if b == "All ages" else bandmap.get(b))
        vals = ["migrants", "residents"] + (["migrants_excl_no_usual_address"] if "migrants_excl_no_usual_address" in d else [])
        d = d.dropna(subset=["age_band"]).groupby([code, "age_band"])[vals].sum().reset_index()
        d = d.merge(w[["msoa_old", "msoa_new", "share", "exact"]], left_on=code, right_on="msoa_old", how="left")
        lost = d.msoa_new.isna()
        if lost.any():
            print(year, "rows without lookup:", int(lost.sum()))
        d = d[~lost]
        for v_ in vals:
            d[v_] *= d.share
        d["apportioned_residents"] = np.where(d.exact, 0, d.residents)
        g = d.groupby(["msoa_new", "age_band"])[vals + ["apportioned_residents"]].sum().reset_index()
        g = g.rename(columns={"apportioned_residents": "apportioned"})
        g["share_apportioned"] = (g.apportioned / g.residents).round(4)
        g = g.drop(columns="apportioned").rename(columns={"msoa_new": "msoa21cd"})
        g["census_year"] = year
        return g

    h11 = {b: b for b in HARM}
    g11 = to21(c11, "msoa11cd", w1121, 2011, h11)
    g01 = to21(c01.drop(columns=["estimated"]), "msoa01cd",
               w0121.assign(msoa_old=w0121.msoa_old), 2001, H01)
    g01["estimated"] = g01.age_band != "All ages"
    g11["estimated"] = False

    b2 = pd.read_csv(EXT_CLEAN / "b2_msoa_inflows_by_age.csv", usecols=["geo_code", "age_band", "measure", "count", "denom_pop", "age_classification"])
    b2 = b2[b2.measure == "in_total"]
    ok = b2.groupby("geo_code").age_band.apply(lambda s: set(s).issubset(set(H21)))
    b2 = b2[b2.geo_code.isin(ok[ok].index)]
    b2["age_band"] = b2.age_band.map(H21)
    g21 = b2.groupby(["geo_code", "age_band"]).agg(migrants=("count", "sum"), residents=("denom_pop", "sum")).reset_index()
    g21 = g21.rename(columns={"geo_code": "msoa21cd"})
    allag = pd.read_csv(CLEAN / "b2_msoa_migration_all_ages.csv")
    allag = allag[(allag.measure == "in_total") & (allag.geo_level == "msoa21")]
    allag = pd.DataFrame({"msoa21cd": allag.geo_code, "age_band": "All ages", "migrants": allag["count"],
                          "residents": allag.denom_pop})
    g21 = pd.concat([allag, g21], ignore_index=True)
    g21["census_year"], g21["share_apportioned"], g21["estimated"] = 2021, 0.0, False

    out = pd.concat([g01, g11, g21], ignore_index=True)
    out = out.rename(columns={"migrants_excl_no_usual_address": "migrants_excl_nua"})
    out["migrants_excl_nua"] = out.migrants_excl_nua.fillna(out.migrants)
    # extra aggregate band 20-34
    agg = (out[out.age_band.isin(["20-24", "25-34"])].groupby(["msoa21cd", "census_year"])
           .agg(migrants=("migrants", "sum"), migrants_excl_nua=("migrants_excl_nua", "sum"),
                residents=("residents", "sum"), share_apportioned=("share_apportioned", "max"),
                estimated=("estimated", "max"), n=("age_band", "size")).reset_index())
    agg = agg[agg.n == 2].drop(columns="n").assign(age_band="20-34")
    out = pd.concat([out, agg], ignore_index=True)
    out["lad23cd"] = out.msoa21cd.map(lad)
    out["rate_per_1000"] = 1000 * out.migrants / out.residents
    out["rate_excl_nua_per_1000"] = (1000 * out.migrants_excl_nua / out.residents).round(3)
    out["migrants_excl_nua"] = out.migrants_excl_nua.round(3)
    # all movers = address one year before differed (incl. within-MSOA moves and arrivals from abroad)
    out["definition"] = out.census_year.map({2001: "all_movers_incl_no_usual_address", 2011: "all_movers",
                                             2021: "all_movers_age1plus"})
    out["rate_per_1000"] = out.rate_per_1000.round(3)
    order = {b: i for i, b in enumerate(["All ages"] + HARM + ["20-34"])}
    out["_o"] = out.age_band.map(order)
    out = out.sort_values(["msoa21cd", "census_year", "_o"]).drop(columns="_o")
    out["migrants"] = out.migrants.round(3)
    out["residents"] = out.residents.round(3)
    cols = ["msoa21cd", "lad23cd", "census_year", "age_band", "migrants", "residents", "rate_per_1000",
            "migrants_excl_nua", "rate_excl_nua_per_1000", "estimated", "share_apportioned", "definition"]
    out[cols].to_csv(CLEAN / "s4_msoa_inflows_on_msoa21.csv", index=False)
    print("harmonised rows", len(out), out.groupby("census_year").msoa21cd.nunique().to_dict())

    # ---------- validation
    val = []
    def add(year, check, value, reference, note=""):
        val.append(dict(census_year=year, check=check, value=value, reference=reference,
                        diff_pct=None if reference in (None, 0) else round(100 * (value - reference) / reference, 4), note=note))
    u8 = pd.read_csv(NOM / "ukmig008_ctry.csv")
    ew = u8[u8.GEOGRAPHY_NAME.isin(["England", "Wales"])].groupby("C_MIGR_NAME").OBS_VALUE.sum()
    a11 = c11[c11.age_band == "All ages"]
    add(2011, "residents, sum of MSOAs", a11.residents.sum(), float(ew["All usual residents"]), "UKMIG008 England + Wales")
    add(2011, "migrants, sum of MSOAs", a11.migrants.sum(), float(ew["Migrants: Total"]), "UKMIG008 England + Wales")
    ks101 = pd.read_csv(NOM / "ks101ew_ew.csv").OBS_VALUE.iloc[0]
    add(2011, "residents, sum of MSOAs vs KS101EW", a11.residents.sum(), float(ks101), "KS101EW England and Wales")
    add(2011, "residents, sum of 2011 OAs (KS101EW, weights)", float(pop11.sum()), float(ks101), "")
    for b in HARM:
        s = c11[c11.age_band == b]
        add(2011, f"band {b} residents, sum of MSOAs", s.residents.sum(), None, f"rate per 1000 {1000*s.migrants.sum()/s.residents.sum():.1f}")
    ks_ew = pd.read_csv(NOM / "ks024_ew.csv").set_index("C_MIGR").OBS_VALUE
    a01 = c01[c01.age_band == "All ages"]
    add(2001, "residents, sum of OAs (KS024 all people)", a01.residents.sum(), float(ks_ew[0]), "KS024 England and Wales")
    add(2001, "migrants, sum of OAs (KS024)", a01.migrants.sum(), float(ks_ew[1]), "KS024 England and Wales")
    add(2001, "migrants excl. no usual address, sum of OAs (KS024)", a01.migrants_excl_no_usual_address.sum(),
        float(ks_ew[1] - ks_ew[4]), "KS024 England and Wales")
    uv_ew = pd.read_csv(NOM / "uv004_ew.csv").set_index("C_AGE").OBS_VALUE
    b01 = c01[c01.age_band != "All ages"]
    add(2001, "residents by band summed (UV004 MSOA)", b01.residents.sum(), float(uv_ew[0]), "UV004 England and Wales")
    st = pd.read_csv(NOM / "st008_ew.csv").pivot_table(index="C_AGE", columns="C_MIGR", values="OBS_VALUE", aggfunc="sum")
    st_m = st[[1, 2, 3, 4, 5]].sum(axis=1)
    st_t = st[[0, 1, 2, 3, 4, 5]].sum(axis=1)
    for code, (labb, lo, hi) in B01.items():
        s = b01[b01.age_band == labb]
        add(2001, f"band {labb} migrants (estimate) vs ST008 E&W", s.migrants.sum(), float(st_m[code]),
            f"rate est {1000*s.migrants.sum()/s.residents.sum():.1f} vs ST008 {1000*st_m[code]/st_t[code]:.1f}")
        add(2001, f"band {labb} migrants excl. no usual address (estimate) vs ST008 E&W",
            s.migrants_excl_no_usual_address.sum(), float(st_m[code] - st[2][code]), "")
    # harmonised totals preserved by the mapping
    for yr, src in [(2011, c11), (2001, c01)]:
        for b in ["All ages", "20-24", "25-34"]:
            if yr == 2001 and b != "All ages":
                s = src[src.age_band.map(H01) == b]
            else:
                s = src[src.age_band == b]
            h = out[(out.census_year == yr) & (out.age_band == b)]
            add(yr, f"{b} migrants on MSOA21 vs native", h.migrants.sum(), s.migrants.sum(), "mapping preserves totals")
            add(yr, f"{b} residents on MSOA21 vs native", h.residents.sum(), s.residents.sum(), "mapping preserves totals")
    for b in ["All ages", "20-24", "25-34"]:
        h = out[(out.census_year == 2021) & (out.age_band == b)]
        add(2021, f"{b} migrants on MSOA21 (B2 file)", h.migrants.sum(), 6493688.0 if b == "All ages" else None,
            "TS019 E&W migrants aged 1+" if b == "All ages" else f"rate {1000*h.migrants.sum()/h.residents.sum():.1f}; MSOAs {h.msoa21cd.nunique()}")
    add(2011, "MSOA01->MSOA11: OA-based weight outside official target for U/M MSOAs (sum of shares)", leak0111, None, f"{n0111} U/M MSOAs")
    add(2011, "MSOA11->MSOA21: OA-based weight outside official target for U/M MSOAs (sum of shares)", leak1121, None, f"{n1121} U/M MSOAs")
    for k_, v_ in diag01.items():
        add(2001, f"estimator diagnostic: {k_}", v_, None)

    # out-of-sample check of the 2001 estimator using 2011 truth (district rates only, a harder test)
    l11 = pd.read_csv(LKP / "OA11_LSOA11_MSOA11_LAD11_EW_LU.csv", dtype=str).drop_duplicates("MSOA11CD").set_index("MSOA11CD").LAD11CD
    t = c11[c11.age_band.isin(HARM)].copy()
    t["lad"] = t.msoa11cd.map(l11)
    lr = t.groupby(["lad", "age_band"]).apply(lambda g: g.migrants.sum() / g.residents.sum()).rename("lr").reset_index()
    t = t.merge(lr, on=["lad", "age_band"])
    t["est"] = t.residents * t.lr
    tot = c11[c11.age_band == "All ages"].set_index("msoa11cd").migrants
    t["est"] *= t.msoa11cd.map(tot / t.groupby("msoa11cd").est.sum())
    for b in ["20-24", "25-34"]:
        s = t[t.age_band == b]
        re_ = 1000 * s.est / s.residents
        rt = 1000 * s.migrants / s.residents
        add(2011, f"estimator test, band {b}: correlation of estimated and true MSOA rates (district rates, raked)",
            round(float(np.corrcoef(re_, rt)[0, 1]), 4), None,
            f"median abs error {float((re_-rt).abs().median()):.1f} per 1000; true median rate {float(rt.median()):.1f}")
    v = pd.DataFrame(val)
    v.to_csv(CLEAN / "s4_validation.csv", index=False)
    print(v.to_string())


if __name__ == "__main__":
    main()
