"""B4 step 4: daily restriction state and hospitality closure intensity by local authority, 1 Mar 2020 - 31 Dec 2021,
then the quarterly mean, on 2023 LAD codes (England and Wales, 318 LAs).

Inputs: CLEAN/b4_legal_areas.csv (local measures read from the regulations by b4_03) plus the national timelines
below, each date taken from the coming-into-force provisions of the SI cited (texts in RAW/restrictions/legislation).
Day rule: a day takes the state in force at the end of that day (23:59).

Hospitality closure intensity (0-1), from the component flags:
  1.00  indoor and outdoor hospitality closed (takeaway / delivery only)
  0.75  indoor closed, outdoor service allowed
  0.50  open, but with a legal ban on indoor mixing between households, a substantial-meal requirement for
        serving alcohol (wet-led pubs closed), or (Wales, 4-19 Dec 2020) 18:00 closing with no alcohol
  0.25  open, with a curfew / early closing, compulsory table service, or a legal group-size limit
        (rule of six; Wales extended-household limit)
  0.00  open with no hospitality-specific legal restriction (guidance only)
Where a local measure covered only listed wards, the LA value is the population-weighted mix of the local and the
surrounding (national) level, using mid-2019 ward populations.
"""
from datetime import date, timedelta

import numpy as np
import pandas as pd

from b4_common import R, ltla20, pop2020
from ext_config import CLEAN, PROJECT
import sys

sys.path.insert(0, str(PROJECT / "scripts"))
from config import la_region_lookup  # noqa: E402

START, END = date(2020, 3, 1), date(2021, 12, 31)
FLAGS = ["indoor_closed", "outdoor_closed", "meal_req", "mix_ban", "early_close_no_alcohol", "curfew",
         "table_service", "group_limit"]

# measure -> set flags
M = {
    "open":            {},
    "closed":          {"indoor_closed": 1, "outdoor_closed": 1},
    "outdoor_only":    {"indoor_closed": 1, "table_service": 1, "group_limit": 1},
    "group":           {"group_limit": 1},
    "curfew":          {"curfew": 1, "table_service": 1, "group_limit": 1},
    "table_group":     {"table_service": 1, "group_limit": 1},
    "tier_oct_1":      {"curfew": 1, "table_service": 1, "group_limit": 1},
    "tier_oct_2":      {"curfew": 1, "table_service": 1, "group_limit": 1, "mix_ban": 1},
    "tier_oct_3":      {"curfew": 1, "table_service": 1, "group_limit": 1, "mix_ban": 1, "meal_req": 1},
    "tier_dec_1":      {"curfew": 1, "table_service": 1, "group_limit": 1},
    "tier_dec_2":      {"curfew": 1, "table_service": 1, "group_limit": 1, "mix_ban": 1, "meal_req": 1},
    "tier_dec_3":      {"indoor_closed": 1, "outdoor_closed": 1},
    "tier_dec_4":      {"indoor_closed": 1, "outdoor_closed": 1},
    "local_mixing":    {"mix_ban": 1},
    "local_mixing_ne": {"mix_ban": 1, "curfew": 1, "table_service": 1},
    "w_6pm_no_alcohol": {"early_close_no_alcohol": 1, "group_limit": 1},
}

