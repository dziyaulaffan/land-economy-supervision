"""B3 mobility: Google COVID-19 Community Mobility Reports mapped to 2023 LADs, England and Wales.

Same source and series as scripts/50_mobility.py (regional CSVs, GB; retail_and_recreation and workplaces; daily
15 Feb 2020 to 15 Oct 2022; % change versus the 3 Jan-6 Feb 2020 day-of-week median baseline). The GB extract the
pilot wrote (PILOT_RAW/google_mobility/GB_Region_Mobility_Report_2020_2022.csv) is read, not rewritten.

Mapping types (one row per 2023 LAD in b3_mobility_google_to_lad_map.csv):
  direct            one Google region whose area is the LAD (district, unitary, metropolitan or London borough);
  county_equals_lad Google county-level series whose area equals a 2023 unitary (Buckinghamshire, North Yorkshire,
                    Somerset); Google's pre-2023 district series inside it are not used;
  composite         2023 unitary formed from pre-2023 districts that Google reports separately and whose county series
                    covers more than the LAD (Cumberland, Westmorland and Furness, North and West Northamptonshire,
                    East Suffolk): daily population-weighted mean of the district series (Census 2011 usual
                    residents, Nomis NM_503_1), weights renormalised over districts with data that day;
  broader_region    the only series available covers a larger area (Shropshire: Google's Shropshire aggregate also
                    contains Telford and Wrekin, which has its own series);
  missing           no Google series (Isles of Scilly).
"""
import re

import numpy as np
import pandas as pd

from b3_migration import lookup
from ext_config import CLEAN, PILOT_RAW, RAW, download

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
SERIES = {"retail_and_recreation_percent_change_from_baseline": "retail_recreation",
          "workplaces_percent_change_from_baseline": "workplaces"}
START, END = pd.Timestamp("2020-02-15"), pd.Timestamp("2022-10-15")
COMPOSITE = {  # 2023 LAD -> (Google sub_region_1, [sub_region_2 districts], {district: 2011 LA code})
    "E06000063": ("Cumbria", {"Allerdale District": "E07000026", "City of Carlisle": "E07000028",
                              "Copeland District": "E07000029"}),
    "E06000064": ("Cumbria", {"Barrow-in-Furness District": "E07000027", "Eden District": "E07000030",
                              "South Lakeland District": "E07000031"}),
    "E06000061": ("Northamptonshire", {"Corby District": "E07000150", "East Northamptonshire": "E07000152",
                                       "Borough of Kettering": "E07000153", "Borough of Wellingborough": "E07000156"}),
    "E06000062": ("Northamptonshire", {"Daventry District": "E07000151", "Northampton District": "E07000154",
                                       "South Northamptonshire District": "E07000155"}),
    "E07000244": ("Suffolk", {"Suffolk Coastal District": "E07000205", "Waveney District": "E07000206"}),
}
SPECIAL = {"bristol city": "bristol", "rhondda cynon taff": "rhondda cynon taf"}


def norm(s: str) -> str:
    s = str(s).lower().replace("&", "and")
    s = re.sub(r",\s*(city|county) of$", "", s)
    s = re.sub(r"^(london borough of|royal borough of|metropolitan borough of|borough of|city of)\s+", "", s)
    s = re.sub(r"\s+(district|council|principal area|principle area|county borough|borough)$", "", s)
    s = s.replace("saint ", "st ").replace(".", "").replace("'", "").replace(",", "")
    s = re.sub(r"\s+", " ", s).strip()
    return SPECIAL.get(s, s)


def census2011_pop(codes):
    url = (f"{NOMIS}/NM_503_1.data.csv?geography={','.join(sorted(codes))}&rural_urban=0&c_age=0&measures=20100"
           "&select=geography_code,geography_name,obs_value")
    p = pd.read_csv(download(url, RAW / "nomis" / "census2011_qs103_total_pre2023_districts.csv"))
    return p.set_index("GEOGRAPHY_CODE").OBS_VALUE


