"""Shared helpers for the B4 restrictions build: 2020 LTLA geography, council-name resolver, legislation XML text."""
import re
from functools import lru_cache

import pandas as pd

from ext_config import RAW

R = RAW / "restrictions"
LEG = R / "legislation"


@lru_cache()
def ltla20() -> pd.DataFrame:
    """336 LTLAs of December 2020 (England 314, Wales 22) with their UTLA."""
    d = pd.read_csv(R / "geography" / "ltla20_utla20.csv")
    d.columns = ["ltla20_code", "ltla20_name", "utla20_code", "utla20_name"]
    d["nation"] = d.ltla20_code.str[0]
    return d.sort_values("ltla20_code").reset_index(drop=True)


def norm(s: str) -> str:
    """Normalise a council or area name so that legislation names match ONS names."""
    s = re.sub(r"(;\s*|\s+)(and|or)$", "", s.strip())
    s = s.replace("&amp;", " and ").replace("&", " and ").replace("’", "'").lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[.,;:'—–\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for p in ["the common council in respect of the ", "council of the ", "the ", "london borough of ",
              "royal borough of ", "city and county borough of ", "city and county of ", "county borough of ", "borough of ", "county of ",
              "area of ", "city of "]:
        if s.startswith(p):
            s = s[len(p):]
    for suf in [" city and district council", " metropolitan borough council", " metropolitan district council", " metropolitan council",
                " county borough council", " county council", " borough council", " city council",
                " district council", " council", " county borough", " city of", " county of", " county"]:
        if s.endswith(suf):
            s = s[: -len(suf)]
    s = s.strip()
    alias = {"hull": "kingston upon hull", "durham": "county durham", "london": "city of london",
             "bradford": "bradford", "st helens": "st helens", "southend on sea": "southend on sea",
             "kings lynn and west norfolk": "king s lynn and west norfolk", "newark and sherwood": "newark and sherwood",
             "rhondda cynon taff": "rhondda cynon taf", "anglesey": "isle of anglesey",
             "newcastle": "newcastle upon tyne"}
    return alias.get(s, s)


@lru_cache()
def _name_index():
    d = ltla20()
    lt = {norm(n): [c] for n, c in zip(d.ltla20_name, d.ltla20_code)}
    ut = {}
    for (uc, un), g in d.groupby(["utla20_code", "utla20_name"]):
        ut[norm(un)] = list(g.ltla20_code)
    return lt, ut


def resolve(name: str):
    """Council name as written in a schedule -> list of 2020 LTLA codes (county councils expand to districts)."""
    if "sub-treasurer" in name.lower() or "inner temple" in name.lower():
        return ["E09000001"]
    if "common council" in name.lower():
        return ["E09000001"]
    k = norm(name)
    lt, ut = _name_index()
    if k in lt:
        return lt[k]
    if k in ut:
        return ut[k]
    raise KeyError(f"unresolved council name: {name!r} -> {k!r}")


def xml_items(path):
    """Ordered (kind, text, raw) tuples from a legislation.gov.uk XML file: kind is 'title' or 'text'.
    Commentaries (footnotes on amendments) are dropped; repealed text shows as dots and is skipped."""
    x = path.read_text(encoding="utf8")
    x = re.sub(r"<Commentaries>.*?</Commentaries>", "", x, flags=re.S)
    x = re.sub(r"<Footnotes>.*?</Footnotes>", "", x, flags=re.S)
    body = x[x.find("<Body") if "<Body" in x else x.find("<Schedule"):]
    out = []
    for m in re.finditer(r"<Title>(.*?)</Title>|<Text>(.*?)</Text>", body, flags=re.S):
        raw = m.group(1) if m.group(1) is not None else m.group(2)
        t = re.sub(r"<[^>]+>", " ", raw)
        t = re.sub(r"\s+", " ", t.replace("&amp;", "&")).strip()
        if not t or set(t) <= set(". "):
            continue
        out.append(("title" if m.group(1) is not None else "text", t, raw))
    return out


@lru_cache()
def ward_shares():
    """(la_code, normalised ward name) -> share of the LA's mid-2019 population living in that ward."""
    lk = pd.read_csv(R / "geography" / "wd20_lad20_partial.csv")
    pop = pd.read_csv(R / "geography" / "ward_pop_mid2019.csv")
    pop.columns = ["ward_name", "ward_code", "pop"]
    m = lk.merge(pop[["ward_code", "pop"]], left_on="WD20CD", right_on="ward_code", how="left")
    if m["pop"].isna().any():
        # 2020 ward codes not in the 2019 table: fall back on a name match within the LA
        miss = m["pop"].isna()
        bynm = pop.assign(k=pop.ward_name.map(norm)).drop_duplicates("k").set_index("k")["pop"]
        m.loc[miss, "pop"] = m.loc[miss, "WD20NM"].map(norm).map(bynm)
    m["share"] = m["pop"] / m.groupby("LAD20CD")["pop"].transform("sum")
    return {(r.LAD20CD, norm(r.WD20NM)): r.share for r in m.itertuples()}, m


def ward_share(la_code, wards):
    """Population share of la_code covered by the listed ward names; also returns any unmatched names."""
    sh, _ = ward_shares()
    tot, miss = 0.0, []
    for w in wards:
        k = (la_code, norm(w))
        if k in sh:
            tot += sh[k]
        else:
            miss.append(w)
    return tot, miss


# 2018-based SNPP (ODI Leeds copy) is on pre-2019/2020 districts; these 2020 LTLAs are sums of old districts
OLD_DISTRICTS = {
    "E06000060": ["E07000004", "E07000005", "E07000006", "E07000007"],     # Buckinghamshire
    "E06000058": ["E06000028", "E06000029", "E07000048"],                   # Bournemouth, Christchurch and Poole
    "E06000059": ["E07000049", "E07000050", "E07000051", "E07000052", "E07000053"],   # Dorset
    "E07000244": ["E07000205", "E07000206"],                                # East Suffolk
    "E07000245": ["E07000201", "E07000204"],                                # West Suffolk
    "E07000246": ["E07000190", "E07000191"],                                # Somerset West and Taunton
}


@lru_cache()
def pop2020() -> pd.Series:
    """Projected 2020 population (ONS 2018-based SNPP) by 2020 English LTLA. Wales not covered."""
    p = pd.read_csv(R / "odileeds" / "populations.csv", sep="\t", thousands=",")
    p = p[p["AGE GROUP"] == "All ages"].set_index("CODE")["2020"].astype(float)
    for new, olds in OLD_DISTRICTS.items():
        p[new] = p.reindex(olds).sum()
    return p