# National timelines: (first day, state label, measure, source)
ENGLAND = [
    (date(2020, 3, 1), "E_open", "open", ""),
    (date(2020, 3, 21), "E_lockdown1", "closed", "SI 2020/327 (in force 2pm 21 Mar 2020); SI 2020/350"),
    (date(2020, 7, 4), "E_reopened", "open", "SI 2020/684 (00:01 4 Jul 2020)"),
    (date(2020, 9, 14), "E_rule_of_six", "group", "SI 2020/986 (14 Sep 2020)"),
    (date(2020, 9, 24), "E_curfew", "curfew", "SI 2020/1029 (05:00 24 Sep 2020); SI 2020/1008, 1046"),
    (date(2020, 10, 14), "E_tier_oct_1", "tier_oct_1", "SI 2020/1103 Medium (14 Oct 2020)"),
    (date(2020, 11, 5), "E_lockdown2", "closed", "SI 2020/1200 (5 Nov 2020)"),
    (date(2020, 12, 2), "E_tier_dec_1", "tier_dec_1", "SI 2020/1374 (2 Dec 2020)"),
    (date(2021, 1, 6), "E_lockdown3", "closed", "SI 2021/8: Tier 4 applied to all England (6 Jan 2021)"),
    (date(2021, 3, 29), "E_step1", "closed", "SI 2021/364 Steps, Step 1 (29 Mar 2021)"),
    (date(2021, 4, 12), "E_step2", "outdoor_only", "SI 2021/364 Sch 4 Step 2 area (12 Apr 2021)"),
    (date(2021, 5, 17), "E_step3", "table_group", "SI 2021/585 (17 May 2021)"),
    (date(2021, 7, 19), "E_step4", "open", "SI 2021/848 revoked Steps Regs (23:55 18 Jul 2021)"),
]
WALES = [
    (date(2020, 3, 1), "W_open", "open", ""),
    (date(2020, 3, 21), "W_lockdown1", "closed", "WSI 2020/326 (21 Mar 2020); WSI 2020/353"),
    (date(2020, 7, 13), "W_outdoor_hospitality", "outdoor_only", "WSI 2020/725 (13 Jul 2020)"),
    (date(2020, 8, 3), "W_indoor_reopened", "group", "WSI 2020/820 (3 Aug 2020); indoor mixing limited to extended household"),
    (date(2020, 9, 24), "W_curfew", "curfew", "WSI 2020/1035 (6pm 24 Sep 2020)"),
    (date(2020, 10, 23), "W_firebreak", "closed", "WSI 2020/1149 (6pm 23 Oct - end of 8 Nov 2020)"),
    (date(2020, 11, 9), "W_post_firebreak", "curfew", "WSI 2020/1219 (9 Nov 2020): groups of 4, close 22:20"),
    (date(2020, 12, 4), "W_6pm_no_alcohol", "w_6pm_no_alcohol", "WSI 2020/1409 (6pm 4 Dec 2020)"),
    (date(2020, 12, 20), "W_alert4", "closed", "WSI 2020/1609 as amended by WSI 2020/1610 (Alert Level 4 from 20 Dec 2020)"),
    (date(2021, 4, 26), "W_outdoor_hospitality", "outdoor_only", "WSI 2021/502 (6am 26 Apr 2021)"),
    (date(2021, 5, 17), "W_alert2_1", "table_group", "WSI 2021/583 (6am 17 May 2021, Alert Level 2; Level 1 from 7 Jun, WSI 2021/668)"),
    (date(2021, 8, 7), "W_alert0", "open", "WSI 2021/925 (6am 7 Aug 2021, no alert level)"),
    (date(2021, 12, 26), "W_alert2", "table_group", "WSI 2021/1485 (6am 26 Dec 2021, Alert Level 2)"),
]


def intensity(f):
    if f["indoor_closed"] and f["outdoor_closed"]:
        return 1.0
    if f["indoor_closed"]:
        return 0.75
    if f["meal_req"] or f["mix_ban"] or f["early_close_no_alcohol"]:
        return 0.5
    if f["curfew"] or f["table_service"] or f["group_limit"]:
        return 0.25
    return 0.0


def flags_of(*measures):
    f = dict.fromkeys(FLAGS, 0)
    for m in measures:
        for k, v in M[m].items():
            f[k] = max(f[k], v)
    return f


def national(timeline, d):
    return [x for x in timeline if x[0] <= d][-1]


