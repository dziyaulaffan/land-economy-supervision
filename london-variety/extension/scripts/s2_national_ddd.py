"""Step 2: national triple difference (pre-analysis plan, Design 1).

Outcome: net internal migration of each LA with all other UK LAs (`all` counterpart) per 1,000 mid-2019 residents of
the age group, years to June 2016-2025, 2019 omitted. Young 20-29 and 25-29; comparison family proxy and 50+.
D = z_log_per1k_IR (Business Counts 2019 I+R per 1,000, standardised over 316 LADs). Specifications (a)-(f) of the
plan, all 316 LADs and the 283 outside London. Secondary: total net migration (internal + ONS MYEB2 international)
in specification (f). Differenced form (e_core.ddd_diff), verified to reproduce the pilot's London estimates exactly.
"""
import numpy as np
import pandas as pd

from e_core import cell, ddd_diff, rademacher, B, SEED
from ext_config import CLEAN, PILOT_RAW, RAW, download

DROP = {"E09000001", "E06000053"}
YOUNG = {"age20_29": "20-29", "age25_29": "25-29"}
COMP = {"family_0_15_30_49": "family proxy", "age50plus": "ages 50+"}
SPECS = {"(a) none": ((), False), "(b) teleworkability": (("X_telework",), False),
         "(c) garden": (("X_garden",), False), "(d) both": (("X_telework", "X_garden"), False),
         "(e) region x year": ((), True), "(f) both + region x year": (("X_telework", "X_garden"), True)}
AGES = {"age20_29": [range(20, 30)], "age25_29": [range(25, 30)],
        "family_0_15_30_49": [range(0, 16), range(30, 50)], "age50plus": [range(50, 200)]}
MYE = ("https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/populationandmigration/populationestimates/"
       "datasets/estimatesofthepopulationforenglandandwales/mid2011tomid2025detailedtimeseries/"
       "myebtablesenglandwales20112025.xlsx")
KEYS = ["2016", "2017", "2018", "2020", "2021", "2022", "2022_minus_2020"]


def international():
    cache = RAW / "ons_mye" / "myeb2_international_by_group.parquet"
    if not cache.exists():
        f = PILOT_RAW / "ons_mye" / "myebtablesenglandwales20112025.xlsx"
        if not f.exists():
            f = download(MYE, RAW / "ons_mye" / "myebtablesenglandwales20112025.xlsx")
        x = pd.read_excel(f, sheet_name="MYEB2", header=1)
        cols = [c for c in x.columns if str(c).startswith(("international_in_", "international_out_"))]
        long = x[["ladcode23", "age"] + cols].melt(id_vars=["ladcode23", "age"], var_name="v", value_name="n")
        long["year_ending_june"] = long.v.str[-4:].astype(int)
        long["flow"] = long.v.str.replace(r"_\d{4}$", "", regex=True)
        rows = []
        for g, rs in AGES.items():
            m = np.logical_or.reduce([long.age.isin(list(r)) for r in rs])
            s = long[m].groupby(["ladcode23", "year_ending_june", "flow"]).n.sum().unstack("flow").reset_index()
            rows.append(s.assign(group=g))
        out = pd.concat(rows).rename(columns={"ladcode23": "la_code"})
        cache.parent.mkdir(parents=True, exist_ok=True)
        out.to_parquet(cache, index=False)
    return pd.read_parquet(cache)


def panel(outcome="internal"):
    m = pd.read_csv(CLEAN / "b3_migration_la_year_by_age_group.csv")
    m = m[~m.la_code.isin(DROP) & m.group.isin(list(YOUNG) + list(COMP))]
    if outcome == "total":
        it = international()
        m = m.merge(it, on=["la_code", "year_ending_june", "group"], how="left")
        m["val"] = (m.all_net + m.international_in - m.international_out) / m.pop_mid2019 * 1000
    else:
        m["val"] = m.all_net_per1k
    p = m.pivot_table(index=["la_code", "year_ending_june"], columns="group", values="val").reset_index()
    c = pd.read_csv(CLEAN / "b3_la_crosssection.csv")[["la_code", "region", "z_log_per1k_IR", "london"]]
    s = pd.read_csv(CLEAN / "s1_controls_la2023.csv")[["la_code", "X_telework_share", "X_garden_share"]]
    s = s.rename(columns={"X_telework_share": "X_telework", "X_garden_share": "X_garden"})
    p = p.merge(c, on="la_code").merge(s, on="la_code").rename(columns={"z_log_per1k_IR": "D"})
    assert p.la_code.nunique() == 316 and p[["D", "X_telework", "X_garden"]].notna().all().all()
    return p


def main():
    out, L = [], []
    for outcome in ("internal", "total"):
        p = panel(outcome)
        for sample in ("all 316", "outside London"):
            q = p if sample == "all 316" else p[~p.london.astype(bool)]
            w = rademacher(B, q.la_code.nunique(), SEED)
            for young in YOUNG:
                for comp in COMP:
                    q = q.assign(dy=q[young] - q[comp])
                    for spec, (ctrl, ry) in SPECS.items():
                        if outcome == "total" and not spec.startswith("(f)"):
                            continue
                        t = ddd_diff(q, ctrl, ry, w=w)
                        out.append(t.assign(outcome=outcome, sample=sample, young=young, comp=comp, spec=spec))
                        print(outcome, sample, young, comp, spec, cell(t, "2020"), cell(t, "2022_minus_2020"),
                              flush=True)
    res = pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore")
    res.to_csv(CLEAN / "s2_national_ddd.csv", index=False)
    L.append("| Outcome | Sample | Young | Comparison | Spec | " + " | ".join(KEYS) + " | Telework x 2020 | Garden x 2020 | LAs |")
    L.append("|---|---|---|---|---|" + "---|" * (len(KEYS) + 3))
    for (o, s, y, c, sp), t in res.groupby(["outcome", "sample", "young", "comp", "spec"], sort=False):
        tc = cell(t, "X_telework:2020") if "X_telework:2020" in set(t.term) else ""
        gc = cell(t, "X_garden:2020") if "X_garden:2020" in set(t.term) else ""
        L.append(f"| {o} | {s} | {YOUNG[y]} | {COMP[c]} | {sp} | " + " | ".join(cell(t, k) for k in KEYS)
                 + f" | {tc} | {gc} | {int(t.n_clusters.iloc[0])} |")
    (CLEAN / "s2_national_ddd.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
