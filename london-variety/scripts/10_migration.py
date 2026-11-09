"""Internal migration panel for London boroughs, years ending June 2015 onwards.

Source: ONS "Internal migration in England and Wales" detailed estimates (origin-destination
LA x single year of age x sex), the same files the Centre for Cities repo
(CentreforCities/urban-population-internal-migration) reads in
internal_migration_script_localauthorities_for_stats.R. The repo does not ship these raw files,
so they are downloaded from ONS here. The repo's LAtoPUA2024 lookup provides the urban flag
(LA inside a Primary Urban Area = urban; PUA ":" = non-urban), and its Inner London lookup
is carried as an alternative Inner/Outer definition.

Year t = year ending 30 June t, i.e. moves between mid-(t-1) and mid-t. All years on 2023 LA boundaries.
"""
import pandas as pd

from config import CLEAN, LONDON, RAW, download, london_frame

BASE = ("https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/populationandmigration/"
        "populationestimates/datasets/internalmigrationinenglandandwales")
YEARS = range(2015, 2026)
CFC = RAW / "cfc_migration" / "Input workbooks"
AGE_BANDS = [(-1, 15, "0-15"), (15, 24, "16-24"), (24, 34, "25-34"), (34, 44, "35-44"),
             (44, 64, "45-64"), (64, 200, "65+")]


def url(y: int) -> str:
    if y <= 2021:
        return f"{BASE}/detailedinternalmigrationestimates{y}2021and2023localauthorities/detailedestimates{y}on2021and2023las.xlsx"
    if y == 2022:
        return f"{BASE}/detailedinternalmigrationestimates20222021and2023localauthorities/detailedestimates2022on2023las.xlsx"
    return f"{BASE}/detailedinternalmigrationestimates{y}2023localauthorities/detailedestimates{y}on2023las.xlsx"


def read_year(y: int) -> pd.DataFrame:
    f = download(url(y), RAW / "ons_internal_migration" / f"detailedestimates{y}.xlsx")
    cache = f.with_suffix(".london.parquet")
    if cache.exists():
        return pd.read_parquet(cache)
    try:
        xl = pd.ExcelFile(f, engine="calamine")  # much faster on these ~140 MB workbooks
    except ImportError:
        xl = pd.ExcelFile(f, engine="openpyxl")
    sheet = next(s for s in xl.sheet_names if "2023" in s and "LA" in s)
    probe = pd.read_excel(xl, sheet, header=None, nrows=15)
    hdr = probe.index[probe.apply(lambda r: r.astype(str).str.lower().isin(["outla", "inla"]).any(), axis=1)][0]
    d = pd.read_excel(xl, sheet, header=hdr)
    d.columns = [str(c).strip().lower() for c in d.columns]
    d = d[d.outla.isin(LONDON) | d.inla.isin(LONDON)]
    # wide layout: one column per single year of age (age_0 ... age_90)
    ages = [c for c in d.columns if c.startswith("age_")]
    d = d.melt(id_vars=["outla", "inla", "sex"], value_vars=ages, var_name="age", value_name="moves")
    d["age"] = pd.to_numeric(d.age.str.removeprefix("age_").str.replace("+", "", regex=False))
    d["moves"] = pd.to_numeric(d.moves).fillna(0.0)
    d = d[d.moves != 0]
    d["year_ending_june"] = y
    d.to_parquet(cache)
    return d


def geography() -> pd.DataFrame:
    g = pd.read_excel(CFC / "LAtoPUA2024.xlsx").iloc[:, :8]
    g.columns = ["la_code", "la_name", "region", "country", "pua", "combined_authority", "super_region",
                 "urban_region"]
    g = g.dropna(subset=["la_code"]).drop_duplicates("la_code")
    g["urban"] = (g.pua.astype(str).str.strip() != ":").astype("boolean")
    # ONS records moves to/from Scotland and Northern Ireland only at country level, so these
    # counterparts have no LA and no urban/non-urban status.
    ctry = pd.DataFrame({"la_code": ["S92000003", "N92000002"], "la_name": ["Scotland", "Northern Ireland"],
                         "region": ["Scotland", "Northern Ireland"], "country": ["Scotland", "Northern Ireland"]})
    g = pd.concat([g, ctry], ignore_index=True)
    g["urban"] = g["urban"].astype("boolean")
    g["in_london"] = g.la_code.isin(LONDON)
    return g