def build_ltla20():
    lt = ltla20()
    legal = pd.read_csv(CLEAN / "b4_legal_areas.csv", parse_dates=["date"])
    legal["date"] = legal.date.dt.date
    leg = {k: g for k, g in legal.groupby(["date", "ltla20_code"])}
    rows = []
    d = START
    while d <= END:
        for la, nation in zip(lt.ltla20_code, lt.nation):
            tl = ENGLAND if nation == "E" else WALES
            _, state, meas, src = national(tl, d)
            tier = {"tier_oct_1": 1, "tier_dec_1": 1}.get(meas, np.nan)
            if state == "E_lockdown3":
                tier = 4
            base = flags_of(meas)
            loc_state, loc_meas, share, loc_src = None, None, 0.0, ""
            g = leg.get((d, la))
            if g is not None:
                # most restrictive local measure in force (tiers replace the default tier of the period)
                order = ["E_leicester_closure", "E_bolton_closure", "E_tier_dec_4", "E_tier_dec_3", "E_tier_dec_2",
                         "E_tier_oct_3", "E_tier_oct_2", "E_local_mixing", "W_lhpa", "E_local_leisure"]
                g = g.assign(o=g.measure.map(order.index)).sort_values("o")
                r = g.iloc[0]
                loc_state, share, loc_src = r.measure, float(r.share), f"{r.source}" + (f" ({r.note})" if isinstance(r.note, str) and r.note else "")
                if r.measure in ("E_leicester_closure", "E_bolton_closure"):
                    loc_meas = "closed"
                elif r.measure.startswith("E_tier"):
                    loc_meas = r.measure[2:]
                elif r.measure == "E_local_mixing":
                    loc_meas = "local_mixing_ne" if "1010" in r.source else "local_mixing"
                elif r.measure == "W_lhpa":
                    loc_meas = "local_mixing"
                else:                                   # leisure closures only: no hospitality effect
                    loc_meas = None
                if r.measure == "E_local_leisure":
                    share = 0.0
            if loc_meas:
                # tiers replace the period's default tier; other local measures add to the national rules
                fl = flags_of(loc_meas) if loc_meas.startswith("tier") else flags_of(meas, loc_meas)
                i_loc, i_base = intensity(fl), intensity(base)
                inten = share * i_loc + (1 - share) * i_base
                if share >= 0.5:
                    state_out = loc_state
                    if loc_meas.startswith("tier"):
                        tier = int(loc_meas[-1])
                else:
                    state_out = state
                    fl = base
                src_out = loc_src + ("; " + src if src and share < 1 else "")
            else:
                fl, inten, state_out, src_out = base, intensity(base), state, src
            rows.append((la, nation, d, state_out, tier, inten, share if loc_meas else 0.0,
                         loc_state if loc_meas and share < 1 else "", *[fl[k] for k in FLAGS], src_out))
        d += timedelta(days=1)
    df = pd.DataFrame(rows, columns=["ltla20_code", "nation", "date", "state", "tier", "hosp_intensity",
                                     "local_share", "partial_local_measure", *FLAGS, "source"])
    df = df.merge(lt[["ltla20_code", "ltla20_name"]], on="ltla20_code")
    return df


def lookup_2023():
    """2020 LTLA -> 2023 LAD, with 2020 population weights (ONS 2018-based SNPP, 2020 projection)."""
    lt = ltla20()
    merge = {
        "E06000061": ["E07000150", "E07000152", "E07000153", "E07000156"],      # North Northamptonshire (Apr 2021)
        "E06000062": ["E07000151", "E07000154", "E07000155"],                   # West Northamptonshire (Apr 2021)
        "E06000063": ["E07000026", "E07000028", "E07000029"],                   # Cumberland (Apr 2023)
        "E06000064": ["E07000027", "E07000030", "E07000031"],                   # Westmorland and Furness (Apr 2023)
        "E06000065": ["E07000163", "E07000164", "E07000165", "E07000166", "E07000167", "E07000168", "E07000169"],
        "E06000066": ["E07000187", "E07000188", "E07000189", "E07000246"],      # Somerset (Apr 2023)
    }
    inv = {o: n for n, olds in merge.items() for o in olds}
    m = lt[["ltla20_code", "ltla20_name"]].copy()
    m["lad23_code"] = m.ltla20_code.map(inv).fillna(m.ltla20_code)
    m["pop2020"] = m.ltla20_code.map(pop2020())  # ONS 2018-based SNPP 2020 projection (England)
    single = m.groupby("lad23_code").ltla20_code.transform("size") == 1
    m.loc[single & m.pop2020.isna(), "pop2020"] = 1.0      # Wales: not merged, weight 1
    if m.pop2020.isna().any():
        raise ValueError(f"missing 2020 population for {m[m.pop2020.isna()].ltla20_code.tolist()}")
    m["weight"] = m.pop2020 / m.groupby("lad23_code").pop2020.transform("sum")
    lad = la_region_lookup()
    # the ONS file carries footnote markers on the Northamptonshire rows
    lad["la_code"] = lad.la_code.astype(str).str.extract(r"([EW]\d{8})", expand=False)
    lad["la_name"] = lad.la_name.astype(str).str.replace(r"[^\w\s,'.()-]", "", regex=True).str.strip()
    m = m.merge(lad.rename(columns={"la_code": "lad23_code", "la_name": "lad23_name"}), on="lad23_code", how="left")
    assert m.lad23_name.notna().all(), m[m.lad23_name.isna()]
    assert m.lad23_code.nunique() == 318
    return m


