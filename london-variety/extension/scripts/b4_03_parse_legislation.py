"""B4 step 3: read the area lists out of the downloaded regulations.

Output: CLEAN/b4_legal_areas.csv, one row per (date, measure, 2020 LTLA) where a local measure listed in the
regulations was in force at the end of that day, with the population share of the LTLA covered (1 unless the
regulation listed only some wards or electoral divisions) and the SI it comes from.

Measures (see notes/B4_restrictions.md for the hospitality content of each):
  E_tier_oct_2 / E_tier_oct_3   Local COVID Alert Level High / Very High (SI 2020/1104, 2020/1105), 14 Oct - 4 Nov 2020
  E_tier_dec_2 / _3 / _4        All Tiers Regulations (SI 2020/1374) Schedule 4, 2 Dec 2020 - 5 Jan 2021
  E_leicester_closure           Leicester Regulations (SI 2020/685), hospitality closed, 4 Jul - 2 Aug 2020
  E_bolton_closure              Bolton Regulations (SI 2020/974), hospitality takeaway only, 10 Sep - 2 Oct 2020
  E_local_mixing                gatherings bans in private dwellings (from 30 Sep 2020 all indoor places in the
                                North of England / North East and North West areas): SI 2020/822, 824, 828, 988, 1010
  E_local_leisure               Blackburn with Darwen and Luton (SI 2020/800): leisure closures only, no hospitality rule
  W_lhpa                        Welsh local health protection areas (SI 2020/725 Schedule 4A), Sep - Oct 2020
"""
import re
from datetime import date, timedelta

import pandas as pd

from b4_common import LEG, ltla20, resolve, ward_share, xml_items, norm
from ext_config import CLEAN


def daterange(d0, d1):
    d = d0
    while d <= d1:
        yield d
        d += timedelta(days=1)


# ---------------------------------------------------------------- tier schedules (October and December 2020)
def parse_tier_schedule(path, default_tier=None):
    """Return list of (tier, ltla20_code, share, note) from a point-in-time tier schedule."""
    rows, tier, partial_for, wards = [], default_tier, None, []

    def flush():
        nonlocal partial_for, wards
        if partial_for:
            code = resolve(partial_for)[0]
            share, miss = ward_share(code, wards)
            rows.append((tier, code, share, f"wards of {partial_for}: {'; '.join(wards)}"
                         + (f" [unmatched: {'; '.join(miss)}]" if miss else "")))
        partial_for, wards = None, []

    for kind, t, raw in xml_items(path):
        if kind == "title":
            m = re.search(r"Tier (\d) area", t)
            if m:
                flush()
                tier = int(m.group(1))
            continue
        if "<Emphasis>" in raw and "Council" not in t:      # county / region heading
            flush()
            continue
        if t.startswith("The areas of the following") or t.startswith("There are no areas"):
            continue
        m = re.match(r"In the area of (.+?Council), the following", t)
        if m:
            flush()
            partial_for = m.group(1)
            continue
        try:
            codes = resolve(t)
        except KeyError:
            codes = None
            if "Council" in t:
                raise
        if codes:
            flush()
            for c in codes:
                rows.append((tier, c, 1.0, ""))
            continue
        if partial_for:
            wards.append(t.rstrip(";,."))
            continue
        if t.startswith("Sch.") or t.startswith("Words") or "in force at" in t:
            continue
        raise ValueError(f"unparsed item in {path.name}: {t!r}")
    flush()
    return rows


def tiers():
    out = []
    pit = LEG / "pit"
    for d in daterange(date(2020, 10, 14), date(2020, 11, 4)):
        for si, tier in [("1104", 2), ("1105", 3)]:
            f = pit / f"uksi_2020_{si}_schedule2_{d.isoformat()}.xml"
            for t, c, sh, note in parse_tier_schedule(f, tier):
                out.append((d, f"E_tier_oct_{t}", c, sh, f"SI 2020/{si} Sch 2", note))
    for d in daterange(date(2020, 12, 2), date(2021, 1, 5)):
        f = pit / f"uksi_2020_1374_schedule4_{d.isoformat()}.xml"
        for t, c, sh, note in parse_tier_schedule(f):
            out.append((d, f"E_tier_dec_{t}", c, sh, "SI 2020/1374 Sch 4", note))
    return out


# ---------------------------------------------------------------- England local measures, July - October 2020
LOCAL_DATES = ["2020-07-04", "2020-07-18", "2020-07-24", "2020-07-25", "2020-08-01", "2020-08-03", "2020-08-05",
               "2020-08-08", "2020-08-15", "2020-08-19", "2020-08-26", "2020-09-02", "2020-09-03", "2020-09-08",
               "2020-09-10", "2020-09-15", "2020-09-18", "2020-09-22", "2020-09-24", "2020-09-26", "2020-09-30",
               "2020-10-03", "2020-10-13"]
LOCAL_MEASURE = {"685": "E_leicester_closure", "974": "E_bolton_closure", "800": "E_local_leisure",
                 "822": "E_local_mixing", "824": "E_local_mixing", "828": "E_local_mixing", "988": "E_local_mixing",
                 "1010": "E_local_mixing"}