def main():
    raw = pd.concat([read_year(y) for y in YEARS], ignore_index=True)
    geo = geography()
    lon = london_frame()

    # long origin-destination table from each borough's point of view
    out = raw[raw.outla.isin(LONDON)].rename(columns={"outla": "la_code", "inla": "cp_code"}).assign(direction="out")
    inn = raw[raw.inla.isin(LONDON)].rename(columns={"inla": "la_code", "outla": "cp_code"}).assign(direction="in")
    od = pd.concat([out, inn], ignore_index=True)
    od["age_band"] = pd.cut(od.age, [b[0] for b in AGE_BANDS] + [200], labels=[b[2] for b in AGE_BANDS])

    missing = set(od.cp_code) - set(geo.la_code.dropna())
    assert not missing, f"counterpart LAs missing from LAtoPUA2024 lookup: {missing}"
    cp = geo.rename(columns=lambda c: "cp_" + c if c != "la_code" else "cp_code")
    od_tot = (od.groupby(["year_ending_june", "la_code", "direction", "cp_code"], as_index=False).moves.sum()
              .merge(cp, on="cp_code").merge(lon[["la_code", "la_name", "london_zone", "inner_cfc"]], on="la_code"))
    od_tot["cp_type"] = "Non-urban"
    od_tot.loc[od_tot.cp_urban.fillna(False), "cp_type"] = "Urban (non-London)"
    od_tot.loc[od_tot.cp_urban.isna(), "cp_type"] = "Scotland/NI (country total)"
    od_tot.loc[od_tot.cp_in_london, "cp_type"] = "London"
    od_tot["period"] = (od_tot.year_ending_june - 1).map("mid-{}".format) + " to mid-" + od_tot.year_ending_june.astype(str)
    od_tot.to_csv(CLEAN / "migration_od_london_boroughs.csv", index=False)
    # out-flow destinations only
    od_tot[od_tot.direction == "out"].rename(columns=lambda c: c.replace("cp_", "dest_")).to_csv(
        CLEAN / "migration_outflow_destinations.csv", index=False)

    # borough x year panel
    def tot(df, name):
        return df.pivot_table(index=["la_code", "year_ending_june"], columns="direction", values="moves",
                              aggfunc="sum", fill_value=0).add_prefix(name + "_")

    parts = [tot(od_tot, "all"),
             tot(od_tot[~od_tot.cp_in_london], "nonlondon"),
             tot(od_tot[od_tot.cp_in_london], "withinlondon"),
             tot(od_tot[od_tot.cp_type == "Urban (non-London)"], "urban_nonlondon"),
             tot(od_tot[od_tot.cp_type == "Non-urban"], "nonurban"),
             tot(od_tot[od_tot.cp_type == "Scotland/NI (country total)"], "scotni")]
    panel = pd.concat(parts, axis=1).fillna(0).reset_index()
    for p in ["all", "nonlondon", "withinlondon", "urban_nonlondon", "nonurban", "scotni"]:
        panel[f"{p}_net"] = panel[f"{p}_in"] - panel[f"{p}_out"]
    panel = lon.merge(panel, on="la_code").sort_values(["la_code", "year_ending_june"])
    panel.insert(panel.columns.get_loc("year_ending_june") + 1, "period",
                 (panel.year_ending_june - 1).map("mid-{}".format) + " to mid-" + panel.year_ending_june.astype(str))
    panel.to_csv(CLEAN / "migration_panel_borough_year.csv", index=False)

    # age-band totals (all counterparts)
    ab = (od.groupby(["la_code", "year_ending_june", "age_band", "direction"], observed=True).moves.sum()
          .unstack("direction", fill_value=0).reset_index())
    ab["net"] = ab["in"] - ab["out"]
    ab.to_csv(CLEAN / "migration_borough_year_ageband.csv", index=False)

    print(panel.groupby("year_ending_june")[["all_in", "all_out", "all_net", "nonlondon_net"]].sum().round(0))


if __name__ == "__main__":
    main()
