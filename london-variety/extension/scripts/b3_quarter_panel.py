"""B3 LA x quarter panel: PIPR rents (2015Q1-2026Q3) and Google mobility (2020Q1-2022Q4) on one grid.

Grid: 318 E&W LAs x every quarter 2015Q1-2026Q3. Rent columns are missing where PIPR does not publish the LA (City of
London, Isles of Scilly) or the quarter is incomplete; mobility columns are missing outside 15 Feb 2020-15 Oct 2022.
Inputs: b3_rents_quarterly_la.csv (b3_rents.py), b3_mobility_quarterly_lad.csv (b3_mobility.py).
"""
import pandas as pd

from b3_migration import lookup
from ext_config import CLEAN


def main():
    lk = lookup()
    r = pd.read_csv(CLEAN / "b3_rents_quarterly_la.csv")
    m = pd.read_csv(CLEAN / "b3_mobility_quarterly_lad.csv")
    qs = pd.period_range("2015Q1", r.quarter.max(), freq="Q").astype(str)
    grid = pd.MultiIndex.from_product([lk.la_code, qs], names=["la_code", "quarter"]).to_frame(index=False)
    p = (lk[["la_code", "la_name", "region", "country"]].merge(grid, on="la_code")
         .merge(r, on=["la_code", "quarter"], how="left").merge(m, on=["la_code", "quarter"], how="left"))
    p["rent_published"] = ~p.la_code.isin(["E09000001", "E06000053"])
    p.to_csv(CLEAN / "b3_la_quarter_panel.csv", index=False)
    print(f"rows {len(p)}, LAs {p.la_code.nunique()}, quarters {p.quarter.nunique()}; "
          f"rent rows {p.rent_y.notna().sum()} ({p[p.rent_y.notna()].la_code.nunique()} LAs); "
          f"mobility rows {p.mob_retail_recreation.notna().sum()} ({p[p.mob_retail_recreation.notna()].la_code.nunique()} LAs)")


if __name__ == "__main__":
    main()
