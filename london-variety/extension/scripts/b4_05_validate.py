"""B4 step 5: verify the regulation-built panel against compiled datasets and published figures.

Writes CLEAN/b4_validation_summary.csv (one row per check) and CLEAN/b4_validation_tier_mismatches.csv.
Checks:
  1  national lockdown days: every LA in the nation has intensity 1
  2  Leicester / Oadby and Wigston July 2020 spike
  3  English tiers vs Abel & Siraj (Zenodo 8191880), every LTLA-day 2 Dec 2020 - 5 Jan 2021
  4  English tiers vs House of Commons Library table (ODI Leeds git snapshots), Oct and Dec 2020
  5  English tiers vs Gibbs et al. daily scrapes of the Commons Library table (Zenodo 4421649), 25 Oct - 4 Nov 2020
  6  local measures on 7 Oct 2020 (England household-mixing areas, Welsh local health protection areas) vs the
     Commons Library 7 Oct snapshot
  7  population by tier on 2 Dec 2020 and 31 Dec 2020 vs figures published at the time (PA / Government)
  8  OxCGRT (nation level) workplace-closing indicator over the national lockdowns, England and Wales
"""
import glob
from datetime import date

import numpy as np
import pandas as pd

from b4_common import R, ltla20, pop2020
from ext_config import CLEAN

TIER_LABEL = {"Medium": 1, "High": 2, "Very High": 3, "Stay at home": 4}
out, mism = [], []


def add(check, item, value, expected, ok, note=""):
    out.append(dict(check=check, item=item, value=value, expected=expected, ok=bool(ok), note=note))


