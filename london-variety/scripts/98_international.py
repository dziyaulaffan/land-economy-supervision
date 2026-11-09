"""International migration: total net migration (internal with the rest of the UK plus international) as outcome.

Source: ONS mid-year population estimates, detailed time series mid-2011 to mid-2025 (released 29 July 2026,
mid-2022 to mid-2024 revised), sheet MYEB2: components of change by LA (April 2023 boundaries), sex and single year
of age. Component year t = mid-(t-1) to mid-t = year to June t; age is age at mid-year t, as in the internal panel.
Outcomes per 1,000 mid-2019 residents of the age group (the internal panel's denominators):
  total = net moves with the rest of the UK (96_age_ddd.py) + international net;  international = international net.
Triple difference for 20-29 and 25-29 against the family proxy and 50+, plus young-adult event studies,
years to June 2016-2025. All inference: CR1 and WCR bootstrap clustered by borough (Rademacher, B = 9,999).
"""
import importlib.util

import pandas as pd

from config import CLEAN, OUT, RAW, download, london_frame
from es_core import rademacher

ES = OUT / "event_study"
URL = ("https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/populationandmigration/populationestimates/"
       "datasets/estimatesofthepopulationforenglandandwales/mid2011tomid2025detailedtimeseries/"
       "myebtablesenglandwales20112025.xlsx")
_spec = importlib.util.spec_from_file_location("m98s", __file__.replace("98_international.py", "98_students_25_29.py"))
m98s = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m98s)
m96 = m98s.m96
COMP = {"family_0_15_30_49": "family proxy", "age50plus": "ages 50+"}
YOUNG = {"age20_29": "20-29", "age25_29": "25-29"}
KEYS = ["2020", "2021", "2022", "reopening_minus_closure", "2022_minus_2020"]


def cell(t, term):
    r = t.set_index("term").loc[term]
    return f"{r.coef:.2f} ({r.p_wcb:.3f})"


def international_panel():
    cache = RAW / "ons_mye" / "myeb2_london_international.parquet"
    if not cache.exists():
        f = download(URL, RAW / "ons_mye" / "myebtablesenglandwales20112025.xlsx")
        x = pd.read_excel(f, sheet_name="MYEB2", header=1)
        x = x[x.ladcode23.isin(london_frame().la_code)]
        cols = [c for c in x.columns if c.startswith(("international_in_", "international_out_"))]
        x[["ladcode23", "sex", "age"] + cols].to_parquet(cache, index=False)
    x = pd.read_parquet(cache)
    long = x.melt(id_vars=["ladcode23", "sex", "age"], var_name="v", value_name="n")
    long["year_ending_june"] = long.v.str[-4:].astype(int)
    long["flow"] = long.v.str.replace(r"_\d{4}$", "", regex=True)
    rows = []
    for g in m96.AGES:
        s = long[m96.in_group(long.age, g)].groupby(["ladcode23", "year_ending_june", "flow"]).n.sum().unstack("flow")
        s["group"] = g
        rows.append(s.reset_index().rename(columns={"ladcode23": "la_code"}))
    return pd.concat(rows, ignore_index=True)


def main():
    w = rademacher(m96.B, 32, m96.SEED)
    d = pd.read_csv(CLEAN / "migration_net_by_age_group_extended.csv")
    it = international_panel()
    d = d.merge(it, on=["la_code", "year_ending_june", "group"], how="left")
    assert d.loc[d.year_ending_june >= 2016, "international_in"].notna().all()
    d["intl_net"] = d.international_in - d.international_out
    d["y_internal"] = d.y
    d["y_international"] = d.intl_net / d.pop_mid2019 * 1000
    d["y_total"] = (d.net_moves + d.intl_net) / d.pop_mid2019 * 1000
    d.to_csv(CLEAN / "migration_total_by_age_group.csv", index=False)
    m96.YEARS = list(range(2016, 2026))
    d = d[d.year_ending_june.isin(m96.YEARS)]

    desc = (d[d.group.isin(["age20_29", "age25_29"])].groupby(["group", "year_ending_june"])
            [["y_internal", "y_international"]].mean().round(2))
    out, L = [], ["### London-wide means of borough outcomes per 1,000 group residents\n", desc.to_string(), ""]
    L.append("### Total and international net migration (2016-2025; WCB p)\n")
    L.append("| Outcome | Model | 2020 | 2021 | 2022 | R - C | 2022 - 2020 |")
    L.append("|---|---|---|---|---|---|---|")
    for yv, ylab in (("y_total", "total"), ("y_international", "international"), ("y_internal", "internal (check)")):
        dd = d.assign(y=d[yv])
        for young, yl in YOUNG.items():
            t = m98s.es_tv(dd[dd.group == young], w)
            out.append(t.assign(outcome=ylab, analysis="event study", young=young, group=young))
            L.append(f"| {ylab} | event study {yl} | " + " | ".join(cell(t, k) for k in KEYS) + " |")
            for comp, cl in COMP.items():
                t = m98s.ddd_tv(m98s.stack_of(dd, young, comp), w)
                out.append(t.assign(outcome=ylab, analysis="triple difference", young=young, group=comp))
                L.append(f"| {ylab} | DDD {yl} vs {cl} | " + " | ".join(cell(t, k) for k in KEYS) + " |")
    m96.YEARS = list(range(2015, 2026))
    pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore").to_csv(
        ES / "international.csv", index=False)
    (ES / "international.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
