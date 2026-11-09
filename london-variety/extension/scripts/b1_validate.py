"""B1d. Validate FHRS and OSM category counts against UK Business Counts local units across local authorities.

LA geography: April 2023 LADs in England and Wales (Nomis TYPE424; 318 LAs). New counts come from
la2023_amenity_counts_ew.csv (points located by coordinates, assigned via 2021 MSOA). Business Counts
from NM_141_1 by SIC 2007 subclass (rounded by ONS). Population: ONS mid-2019 (and mid-2022 for the 2022
comparisons), same geography.

Correlations across LAs (Pearson): levels; logs, log(1 + x); per 1,000 residents; log per 1,000 residents
(log(1 + per1k * 1)). Also Spearman on levels, and per-1k correlations excluding City of London
(E09000001), whose tiny resident base makes per-resident values extreme.
Primary comparison: Business Counts March 2019. Supplementary: OSM 2022 vs Business Counts 2022, FHRS vs
Business Counts 2026 (latest, closest to the FHRS snapshot date).
"""
import numpy as np
import pandas as pd

from ext_config import CLEAN, RAW

SIC = {"56101": "Licensed restaurants", "56102": "Unlicensed restaurants and cafes",
       "56103": "Take-away food shops and mobile food stands", "56210": "Event catering",
       "56290": "Other food service", "56301": "Licensed clubs", "56302": "Public houses and bars",
       "59140": "Motion picture projection", "90010": "Performing arts",
       "90020": "Support activities to performing arts", "90030": "Artistic creation",
       "90040": "Operation of arts facilities", "93110": "Operation of sports facilities",
       "93130": "Fitness facilities"}
# new category -> Business Counts subclasses
MAP = {
    "fhrs_restaurant_cafe": ["56101", "56102"],
    "fhrs_takeaway": ["56103"],
    "fhrs_pub_bar_club": ["56301", "56302"],
    "fhrs_restaurant_cafe_by_authority": ["56101", "56102"],
    "fhrs_takeaway_by_authority": ["56103"],
    "fhrs_pub_bar_club_by_authority": ["56301", "56302"],
    "osm{y}_restaurant_cafe": ["56101", "56102"],
    "osm{y}_restaurant": ["56101"],
    "osm{y}_cafe": ["56102"],
    "osm{y}_fast_food": ["56103"],
    "osm{y}_pub_bar_club": ["56301", "56302"],
    "osm{y}_pub": ["56302"],
    "osm{y}_nightclub": ["56301"],
    "osm{y}_cinema": ["59140"],
    "osm{y}_arts_venue": ["90010", "90040"],
    "osm{y}_theatre": ["90010", "90040"],
    "osm{y}_fitness_centre": ["93130"],
}
CITY = "E09000001"


def ukbc(year):
    u = pd.read_csv(RAW / "nomis" / f"ukbc_local_units_{year}_subclasses_la2023.csv", dtype={"GEOGRAPHY_CODE": str})
    u["sic"] = u.INDUSTRY_NAME.str.split(" : ").str[0]
    w = u.pivot_table(index="GEOGRAPHY_CODE", columns="sic", values="OBS_VALUE", aggfunc="sum")
    return w[w.index.str[0].isin(["E", "W"])]


def pop(year):
    p = pd.read_csv(RAW / "nomis" / f"mye_population_mid{year}_la2023.csv")
    return p.set_index("GEOGRAPHY_CODE").OBS_VALUE


def corr_row(new, ref, popn, label):
    d = pd.DataFrame({"new": new, "ref": ref, "pop": popn}).dropna()
    pk = d[["new", "ref"]].div(d["pop"], axis=0) * 1000
    nc = d.index != CITY
    return dict(
        comparison=label, n_la=len(d), new_total=int(d.new.sum()), ukbc_total=int(d.ref.sum()),
        ratio_new_to_ukbc=round(d.new.sum() / d.ref.sum(), 3),
        r_levels=d.new.corr(d.ref), r_logs=np.log1p(d.new).corr(np.log1p(d.ref)),
        rho_levels=d.new.corr(d.ref, method="spearman"),
        r_per1k=pk.new.corr(pk.ref), r_log_per1k=np.log(pk.new + 0.01).corr(np.log(pk.ref + 0.01)),
        r_per1k_excl_city=pk.new[nc].corr(pk.ref[nc]),
        r_log_per1k_excl_city=np.log(pk.new[nc] + 0.01).corr(np.log(pk.ref[nc] + 0.01)))


def main():
    la = pd.read_csv(CLEAN / "la2023_amenity_counts_ew.csv").set_index("lad23cd")
    u = {y: ukbc(y) for y in ["2019", "2022", "latest"]}
    assert set(u["2019"].index) == set(la.index), set(u["2019"].index) ^ set(la.index)
    p = {"2019": pop("2019"), "2022": pop("2022")}
    rows = []
    for k, sics in MAP.items():
        ref_lab = "+".join(sics)
        if k.startswith("fhrs"):
            for uy, py in [("2019", "2019"), ("latest", "2022")]:
                rows.append(corr_row(la[k], u[uy][sics].sum(axis=1), p[py],
                                     f"{k} vs UKBC {uy if uy != 'latest' else '2026'} {ref_lab}"))
        else:
            for y in ["2019", "2022"]:
                kk = k.format(y=y)
                rows.append(corr_row(la[kk], u[y][sics].sum(axis=1), p[y], f"{kk} vs UKBC {y} {ref_lab}"))
            # OSM 2022 against UKBC 2019 as well (same reference year as the primary table)
            kk = k.format(y="2022")
            rows.append(corr_row(la[kk], u["2019"][sics].sum(axis=1), p["2019"], f"{kk} vs UKBC 2019 {ref_lab}"))
    r = pd.DataFrame(rows)
    num = r.select_dtypes("float").columns
    r[num] = r[num].round(3)
    r.to_csv(CLEAN / "b1_validation_correlations_la.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(r.to_string(index=False))
    pd.Series(SIC).rename("description").to_csv(CLEAN / "b1_ukbc_sic_subclasses_used.csv", index_label="sic2007")


if __name__ == "__main__":
    main()