def main():
    d = pd.read_csv(CLEAN / "b4_restrictions_daily_ltla20.csv.gz", parse_dates=["date"])
    d23 = pd.read_csv(CLEAN / "b4_restrictions_daily_lad23.csv", parse_dates=["date"])
    lt = ltla20()

    # 1 national lockdowns
    for day, nations in [("2020-04-15", "EW"), ("2020-11-15", "E"), ("2020-10-30", "W"), ("2021-01-20", "EW"),
                         ("2021-02-15", "EW"), ("2021-04-01", "EW")]:
        for n in nations:
            x = d23[(d23.date == day) & (d23.nation == n)]
            add("1 national lockdown", f"{n} {day}", round(x.hosp_intensity.mean(), 4), 1.0,
                (x.hosp_intensity == 1).all(), f"{len(x)} LAs")
    for day, n, exp in [("2020-08-15", "E", "0 except local measures"), ("2021-08-15", "E", 0.0), ("2021-08-15", "W", 0.0)]:
        x = d23[(d23.date == day) & (d23.nation == n)]
        add("1 national open", f"{n} {day}", round(x.hosp_intensity.mean(), 4), exp,
            x.hosp_intensity.median() == 0, f"max {x.hosp_intensity.max()}")

    # 2 Leicester spike
    jul = d23[(d23.date >= "2020-07-04") & (d23.date <= "2020-07-31")]
    m = jul.groupby(["lad23_code", "lad23_name"]).hosp_intensity.mean().sort_values(ascending=False)
    add("2 Leicester July 2020", "mean intensity 4-31 Jul, Leicester", round(m.loc["E06000016"].iloc[0], 3), 1.0,
        m.loc["E06000016"].iloc[0] == 1)
    add("2 Leicester July 2020", "mean intensity 4-31 Jul, Oadby and Wigston", round(m.loc["E07000135"].iloc[0], 3), 1.0,
        m.loc["E07000135"].iloc[0] == 1)
    others = m.drop(["E06000016", "E07000135"], level=0)
    add("2 Leicester July 2020", "max mean intensity 4-31 Jul, all other English LAs", round(others[others.index.get_level_values(0).str[0] == "E"].max(), 3),
        0.0, others[others.index.get_level_values(0).str[0] == "E"].max() == 0)
    q = pd.read_csv(CLEAN / "b4_restrictions_quarterly_lad23.csv")
    q3 = q[(q.quarter == "2020Q3") & (q.nation == "E")].sort_values("hosp_intensity_q", ascending=False)
    top = q3.head(5)
    add("2 Leicester July 2020", "2020Q3 top-5 English LAs", ", ".join(top.lad23_name), "Leicester first, Oadby and Wigston in top 5",
        top.lad23_code.iloc[0] == "E06000016" and "E07000135" in set(top.lad23_code), f"values {top.hosp_intensity_q.tolist()}")

    # 3 Abel & Siraj
    ab = pd.read_csv(R / "zenodo" / "abel_siraj_tiers.csv", parse_dates=["date"])
    mine = d[d.nation == "E"][["ltla20_code", "ltla20_name", "date", "tier"]]
    # the dashboard geography merges Cornwall with the Isles of Scilly and Hackney with the City of London
    mine_c = mine.copy()
    mine_c["code"] = mine_c.ltla20_code.replace({"E06000053": "E06000052", "E09000001": "E09000012"})
    mine_c = mine_c[~mine_c.ltla20_code.isin(["E06000053", "E09000001"])]   # compare Cornwall / Hackney rows only
    # Abel-Siraj keep the four pre-2020 Buckinghamshire district codes
    ab["LTLACode"] = ab.LTLACode.replace({c: "E06000060" for c in ["E07000004", "E07000005", "E07000006", "E07000007"]})
    ab = ab.drop_duplicates(["LTLACode", "date"])
    j = ab.merge(mine_c, left_on=["LTLACode", "date"], right_on=["code", "date"], how="left")
    unmatched = j[j.tier_y.isna()].LTLACode.unique().tolist()
    j = j.dropna(subset=["tier_y"])
    j["agree"] = j.tier_x == j.tier_y
    add("3 Abel-Siraj tiers", "LTLA-days compared", len(j), "", True, f"unmatched Abel codes: {unmatched}")
    add("3 Abel-Siraj tiers", "share of LTLA-days with same tier", round(j.agree.mean(), 4), 1.0, j.agree.mean() > 0.99)
    for r in j[~j.agree].itertuples():
        mism.append(dict(source="Abel-Siraj", date=r.date.date(), ltla20_code=r.ltla20_code, name=r.ltla20_name,
                         tier_panel=r.tier_y, tier_source=r.tier_x))

    # 4/5 Commons Library snapshots (ODI Leeds) and Gibbs scrapes
    def compare_snap(f, day, label):
        s = pd.read_csv(f)
        s.columns = [c.replace("l_l_", "l_") for c in s.columns]
        code = next((c for c in ["lacode", "l_lacode", "l_lockdownareacode"] if c in s.columns), None)
        tcol = "tier" if "tier" in s.columns else "l_tier"
        if code is None:
            return
        s = s[s[code].astype(str).str.match(r"E0[6789]\d{6}$") & s[tcol].isin(TIER_LABEL)]
        s = s.assign(t=s[tcol].map(TIER_LABEL)).drop_duplicates(code)
        x = mine[mine.date == pd.Timestamp(day)].set_index("ltla20_code").tier
        cmp = s.assign(panel=s[code].map(x)).dropna(subset=["panel"])
        ok = (cmp.t == cmp.panel)
        add(label, f"snapshot {f.split('_')[1] if 'commonslib' in f else f[-20:]} vs panel {day}", round(ok.mean(), 4), 1.0,
            ok.mean() > 0.98, f"{len(cmp)} English LAs listed")
        for r in cmp[~ok].itertuples():
            mism.append(dict(source=label, date=day, ltla20_code=getattr(r, code), name="", tier_panel=r.panel,
                             tier_source=r.t))

    snap = R / "odileeds" / "snapshots"
    for stamp, day in [("20201014T1004", "2020-10-14"), ("20201017T0853", "2020-10-17"), ("20201020T1654", "2020-10-20"),
                       ("20201023T0853", "2020-10-23"), ("20201024T0853", "2020-10-24"), ("20201027T0854", "2020-10-27"),
                       ("20201030T0853", "2020-10-30"), ("20201031T0853", "2020-10-31"), ("20201203T1026", "2020-12-03"),
                       ("20201214T1751", "2020-12-14"), ("20201216T0851", "2020-12-16"), ("20201219T0852", "2020-12-19"),
                       ("20201221T1754", "2020-12-21")]:
        f = glob.glob(str(snap / f"commonslib_{stamp}_*.csv"))[0]
        compare_snap(f, day, "4 Commons Library snapshots")
    gb = R / "zenodo" / "uk_tier_data" / "uk_tier_data-0.0.2" / "output"
    for f in sorted(glob.glob(str(gb / "uk_tier_data_parliament_2020_1*.csv"))):
        ds = f.split("parliament_")[1][:10].replace("_", "-")
        if ds <= "2020-11-04":
            compare_snap(f, ds, "5 Gibbs et al. daily scrapes")

    # 6 local measures on 7 Oct 2020
    s = pd.read_csv(glob.glob(str(snap / "commonslib_20201007T1209_*.csv"))[0])
    s = s[(s.l_local_householdmixing == 1) & s.l_Country.isin(["E", "W"])]
    nm = {k: v for k, v in zip(lt.ltla20_name.str.replace(".", "", regex=False), lt.ltla20_code)}
    nm.update({"Birmingham": "E08000025", "St Helens": "E08000013", "Llanelli": "W06000010", "County Durham": "E06000047"})
    listed = set(s.l_Category.str.replace(".", "", regex=False).map(nm).dropna())
    unmapped = s.l_Category[~s.l_Category.str.replace(".", "", regex=False).isin(nm)].tolist()
    o7 = d[(d.date == "2020-10-07") & (d.local_share > 0) & d.state.isin(["E_local_mixing", "E_bolton_closure", "W_lhpa"])
           | ((d.date == "2020-10-07") & d.partial_local_measure.isin(["E_local_mixing", "W_lhpa"]))]
    mine7 = set(o7.ltla20_code)
    add("6 local measures 7 Oct 2020", "LAs in Commons list but not in panel", sorted(listed - mine7), "[]",
        not (listed - mine7), f"unmapped names: {unmapped}")
    add("6 local measures 7 Oct 2020", "LAs in panel but not in Commons list",
        sorted(lt.set_index("ltla20_code").loc[sorted(mine7 - listed)].ltla20_name), "[]", not (mine7 - listed))

    # 7 population by tier vs published figures
    pop = pop2020()
    pub ={("2020-12-02", 3): 23.3e6, ("2020-12-02", 2): 32.2e6, ("2020-12-02", 1): 0.714e6, ("2020-12-31", 4): 44e6}
    eng = mine.assign(pop=mine.ltla20_code.map(pop))
    for (day, t), v in pub.items():
        x = eng[eng.date == day]
        tot = x.loc[x.tier == t, "pop"].sum()
        add("7 published population by tier", f"Tier {t} on {day} (m)", round(tot / 1e6, 2), v / 1e6,
            abs(tot / v - 1) < 0.05, f"{(x.tier == t).sum()} LTLAs; ONS 2018-based SNPP, 2020 projection")
    x = eng[eng.date == "2020-12-02"]
    add("7 published population by tier", "LTLAs in Tier 3 on 2 Dec 2020", int((x.tier == 3).sum()), "119 (Abel-Siraj, dashboard geography)",
        True, f"Tier 1: {sorted(x[x.tier == 1].ltla20_name)}")
    x = eng[eng.date == "2020-12-31"]
    add("7 published population by tier", "Tier 1 on 31 Dec 2020", sorted(x[x.tier == 1].ltla20_name), "Isles of Scilly only",
        sorted(x[x.tier == 1].ltla20_name) == ["Isles of Scilly"])

    # 8 OxCGRT nation level
    ox = pd.read_csv(R / "oxcgrt" / "OxCGRT_compact_subnational_v1.csv", low_memory=False)
    ox = ox[(ox.CountryCode == "GBR") & ox.RegionName.isin(["England", "Wales"])]
    ox["date"] = pd.to_datetime(ox.Date.astype(str))
    for day in ["2020-04-15", "2020-11-15", "2020-10-30", "2021-02-15", "2021-08-15"]:
        for reg in ["England", "Wales"]:
            v = ox[(ox.date == day) & (ox.RegionName == reg)]["C2M_Workplace.closing"]
            n = reg[0]
            pi = d23[(d23.date == day) & (d23.nation == n)].hosp_intensity.mean()
            add("8 OxCGRT C2 workplace closing (nation)", f"{reg} {day}", float(v.iloc[0]) if len(v) else np.nan,
                "3 when panel = 1", True, f"panel mean intensity {pi:.2f}")

    res = pd.DataFrame(out)
    res["value"] = res["value"].astype(str)
    res["expected"] = res["expected"].astype(str)
    res.to_csv(CLEAN / "b4_validation_summary.csv", index=False)
    pd.DataFrame(mism).to_csv(CLEAN / "b4_validation_tier_mismatches.csv", index=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 110)
    print(res.to_string())
    print(pd.DataFrame(mism).groupby(["source", "date"]).size() if mism else "no mismatches")


if __name__ == "__main__":
    main()