def main():
    lk = lookup()
    gb = pd.read_csv(PILOT_RAW / "google_mobility" / "GB_Region_Mobility_Report_2020_2022.csv", dtype=str)
    gb = gb[gb.sub_region_1.notna()].copy()
    gb["date"] = pd.to_datetime(gb.date)
    for c in SERIES:
        gb[c] = pd.to_numeric(gb[c])
    gb = gb.rename(columns=SERIES)
    gb["sub_region_2"] = gb.sub_region_2.fillna("")
    reg = gb.groupby(["sub_region_1", "sub_region_2"], as_index=False).agg(
        iso_3166_2_code=("iso_3166_2_code", "first"), place_id=("place_id", "first"), n_days=("date", "size"),
        rr_valid=("retail_recreation", "count"), wp_valid=("workplaces", "count"))
    reg["level"] = np.where(reg.sub_region_2 == "", "sub_region_1", "sub_region_2")
    reg["name"] = np.where(reg.level == "sub_region_2", reg.sub_region_2, reg.sub_region_1)
    reg["key"] = reg.name.map(norm)

    lk["key"] = lk.la_name.map(norm)
    name2lad = dict(zip(lk.key, lk.la_code))
    reg["lad_direct"] = reg.key.map(name2lad)
    # Google's "Dorset" county aggregate (GB-DOR) also covers BCP; Dorset UA is the sub_region_2 "Dorset" series.
    reg.loc[(reg.sub_region_1 == "Dorset") & (reg.level == "sub_region_1"), "lad_direct"] = np.nan
    # Google's "Shropshire" aggregate covers Shropshire UA and Telford and Wrekin: kept as broader_region.
    shrop = (reg.sub_region_1 == "Shropshire") & (reg.level == "sub_region_1")
    reg.loc[shrop, "lad_direct"] = np.nan

    rows = []
    for _, la in lk.iterrows():
        c = la.la_code
        hit = reg[reg.lad_direct == c]
        if c in COMPOSITE:
            s1, parts = COMPOSITE[c]
            rows.append(dict(la_code=c, mapping_type="composite", google_sub_region_1=s1,
                             google_sub_region_2="; ".join(parts), n_google_regions=len(parts)))
        elif len(hit) == 1:
            h = hit.iloc[0]
            mt = "county_equals_lad" if c in {"E06000060", "E06000065", "E06000066"} else "direct"
            rows.append(dict(la_code=c, mapping_type=mt, google_sub_region_1=h.sub_region_1,
                             google_sub_region_2=h.sub_region_2, n_google_regions=1))
        elif len(hit) > 1:
            raise ValueError(f"{la.la_name}: several Google regions {hit.name.tolist()}")
        elif c == "E06000051":
            rows.append(dict(la_code=c, mapping_type="broader_region", google_sub_region_1="Shropshire",
                             google_sub_region_2="", n_google_regions=1))
        else:
            rows.append(dict(la_code=c, mapping_type="missing", google_sub_region_1="", google_sub_region_2="",
                             n_google_regions=0))
    mp = lk[["la_code", "la_name", "region"]].merge(pd.DataFrame(rows), on="la_code")
    note = {"composite": "population-weighted mean of pre-2023 district series (Census 2011 weights)",
            "county_equals_lad": "Google county series; area equals the 2023 unitary",
            "broader_region": "Google Shropshire aggregate, also covers Telford and Wrekin",
            "missing": "no Google series", "direct": ""}
    mp["note"] = mp.mapping_type.map(note)
    mp.loc[mp.la_code == "E06000052", "note"] = "Google Cornwall (GB-CON); sub-LA area 'Penryn' not used"
    mp.loc[mp.la_code == "E06000059", "note"] = "Google 'Dorset' sub_region_2 series (Dorset UA); GB-DOR county aggregate not used"

    # daily series per LAD
    w = census2011_pop({code for _, parts in COMPOSITE.values() for code in parts.values()})
    dates = pd.date_range(START, END, freq="D")
    out = []
    for _, m in mp.iterrows():
        if m.mapping_type == "missing":
            continue
        if m.mapping_type == "composite":
            s1, parts = COMPOSITE[m.la_code]
            x = gb[(gb.sub_region_1 == s1) & gb.sub_region_2.isin(parts)].copy()
            assert x.sub_region_2.nunique() == len(parts), (m.la_name, x.sub_region_2.unique())
            x["w"] = x.sub_region_2.map(parts).map(w)
            res = {}
            for s in SERIES.values():
                v = x.dropna(subset=[s])
                g = v.assign(wy=v.w * v[s]).groupby("date")
                res[s] = g.wy.sum() / g.w.sum()
                res[f"{s}_weight_share"] = g.w.sum() / sum(w[p] for p in parts.values())
            d = pd.DataFrame(res).reindex(dates)
        else:
            x = gb[(gb.sub_region_1 == m.google_sub_region_1) & (gb.sub_region_2 == m.google_sub_region_2)]
            d = x.set_index("date")[list(SERIES.values())].reindex(dates)
            for s in SERIES.values():
                d[f"{s}_weight_share"] = d[s].notna().astype(float)
        d = d.rename_axis("date").reset_index()
        d.insert(0, "la_code", m.la_code)
        d["mapping_type"] = m.mapping_type
        out.append(d)
    daily = pd.concat(out, ignore_index=True)
    daily.to_parquet(CLEAN / "b3_mobility_daily_lad.parquet", index=False)

    # Google regions in England and Wales not used, with the reason
    used = set(zip(mp.google_sub_region_1, mp.google_sub_region_2))
    used |= {(s1, p) for s1, parts in COMPOSITE.values() for p in parts}
    sn = SCOT_NI_NAMES(reg)
    print(f"Scottish/NI Google regions (expected 43): {len(sn)}: {sorted(sn)}")
    scot_ni = reg.sub_region_1.isin(sn)
    reg["used"] = [(a, b) in used for a, b in zip(reg.sub_region_1, reg.sub_region_2)]
    unused = reg[~reg.used & ~scot_ni].copy()
    unused["reason"] = np.where(unused.level == "sub_region_1", "county or metropolitan-county aggregate",
                                "pre-2023 district inside a county-level series that equals the 2023 unitary")
    unused.loc[unused.sub_region_2 == "Penryn", "reason"] = "sub-LA area (town)"
    unused[["sub_region_1", "sub_region_2", "iso_3166_2_code", "rr_valid", "wp_valid", "reason"]].to_csv(
        CLEAN / "b3_mobility_google_regions_not_used.csv", index=False)

    # coverage per LAD
    cov = daily.groupby("la_code").agg(rr_valid_days=("retail_recreation", "count"),
                                       wp_valid_days=("workplaces", "count"))
    mp = mp.merge(cov, on="la_code", how="left").fillna({"rr_valid_days": 0, "wp_valid_days": 0})
    mp["window_days"] = len(dates)
    mp.to_csv(CLEAN / "b3_mobility_google_to_lad_map.csv", index=False)

    # quarterly LA x quarter (all of 2020Q1-2022Q4; 2020Q1 starts 15 Feb, 2022Q4 ends 15 Oct)
    daily["quarter"] = daily.date.dt.to_period("Q").astype(str)
    q = daily.groupby(["la_code", "quarter"]).agg(
        mob_retail_recreation=("retail_recreation", "mean"), mob_rr_valid_days=("retail_recreation", "count"),
        mob_workplaces=("workplaces", "mean"), mob_wp_valid_days=("workplaces", "count"),
        mob_window_days=("date", "size")).reset_index()
    q = q.merge(mp[["la_code", "mapping_type"]].rename(columns={"mapping_type": "mob_mapping_type"}), on="la_code")
    q.to_csv(CLEAN / "b3_mobility_quarterly_lad.csv", index=False)
    print(mp.mapping_type.value_counts().to_string())
    print(mp[mp.mapping_type != "direct"][["la_name", "mapping_type", "google_sub_region_1",
                                           "google_sub_region_2", "rr_valid_days"]].to_string(index=False))
    print(f"unused E&W Google regions: {len(unused)}")
    print(f"daily rows {len(daily)}, LADs {daily.la_code.nunique()}; quarterly rows {len(q)}")


def SCOT_NI_NAMES(reg):
    """Scottish and Northern Irish Google regions: sub_region_1 rows that match no E&W LAD and are not E&W counties."""
    ew_counties = {"Buckinghamshire", "Cambridgeshire", "Cornwall", "Cumbria", "Derbyshire", "Devon", "Dorset",
                   "East Sussex", "Essex", "Gloucestershire", "Greater London", "Greater Manchester", "Hampshire",
                   "Hertfordshire", "Kent", "Lancashire", "Leicestershire", "Lincolnshire", "Merseyside", "Norfolk",
                   "North Yorkshire", "Northamptonshire", "Nottinghamshire", "Oxfordshire", "Shropshire", "Somerset",
                   "South Yorkshire", "Staffordshire", "Suffolk", "Surrey", "Tyne and Wear", "Warwickshire",
                   "West Midlands", "West Sussex", "West Yorkshire", "Worcestershire"}
    s1 = reg[reg.level == "sub_region_1"]
    return set(s1[s1.lad_direct.isna() & ~s1.sub_region_1.isin(ew_counties)].sub_region_1)


if __name__ == "__main__":
    main()
