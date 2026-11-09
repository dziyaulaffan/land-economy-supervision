"""B1 helper. England and Wales postcode extract from the pilot's NSPL (August 2026), read only.

Keeps live and terminated postcodes (FHRS addresses can carry terminated postcodes), with lat/long,
BNG easting/northing, 2021 MSOA, 2026 LAD and country. Postcodes with no grid reference (gridind 9)
are dropped. Output: big clean folder, nspl_ew.parquet.
"""
import zipfile

import pandas as pd

from ext_config import PILOT_RAW, ROOT

BIG = __import__("pathlib").Path.home() / "research-data" / "london-variety-extension" / "clean"
BIG.mkdir(parents=True, exist_ok=True)
COLS = ["pcds", "doterm", "usrtypind", "east1m", "north1m", "gridind", "lad26cd", "ctry26cd", "msoa21cd",
        "lsoa21cd", "lat", "long"]


def main():
    out = BIG / "nspl_ew.parquet"
    z = zipfile.ZipFile(PILOT_RAW / "nspl" / "NSPL_AUG_2026.zip")
    with z.open("Data/NSPL_AUG_2026_UK.csv") as fh:
        n = pd.read_csv(fh, usecols=COLS, dtype=str)
    n = n[n.ctry26cd.isin(["E92000001", "W92000004"])]
    n = n[n.gridind != "9"].copy()
    for c in ["east1m", "north1m", "lat", "long"]:
        n[c] = pd.to_numeric(n[c], errors="coerce")
    n = n.dropna(subset=["lat", "long", "msoa21cd"])
    n["pc_key"] = n.pcds.str.replace(" ", "").str.upper()
    n["live"] = n.doterm.isna()
    n.to_parquet(out, index=False)
    print(f"{len(n):,} E&W postcodes with grid refs ({n.live.sum():,} live), {n.msoa21cd.nunique()} MSOAs, "
          f"{n.lad26cd.nunique()} LADs")


if __name__ == "__main__":
    main()
