"""B3 rents: ONS Price Index of Private Rents (PIPR), monthly LA index and average rents, all LAs in England and Wales.

Same release and table as the pilot (scripts/20_rents.py, release 21 October 2026, Table 1). Quarterly outcome as in
scripts/80_event_study.py: y = 100 x log(mean monthly index over the quarter), complete quarters only (3 months).
Average rent: mean of the three monthly average rents. January 2015 onwards.
"""
import re

import numpy as np
import pandas as pd

from b3_migration import BIG, lookup
from ext_config import CLEAN, PILOT_RAW

RELEASE = "21october2026"
# PIPR uses the April 2024 codes for Barnsley and Sheffield (minor boundary change between the two); recode to the
# 2023 codes used by the migration files.
RECODE_2024 = {"E08000038": "E08000016", "E08000039": "E08000019"}


def snake(c: str) -> str:
    c = c.lower().replace("rental price", "avg_rent").replace("semidetached", "semi_detached")
    c = c.replace("four or more bed", "4plus_bed").replace("one bed", "1_bed").replace("two bed", "2_bed")
    c = c.replace("three bed", "3_bed").replace("flat maisonette", "flat")
    return re.sub(r"\W+", "_", c).strip("_")


def main():
    lk = lookup()
    d = pd.read_excel(PILOT_RAW / "ons_pipr" / f"pipr_{RELEASE}.xlsx", sheet_name="Table 1", header=2)
    d.columns = [snake(c) for c in d.columns]
    d = d.rename(columns={"time_period": "month", "area_code": "la_code", "area_name": "pipr_name",
                          "region_or_country_name": "pipr_region"})
    d["month"] = pd.to_datetime(d.month)
    d["pipr_code"] = d.la_code
    d["la_code"] = d.la_code.replace(RECODE_2024)
    vals = [c for c in d.columns if c.startswith(("index", "avg_rent", "monthly_change", "annual_change"))]
    d[vals] = d[vals].replace({"[x]": np.nan, "[z]": np.nan, "[c]": np.nan}).apply(pd.to_numeric, errors="coerce")
    d = d[d.la_code.isin(lk.la_code) & (d.month >= "2015-01-01")].copy()
    d = lk.merge(d, on="la_code")
    d[["la_code", "la_name", "region", "pipr_code", "month", *vals]].sort_values(["la_code", "month"]).to_csv(
        BIG / "b3_rents_monthly_la.csv", index=False)

    d["quarter"] = d.month.dt.to_period("Q")
    q = d.groupby(["la_code", "quarter"]).agg(
        index=("index", "mean"), n_months=("index", "count"), n_rows=("month", "size"),
        avg_rent=("avg_rent", "mean"), n_months_rent=("avg_rent", "count")).reset_index()
    q = q[(q.n_months == 3) & (q.n_rows == 3)].copy()  # complete quarters only
    q["rent_y"] = 100 * np.log(q["index"])
    q.loc[q.n_months_rent < 3, "avg_rent"] = np.nan
    q["quarter"] = q.quarter.astype(str)
    q = q.rename(columns={"index": "rent_index_qmean", "avg_rent": "avg_rent_qmean", "n_months": "rent_n_months"})
    q = q[["la_code", "quarter", "rent_index_qmean", "rent_y", "avg_rent_qmean", "rent_n_months"]]
    q.to_csv(CLEAN / "b3_rents_quarterly_la.csv", index=False)

    # coverage
    pub = set(d.la_code)
    missing = lk[~lk.la_code.isin(pub)]
    span = d.dropna(subset=["index"]).groupby("la_code").month.agg(["min", "max", "count"])
    short = span[(span["min"] > "2015-01-01") | (span["count"] < span["count"].max())]
    print(f"PIPR publishes {len(pub)} of 318 E&W LAs; not published: {missing.la_name.tolist()}")
    print(f"monthly range {d.month.min():%Y-%m} to {d.month.max():%Y-%m}; LAs with a shorter index series: {len(short)}")
    if len(short):
        print(short.join(lk.set_index("la_code").la_name).to_string())
    print(f"quarterly rows {len(q)}, LAs {q.la_code.nunique()}, quarters {q.quarter.min()}-{q.quarter.max()}")
    missing.to_csv(CLEAN / "b3_rents_las_not_published.csv", index=False)


if __name__ == "__main__":
    main()
