"""Rents: ONS Price Index of Private Rents (PIPR), UK monthly price statistics, Table 1.

Keeps index levels (January 2023 = 100) and average monthly rents, overall and by
bedrooms / property type, from January 2015, for London boroughs, local authorities in
the South East and East of England, and the three region aggregates.
City of London is not published in PIPR.
"""
import re

import pandas as pd

from config import CLEAN, RAW, REGION_CODES, download

RELEASE = "21october2026"
URL = ("https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/datasets/"
       f"priceindexofprivaterentsukmonthlypricestatistics/{RELEASE}/priceindexofprivaterentsukmonthlypricestatistics.xlsx")


def snake(c: str) -> str:
    c = c.lower().replace("rental price", "avg_rent").replace("semidetached", "semi_detached")
    c = c.replace("four or more bed", "4plus_bed").replace("one bed", "1_bed").replace("two bed", "2_bed")
    c = c.replace("three bed", "3_bed").replace("flat maisonette", "flat")
    return re.sub(r"\W+", "_", c).strip("_")


def main():
    f = download(URL, RAW / "ons_pipr" / f"pipr_{RELEASE}.xlsx")
    d = pd.read_excel(f, sheet_name="Table 1", header=2)
    d.columns = [snake(c) for c in d.columns]
    d = d.rename(columns={"time_period": "month", "area_code": "la_code", "area_name": "la_name",
                          "region_or_country_name": "region"})
    d["month"] = pd.to_datetime(d.month)
    keep_region = d.region.isin(REGION_CODES.values()) | d.la_code.isin(REGION_CODES)
    d = d[keep_region & (d.month >= "2015-01-01")].copy()
    d["geo_level"] = d.la_code.map(lambda c: "region" if c in REGION_CODES else "local authority")
    d.loc[d.geo_level == "region", "region"] = d.la_name
    vals = [c for c in d.columns if c.startswith(("index", "avg_rent", "monthly_change", "annual_change"))]
    d[vals] = d[vals].replace({"[x]": pd.NA, "[z]": pd.NA}).apply(pd.to_numeric)
    d = d[["month", "la_code", "la_name", "region", "geo_level", *vals]].sort_values(["region", "la_code", "month"])
    d.to_csv(CLEAN / "rents_monthly_la.csv", index=False)

    # long version: one row per area x month x dwelling category
    long = []
    for c in [c for c in vals if c.startswith("index")]:
        cat = c.removeprefix("index").strip("_") or "all"
        rent = "avg_rent" + ("" if cat == "all" else "_" + cat)
        long.append(d[["month", "la_code", "la_name", "region", "geo_level"]].assign(
            category=cat, index_jan2023_100=d[c], avg_rent=d[rent]))
    pd.concat(long).to_csv(CLEAN / "rents_monthly_la_long.csv", index=False)
    print(d.groupby(["region", "geo_level"]).la_code.nunique(), d.month.min(), d.month.max())


if __name__ == "__main__":
    main()
