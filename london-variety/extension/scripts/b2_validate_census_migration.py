"""B2: validation of the Census 2021 migration outputs. Writes data/clean/b2_validation_summary.csv."""
import pandas as pd

from ext_config import CLEAN, RAW

SRC = RAW / "census2021_migration"
BIG = RAW.parent / "clean"
rows = []


def check(name, a, b, note=""):
    diff = a - b
    rows.append({"check": name, "value_a": a, "value_b": b, "diff": diff,
                 "pct_diff": 100 * diff / b if b else float("nan"), "note": note})
    print(f"{name:75s} {a:>14,.0f} {b:>14,.0f} {diff:>10,.0f} ({100 * diff / b if b else float('nan'):.3f}%)")


def main():
    ts = pd.read_csv(SRC / "census2021-ts019" / "census2021-ts019-ctry.csv")
    ts.columns = ["date", "name", "code", "tot", "same", "stud", "uk", "abroad"]
    ew = ts[ts.code == "K04000001"].iloc[0]   # England and Wales row
    nat_mig = ew.stud + ew.uk + ew.abroad

    la = pd.read_csv(CLEAN / "b2_la_migration_by_age.csv")
    for vint in ["lad21", "lad23"]:
        x = la[la.geo_level == vint]
        print(vint, "areas:", x.geo_code.nunique())
        allg = x[x.age_band == "All ages 1+"].pivot_table(index="geo_code", columns="measure", values="count")
        pop = x[(x.age_band == "All ages 1+") & (x.measure == "in_total")].denom_pop.sum()
        check(f"{vint}: sum LA usual residents 1+ (ODMG01EW) vs TS019 E&W total", pop, ew.tot)
        check(f"{vint}: sum LA in_total all ages vs TS019 E&W migrants (UK+student+abroad)", allg.in_total.sum(), nat_mig)
        check(f"{vint}: sum LA in_outside_uk vs TS019 E&W outside UK", allg.in_outside_uk.sum(), ew.abroad)
        check(f"{vint}: sum in_other_ew vs sum out_other_ew (identity)", allg.in_other_ew.sum(), allg.out_other_ew.sum())
        bands = x[x.age_band != "All ages 1+"].groupby("measure")["count"].sum()
        check(f"{vint}: sum of 22 bands in_total (ODMG02EW) vs all-ages (ODMG01EW)", bands["in_total"], allg.in_total.sum(),
              "perturbation: different tables")
        check(f"{vint}: sum of 22 bands in_other_ew vs out_other_ew (identity)", bands["in_other_ew"], bands["out_other_ew"])
    a21 = la[(la.geo_level == "lad21") & (la.age_band == "All ages 1+")].groupby("measure")["count"].sum()
    a23 = la[(la.geo_level == "lad23") & (la.age_band == "All ages 1+")].groupby("measure")["count"].sum()
    check("LAD23 vs LAD21 in_total (should be equal)", a23.in_total, a21.in_total)
    check("LAD23 vs LAD21 in_same_area (rises: merged districts)", a23.in_same_area, a21.in_same_area,
          "moves between districts merged in April 2023 become same-area moves")

    # MSOA all ages
    ma = pd.read_csv(CLEAN / "b2_msoa_migration_all_ages.csv")
    print("MSOAs (all ages):", ma.geo_code.nunique())
    mw = ma.pivot_table(index=["geo_code", "lad21_code"], columns="measure", values="count").reset_index()
    mpop = ma[ma.measure == "in_total"].denom_pop.sum()
    check("MSOA: sum usual residents 1+ (ODMG01EW MSOA) vs TS019 E&W total", mpop, ew.tot)
    check("MSOA: sum in_total vs TS019 E&W migrants", mw.in_total.sum(), nat_mig)
    check("MSOA: sum in_outside_uk vs TS019 E&W outside UK", mw.in_outside_uk.sum(), ew.abroad)
    check("MSOA: sum in_other_ew vs out_other_ew (identity)", mw.in_other_ew.sum(), mw.out_other_ew.sum())
    agg = mw.groupby("lad21_code")[["in_total", "in_outside_uk"]].sum()
    l21 = la[(la.geo_level == "lad21") & (la.age_band == "All ages 1+")].pivot_table(index="geo_code", columns="measure", values="count")
    j = agg.join(l21[["in_total", "in_outside_uk"]], rsuffix="_la")
    d = (j.in_total - j.in_total_la) / j.in_total_la * 100
    print(f"MSOA->LAD21 in_total vs LA file: median abs % diff {d.abs().median():.3f}, max abs % diff {d.abs().max():.3f}")
    rows.append({"check": "MSOA summed to LAD21 vs LA file, in_total: median / max abs % diff",
                 "value_a": d.abs().median(), "value_b": d.abs().max(), "note": "perturbation"})

    # MSOA by age (API)
    p = CLEAN / "b2_msoa_inflows_by_age.csv"
    p = p if p.exists() else BIG / p.name
    mb = pd.read_csv(p)
    print("MSOAs by age:", mb.geo_code.nunique(), mb.age_classification.value_counts().to_dict())
    full = mb[mb.age_classification == "resident_age_23a"]
    cov = full.geo_code.nunique()
    nat = mb.groupby("measure")["count"].sum()
    check("MSOA by-age (API): sum in_total vs TS019 E&W migrants", nat.in_total, nat_mig)
    check("MSOA by-age (API): sum in_outside_uk vs TS019", nat.in_outside_uk, ew.abroad)
    check("MSOA by-age (API): sum in_student_termtime vs TS019", nat.in_student_termtime, ew.stud)
    lb = la[(la.geo_level == "lad21") & (la.age_band != "All ages 1+") & (la.measure == "in_total")].groupby("age_band")["count"].sum()
    if cov == mb.geo_code.nunique():
        mbb = full[full.measure == "in_total"].groupby("age_band")["count"].sum()
        for b in ["18-19", "20-24", "25-29", "30-34", "65-69"]:
            check(f"band {b}: MSOA API in_total vs LA ODMG02EW in_total", mbb[b], lb[b], "different tables, perturbation")

    # MSOA single year vs 23 bands
    ms = pd.read_csv(BIG / "b2_msoa_inflows_single_year.csv.gz")
    blocked = pd.read_csv(SRC / "ons_api" / "msoa_migrant_ind_resident_age_86a_blocked.csv")
    print("MSOAs single year:", ms.geo_code.nunique(), "blocked:", len(blocked))
    rows.append({"check": "MSOA single-year: MSOAs returned / blocked by API", "value_a": ms.geo_code.nunique(),
                 "value_b": len(blocked)})
    keep = ms.geo_code.unique()
    a = ms[ms.measure == "in_total"]["count"].sum()
    b = full[(full.geo_code.isin(keep)) & (full.measure == "in_total")]["count"].sum()
    check("MSOA single-year in_total vs 22-band in_total (same MSOAs)", a, b, "perturbation")

    # LA single year
    sy = pd.read_csv(CLEAN / "b2_la_inflows_single_year.csv")
    s21 = sy[sy.geo_level == "lad21"].groupby("measure")["count"].sum()
    check("LA single-year (API): sum in_total vs TS019 E&W migrants", s21.in_total, nat_mig)
    check("LA single-year (API): sum denom_pop vs TS019 E&W total", sy[(sy.geo_level == "lad21") & (sy.measure == "in_total")].denom_pop.sum(), ew.tot)

    pd.DataFrame(rows).to_csv(CLEAN / "b2_validation_summary.csv", index=False)


if __name__ == "__main__":
    main()
