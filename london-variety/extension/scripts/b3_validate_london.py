"""B3 validation: the national files must reproduce the pilot's clean London files for the 32 analysis boroughs.

Read-only comparison against PROJECT/data/clean. Writes extension/data/clean/b3_validation_london.csv (one row per
check) and prints a summary.
"""
import numpy as np
import pandas as pd

from ext_config import CLEAN, PROJECT

PC = PROJECT / "data" / "clean"
CITY = "E09000001"


def check(name, a, b, key, cols, rows):
    a2 = a[key + sorted({c for c, _ in cols})].rename(columns=lambda c: c if c in key else "n__" + c)
    b2 = b[key + sorted({c for _, c in cols})].rename(columns=lambda c: c if c in key else "p__" + c)
    m = a2.merge(b2, on=key, how="outer", indicator=True)
    both = m[m._merge == "both"]
    for c_nat, c_pilot in cols:
        x, y = both["n__" + c_nat].astype(float), both["p__" + c_pilot].astype(float)
        d = (x - y).abs()
        rows.append(dict(check=name, variable=f"{c_nat} vs {c_pilot}", n_pilot=len(b), n_matched=len(both),
                         n_only_pilot=int((m._merge == "right_only").sum()),
                         n_only_national=int((m._merge == "left_only").sum()),
                         max_abs_diff=float(d.max()), n_diff_gt_1e6=int((d > 1e-6).sum()),
                         exact_match=bool(np.allclose(x, y, rtol=0, atol=1e-6, equal_nan=True))))


def main():
    rows = []
    # 1. migration by age group (pilot: net moves crossing the Greater London boundary)
    nat = pd.read_csv(CLEAN / "b3_migration_la_year_by_age_group.csv")
    nat = nat[nat.region == "London"]
    pilot = pd.read_csv(PC / "migration_net_by_age_group.csv")
    check("migration_net_by_age_group.csv (all, 20-29, 30-39, family, 50+)", nat, pilot,
          ["la_code", "year_ending_june", "group"],
          [("xregion_net", "net_moves"), ("pop_mid2019", "pop_mid2019"),
           ("xregion_net_per1k", "net_per1k_group")], rows)
    ext = pd.read_csv(PC / "migration_net_by_age_group_extended.csv")
    check("migration_net_by_age_group_extended.csv (20-29, 20-24, 25-29, family, 50+)", nat, ext,
          ["la_code", "year_ending_june", "group"],
          [("xregion_net", "net_moves"), ("xregion_net_per1k", "y")], rows)
    panel = pd.read_csv(PC / "migration_panel_borough_year.csv")
    na = nat[nat.group == "all"]
    check("migration_panel_borough_year.csv (all counterparts, non-London, Scotland/NI)", na, panel,
          ["la_code", "year_ending_june"],
          [("all_in", "all_in"), ("all_out", "all_out"), ("all_net", "all_net"),
           ("xregion_in", "nonlondon_in"), ("xregion_out", "nonlondon_out"), ("xregion_net", "nonlondon_net"),
           ("scotni_in", "scotni_in"), ("scotni_out", "scotni_out")], rows)

    # 2. rents
    r = pd.read_csv(CLEAN / "b3_rents_quarterly_la.csv").rename(columns={"quarter": "q"})
    pr = pd.read_csv(PC / "event_study_rents_quarterly.csv")
    check("event_study_rents_quarterly.csv", r[r.la_code.isin(pr.la_code)], pr, ["la_code", "q"],
          [("rent_index_qmean", "index"), ("rent_y", "y")], rows)

    # 3. amenity density
    x = pd.read_csv(CLEAN / "b3_la_crosssection.csv")
    pa = pd.read_csv(PC / "london_amenity_density_2019.csv")
    lon = x[x.la_code.isin(pa.la_code)].copy()
    lon["z_log_per1k_IR_london32"] = (lon.log_per1k_IR - lon.log_per1k_IR.mean()) / lon.log_per1k_IR.std()
    check("london_amenity_density_2019.csv", lon, pa, ["la_code"],
          [(c, c) for c in ["units_div55", "units_div56", "units_div90", "units_div91", "units_div92", "units_div93",
                            "units_all_industries", "units_IR", "per1k_I_accom_food", "per1k_R_arts_rec",
                            "per1k_IR", "log_per1k_IR"]]
          + [("pop_mid2019", "pop_mid2019"), ("z_log_per1k_IR_london32", "z_log_per1k_IR")], rows)
    pc = pd.read_csv(PC / "controls_borough.csv")
    check("controls_borough.csv (garden share)", lon, pc, ["la_code"], [("garden_share", "garden_share")],
          rows)

    # 4. mobility (daily, London boroughs)
    md = pd.read_parquet(CLEAN / "b3_mobility_daily_lad.parquet")
    pm = pd.read_csv(PC / "mobility_daily_london.csv", parse_dates=["date"])
    pm = pm[pm.la_code.str.startswith("E09")]
    check("mobility_daily_london.csv", md[md.la_code.str.startswith("E09") & (md.la_code != CITY)], pm,
          ["la_code", "date"], [("retail_recreation", "retail_recreation"),
                                ("workplaces", "workplaces")], rows)

    out = pd.DataFrame(rows)
    out.to_csv(CLEAN / "b3_validation_london.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_colwidth", 70):
        print(out.to_string(index=False))
    # z-score correlation between London-only and national standardisation
    print("corr(national z, London-32 z):", lon[["z_log_per1k_IR", "z_log_per1k_IR_london32"]].corr().iloc[0, 1])


if __name__ == "__main__":
    main()