def to_2023(daily, m):
    x = daily.merge(m[["ltla20_code", "lad23_code", "lad23_name", "region", "weight"]], on="ltla20_code")
    num = ["hosp_intensity", "local_share", *FLAGS]
    for c in num:
        x[c] = x[c] * x.weight
    agg = x.groupby(["lad23_code", "date"], as_index=False)[num].sum()
    # categorical: state / tier / source of the predecessor with the largest population on that day's state
    x = x.sort_values(["lad23_code", "date", "weight"], ascending=[True, True, False])
    cat = x.groupby(["lad23_code", "date"], as_index=False).agg(
        lad23_name=("lad23_name", "first"), region=("region", "first"), nation=("nation", "first"),
        state=("state", "first"), tier=("tier", "first"), source=("source", "first"),
        partial_local_measure=("partial_local_measure", "first"),
        n_pred=("ltla20_code", "size"), n_states=("state", "nunique"))
    out = cat.merge(agg, on=["lad23_code", "date"])
    out["predecessors_differ"] = (out.n_states > 1).astype(int)
    out = out.drop(columns="n_states")
    for c in ["hosp_intensity", "local_share", *FLAGS]:
        out[c] = out[c].round(4)
    cols = ["lad23_code", "lad23_name", "region", "nation", "date", "state", "tier", "hosp_intensity", *FLAGS,
            "local_share", "partial_local_measure", "n_pred", "predecessors_differ", "source"]
    return out[cols].sort_values(["lad23_code", "date"]).reset_index(drop=True)


def quarterly(d23):
    q = d23.copy()
    q["date"] = pd.to_datetime(q.date)
    q["quarter"] = q.date.dt.to_period("Q").astype(str)
    g = q.groupby(["lad23_code", "lad23_name", "region", "nation", "quarter"], as_index=False).agg(
        n_days_panel=("hosp_intensity", "size"), sum_int=("hosp_intensity", "sum"),
        days_full_closure=("hosp_intensity", lambda s: int((s >= 0.999).sum())),
        days_any_restriction=("hosp_intensity", lambda s: int((s > 0).sum())))
    per = pd.PeriodIndex(g.quarter, freq="Q")
    g["n_days_quarter"] = (per.end_time.normalize() - per.start_time.normalize()).days + 1
    # 2020Q1: 1 Jan - 29 Feb 2020 had no restrictions (intensity 0), so the calendar-quarter mean counts them as 0
    g["hosp_intensity_q"] = (g.sum_int / g.n_days_quarter).round(4)
    g["hosp_intensity_panel_days"] = (g.sum_int / g.n_days_panel).round(4)
    return g.drop(columns="sum_int")


def main():
    daily = build_ltla20()
    daily.to_csv(CLEAN / "b4_restrictions_daily_ltla20.csv.gz", index=False)
    m = lookup_2023()
    m.to_csv(CLEAN / "b4_ltla20_to_lad23.csv", index=False)
    d23 = to_2023(daily, m)
    d23.to_csv(CLEAN / "b4_restrictions_daily_lad23.csv", index=False)
    q = quarterly(d23)
    q.to_csv(CLEAN / "b4_restrictions_quarterly_lad23.csv", index=False)
    print("daily ltla20", daily.shape, "daily lad23", d23.shape, "quarterly", q.shape)
    print(q.pivot_table(index="quarter", columns="nation", values="hosp_intensity_q", aggfunc="mean").round(3))


if __name__ == "__main__":
    main()