def protected_area(path):
    """Areas in the 'protected area' definition of a local regulation (whole text, point in time).
    Returns list of (ltla20_code, share, note); empty if the regulation is revoked or not yet in force."""
    items = xml_items(path)
    start = next((i for i, (k, t, raw) in enumerate(items) if re.search(r"protected area.{0,3} means", t)), None)
    if start is None:
        return []
    rows, partial, wards = [], None, []

    def flush():
        nonlocal partial, wards
        if partial:
            code = resolve(partial)[0]
            share, miss = ward_share(code, wards)
            rows.append((code, share, f"wards of {partial}: {'; '.join(wards)}"
                         + (f" [unmatched: {'; '.join(miss)}]" if miss else "")))
        partial, wards = None, []

    first = items[start][1]
    seg = [first[first.find("means") + 5:]] + [t for k, t, raw in items[start + 1:start + 80]]
    for t in seg:
        if re.match(r"^\W*(public outdoor place|vulnerable person|change of protected area|child)", t)                 or t.startswith("But this is subject") or t.startswith("Interpretation") or t.startswith("In this Part"):
            break
        for part in re.split(r",? or (?=the area of|in the area of)", t):
            part = part.strip()
            m = re.match(r"(?:in )?the area of (?:the )?(.+?Council|Borough of Oadby and Wigston), the following wards", part)
            if m:
                flush()
                partial = m.group(1)
                continue
            m = re.match(r"(?:\w{1,3} )?the area of (?:the )?(.+?(?:Council|Oadby and Wigston))", part)
            if m:
                flush()
                rows += [(c, 1.0, "") for c in resolve(m.group(1))]
                continue
            if partial and part and not part.startswith("the area falling"):
                w = re.sub(r"(,? and|,? or|[,;.])+$", "", part).strip()
                if w:
                    wards.append(w)
    flush()
    return rows


def england_local():
    out = []
    pit = LEG / "pit_local"
    dates = [date.fromisoformat(d) for d in LOCAL_DATES]
    for si, measure in LOCAL_MEASURE.items():
        states = {}
        for d in dates:
            f = pit / f"uksi_2020_{si}_{d.isoformat()}.xml"
            states[d] = protected_area(f) if f.exists() else []
        if si == "685":
            # 4-17 July the Leicester protected area was defined by postcodes (Schedule 1): the whole of Leicester
            # and Oadby and Wigston, plus suburban fringes of Blaby and Charnwood (not coded, see notes).
            states[date(2020, 7, 4)] = [("E06000016", 1.0, "postcode-defined area"),
                                        ("E07000135", 1.0, "postcode-defined area")]
        for d in daterange(date(2020, 7, 4), date(2020, 10, 13)):
            key = max(x for x in dates if x <= d)
            for c, sh, note in states[key]:
                out.append((d, measure, c, sh, f"SI 2020/{si}", note))
    return out


# ---------------------------------------------------------------- Wales local health protection areas
def wales_lhpa():
    out = []
    pit = LEG / "pit"
    for d in daterange(date(2020, 9, 8), date(2020, 10, 22)):
        f = pit / f"wsi_2020_725_schedule4A_{d.isoformat()}.xml"
        if not f.exists():
            continue
        items = xml_items(f)
        in_part1, partial, wards = False, None, []
        rows = []

        def flush():
            nonlocal partial, wards
            if partial:
                code = resolve(partial)[0]
                share, miss = ward_share(code, wards)
                rows.append((code, share, f"electoral divisions of {partial}: {'; '.join(wards)}"
                             + (f" [unmatched: {'; '.join(miss)}]" if miss else "")))
            partial, wards = None, []

        for k, t, raw in items:
            if k == "title":
                if "Local health protection area" in t:
                    in_part1 = True
                elif in_part1:
                    flush()
                    in_part1 = False
                continue
            m = re.match(r"For the purposes of these Regulations, (.+?) is a local health protection area", t)
            if in_part1 and m:                      # 8-16 Sep 2020 wording (Caerphilly only)
                rows += [(c, 1.0, "") for c in resolve(m.group(1))]
                in_part1 = False
                continue
            if not in_part1 or t.startswith("For the purposes"):
                continue
            m = re.search(r"electoral (?:divisions|wards) in the (?:county|county borough) of (\w+)", t)
            if m:
                flush()
                partial = m.group(1)
                continue
            nm = t.rstrip(";.")
            try:
                codes = resolve(nm)
            except KeyError:
                if partial:
                    wards.append(nm)
                    continue
                raise
            flush()
            rows += [(c, 1.0, "") for c in codes]
        flush()
        for c, sh, note in rows:
            out.append((d, "W_lhpa", c, sh, "WSI 2020/725 Sch 4A", note))
    return out


def main():
    rows = tiers() + england_local() + wales_lhpa()
    df = pd.DataFrame(rows, columns=["date", "measure", "ltla20_code", "share", "source", "note"])
    df = df.drop_duplicates(["date", "measure", "ltla20_code"])
    lt = ltla20().set_index("ltla20_code")
    assert df.ltla20_code.isin(lt.index).all()
    df["ltla20_name"] = df.ltla20_code.map(lt.ltla20_name)
    df.to_csv(CLEAN / "b4_legal_areas.csv", index=False)
    print(df.groupby("measure").agg(days=("date", "nunique"), las=("ltla20_code", "nunique"), rows=("date", "size")))
    p = df[df.share < 1].drop_duplicates(["measure", "ltla20_code", "note"])
    print(p[["measure", "ltla20_name", "share", "note"]].to_string()[:4000])


if __name__ == "__main__":
    main()
