"""Amenity use: Google COVID-19 Community Mobility Reports (historical regional CSVs, UK).

Keeps the retail_and_recreation and workplaces series for each London borough plus the
Greater London aggregate. Daily, 15 Feb 2020 to 15 Oct 2022. Values are % change versus
the 3 Jan-6 Feb 2020 day-of-week median baseline. City of London is dropped from the
clean panel (it stays in the raw GB extract).
"""
import re
import zipfile

import pandas as pd

from config import CITY, CLEAN, LONDON, RAW, download, london_frame

URL = "https://www.gstatic.com/covid19/mobility/Region_Mobility_Report_CSVs.zip"
SERIES = {"retail_and_recreation_percent_change_from_baseline": "retail_recreation",
          "workplaces_percent_change_from_baseline": "workplaces"}


def norm(s: str) -> str:
    s = re.sub(r"^(London Borough of|Royal Borough of|City of)\s+", "", s)
    return s.replace("&", "and").strip().lower()


def main():
    z = download(URL, RAW / "google_mobility" / "Region_Mobility_Report_CSVs.zip")
    frames = []
    with zipfile.ZipFile(z) as zf:
        for name in sorted(n for n in zf.namelist() if "_GB_" in n):
            with zf.open(name) as fh:
                frames.append(pd.read_csv(fh, dtype=str))
    gb = pd.concat(frames, ignore_index=True)
    gb.to_csv(RAW / "google_mobility" / "GB_Region_Mobility_Report_2020_2022.csv", index=False)

    lon = gb[gb.sub_region_1 == "Greater London"].copy()
    names = {norm(v): k for k, v in LONDON.items()}
    names["westminster"] = "E09000033"
    names["london"] = "E09000001"  # "City of London" normalises to "london"
    lon["la_code"] = lon.sub_region_2.fillna("").map(lambda s: names.get(norm(s)) if s else "E12000007")
    unmatched = lon.loc[lon.la_code.isna(), "sub_region_2"].unique()
    assert len(unmatched) == 0, f"unmatched Google areas: {unmatched}"
    lon["date"] = pd.to_datetime(lon.date)
    for c in SERIES:
        lon[c] = pd.to_numeric(lon[c])
    out = lon.rename(columns=SERIES)[["la_code", "sub_region_2", "iso_3166_2_code", "date", *SERIES.values()]]
    out = out.rename(columns={"sub_region_2": "google_area_name"})
    out["google_area_name"] = out.google_area_name.fillna("Greater London (aggregate)")
    meta = london_frame()[["la_code", "la_name", "london_zone"]]
    out = out[out.la_code != CITY].merge(meta, on="la_code", how="left")  # City excluded from analysis panel
    out.loc[out.la_code == "E12000007", ["la_name", "london_zone"]] = ["Greater London", "All London"]
    out = out.sort_values(["la_code", "date"])
    out.to_csv(CLEAN / "mobility_daily_london.csv", index=False)

    # monthly means and missing-day counts
    out["month"] = out.date.dt.to_period("M").dt.to_timestamp()
    m = out.groupby(["la_code", "la_name", "london_zone", "month"]).agg(
        retail_recreation=("retail_recreation", "mean"), workplaces=("workplaces", "mean"),
        days=("date", "size"), rr_days_missing=("retail_recreation", lambda s: s.isna().sum()),
        wp_days_missing=("workplaces", lambda s: s.isna().sum())).reset_index()
    m.to_csv(CLEAN / "mobility_monthly_london.csv", index=False)
    print(out.groupby("la_name").agg(start=("date", "min"), end=("date", "max"), n=("date", "size"),
                                     rr_na=("retail_recreation", lambda s: s.isna().sum()),
                                     wp_na=("workplaces", lambda s: s.isna().sum())).to_string())


if __name__ == "__main__":
    main()
