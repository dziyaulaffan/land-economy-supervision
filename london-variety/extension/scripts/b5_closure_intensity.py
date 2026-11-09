"""B5 closure intensity: mean Google retail_and_recreation % change from baseline, LA x quarter, 2020Q1-2022Q3.

Input: b3_mobility_daily_lad.parquet (b3_mobility.py). Google's baseline is each area's own pre-pandemic baseline
(median for the same day of the week, 3 Jan-6 Feb 2020), so no further LA normalisation is applied.
2020Q1 covers only 15 Feb-31 Mar 2020 (46 days), the start of the Google series. Valid day = non-missing value.
Coverage = valid days / days in the quarter window; LA-quarters under 50% coverage are flagged (low_coverage).
LAs with no Google series (Isles of Scilly) appear with zero valid days and a missing mean.
"""
import numpy as np
import pandas as pd

from b3_migration import lookup
from ext_config import CLEAN

START, END = pd.Timestamp("2020-02-15"), pd.Timestamp("2022-09-30")


def main():
    lk = lookup()
    d = pd.read_parquet(CLEAN / "b3_mobility_daily_lad.parquet")
    d = d[(d.date >= START) & (d.date <= END)].copy()
    d["quarter"] = d.date.dt.to_period("Q").astype(str)
    days = pd.Series(pd.date_range(START, END, freq="D"))
    window = days.groupby(days.dt.to_period("Q").astype(str)).size().rename("window_days")
    q = d.groupby(["la_code", "quarter"]).agg(
        rr_mean=("retail_recreation", "mean"), rr_valid_days=("retail_recreation", "count"),
        rr_weight_share_mean=("retail_recreation_weight_share", "mean")).reset_index()
    grid = pd.MultiIndex.from_product([lk.la_code, window.index], names=["la_code", "quarter"]).to_frame(index=False)
    q = grid.merge(q, on=["la_code", "quarter"], how="left").merge(window, left_on="quarter", right_index=True)
    q["rr_valid_days"] = q.rr_valid_days.fillna(0).astype(int)
    q["coverage"] = q.rr_valid_days / q.window_days
    q["low_coverage"] = q.coverage < 0.5
    mt = d.drop_duplicates("la_code").set_index("la_code").mapping_type
    q["mapping_type"] = q.la_code.map(mt).fillna("missing")
    q["quarter_note"] = np.where(q.quarter == "2020Q1", "15 Feb-31 Mar 2020 only", "")
    q = lk[["la_code", "la_name", "region"]].merge(q, on="la_code").sort_values(["la_code", "quarter"])
    q = q.rename(columns={"rr_mean": "closure_rr_mean"})
    q.to_csv(CLEAN / "b5_closure_intensity_la_quarter.csv", index=False)
    print(f"rows {len(q)}, LAs {q.la_code.nunique()}, quarters {q.quarter.nunique()}")
    print(window.to_string())
    print("LA-quarters with a value:", q.closure_rr_mean.notna().sum(), "low coverage:", q.low_coverage.sum())
    print(q[q.low_coverage][["la_name", "quarter", "rr_valid_days", "window_days", "mapping_type"]].to_string(index=False))
    print(q.groupby("quarter").closure_rr_mean.describe().round(1).to_string())


if __name__ == "__main__":
    main()
