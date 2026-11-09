"""B2: MSOA (2021) to LAD (April 2023) best-fit lookup, England and Wales, from the ONS Open Geography Portal.

Service: MSOA21_LAD23_EW_LU (owner ONSGeography_data).
"""
import time

import pandas as pd
import requests

from ext_config import RAW, UA

OUT = RAW / "census2021_migration" / "geography"
OUT.mkdir(parents=True, exist_ok=True)
URL = ("https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
       "MSOA21_LAD23_EW_LU/FeatureServer/0/query")


def fetch():
    dest = OUT / "MSOA21_LAD23_EW_LU.csv"
    if dest.exists():
        return pd.read_csv(dest)
    rows, offset = [], 0
    while True:
        r = requests.get(URL, params={"where": "1=1", "outFields": "*", "returnGeometry": "false",
                                      "f": "json", "resultOffset": offset, "resultRecordCount": 2000},
                         headers=UA, timeout=120)
        r.raise_for_status()
        js = r.json()
        feats = [f["attributes"] for f in js.get("features", [])]
        rows += feats
        if not feats or not js.get("exceededTransferLimit"):
            break
        offset += len(feats)
        time.sleep(0.5)
    df = pd.DataFrame(rows)
    df.to_csv(dest, index=False)
    return df


if __name__ == "__main__":
    df = fetch()
    print(df.shape, list(df.columns))
    print(df.head())
