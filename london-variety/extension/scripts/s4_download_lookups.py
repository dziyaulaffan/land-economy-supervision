"""S4: download ONS Open Geography Portal lookups for 2001 -> 2011 -> 2021 small-area harmonisation.

All services are on services1.arcgis.com/ESMARspQHYMw9BZ9 (owner ONSGeography_data). Saved as CSV under
RAW/ons_geography/s4_lookups/.
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ext_config import RAW, UA  # noqa: E402

OUT = RAW / "ons_geography" / "s4_lookups"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/{}/FeatureServer/0/query"
SERVICES = {
    "OA01_LSOA01_MSOA01_EW_LU": "OA01_LSOA01_MSOA01_EW_LU_b75358eac2274f4fb012dcd32d13f5cf",
    "OA01_OA11_LAD11_EW_LU": "OA01_OA11_LAD11_EW_LU_4ba063a6b6ce40ab8faf4d6453662a08",
    "MSOA01_MSOA11_LAD11_EW_LU": "MSOA01_MSOA11_LAD11_EW_LU_4d62b7319b914e52bb640ccd5d7977b6",
    "OA11_LSOA11_MSOA11_LAD11_EW_LU": "OA11_LSOA11_MSOA11_LAD11_EW_LUv2_b3fe7c68f4b2420185eaff6284d4c125",
    "OA11_OA21_LAD22_EW_LU_Exact_fit": "OA11_OA21_LAD22_EW_LU_Exact_fit_V3",
    "MSOA11_MSOA21_LAD22_EW_LU_bestfit": "MSOA11_MSOA21_LAD22_EW_LU_v2",
    "MSOA11_MSOA21_LAD22_EW_LU": "MSOA_(2011)_to_MSOA_(2021)_to_Local_Authority_District_(2022)_Lookup_for_EW_v2",
    "OA21_LSOA21_MSOA21_EW_LU": "OA_LSOA_MSOA_EW_DEC_2021_LU_v3",
}


def fetch(name, svc):
    dest = OUT / f"{name}.csv"
    if dest.exists() and dest.stat().st_size > 0:
        print("have", dest.name)
        return
    rows, offset = [], 0
    while True:
        for attempt in range(5):
            try:
                r = requests.get(BASE.format(svc), params={
                    "where": "1=1", "outFields": "*", "returnGeometry": "false", "f": "json",
                    "resultOffset": offset, "resultRecordCount": 2000, "orderByFields": "ObjectId" if "LAD11" not in name or name.startswith("OA") else "FID"},
                    headers=UA, timeout=120)
                js = r.json()
                if "error" in js:  # orderBy field name differs between services
                    r = requests.get(BASE.format(svc), params={
                        "where": "1=1", "outFields": "*", "returnGeometry": "false", "f": "json",
                        "resultOffset": offset, "resultRecordCount": 2000}, headers=UA, timeout=120)
                    js = r.json()
                break
            except Exception as e:  # noqa: BLE001
                print("retry", name, offset, e, flush=True)
                time.sleep(5 * (attempt + 1))
        feats = [f["attributes"] for f in js.get("features", [])]
        rows += feats
        if not feats or not js.get("exceededTransferLimit"):
            break
        offset += len(feats)
    df = pd.DataFrame(rows)
    df.to_csv(dest, index=False)
    print(name, len(df), flush=True)


if __name__ == "__main__":
    for k, v in SERVICES.items():
        fetch(k, v)
