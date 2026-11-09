"""B1c helper. 2021 MSOA boundaries (BFE V8, full extent of the realm) and 2021 MSOA population-weighted
centroids (V2) for England and Wales from the ONS Open Geography Portal ArcGIS services, British National
Grid. Boundaries are requested with maxAllowableOffset = 2 m to keep the file manageable. Paged at 2,000
(BFE in smaller pages of 200 because of geometry size). Resumable: pages already on disk are skipped.
Also Census 2021 usual residents by 2021 MSOA (Nomis NM_2021_1, TS001) for per-resident measures.
"""
import json
import time

import pandas as pd
import requests

from ext_config import RAW, UA, download

SVC = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services"
OUT = RAW / "ons_geography"
LAYERS = {
    "msoa21_bfe_v8": ("Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFE_V8",
                      "MSOA21CD,MSOA21NM", 200, {"maxAllowableOffset": 2, "geometryPrecision": 1}),
    "msoa21_pwc_v2": ("MSOA_December_2021_EW_PWC_V2", "MSOA21CD", 2000, {}),
}


def pull(key):
    svc, fields, page, extra = LAYERS[key]
    d = OUT / key
    d.mkdir(parents=True, exist_ok=True)
    offset = 0
    while True:
        f = d / f"page_{offset:05d}.geojson"
        if not (f.exists() and f.stat().st_size > 0):
            for k in range(5):
                try:
                    r = requests.get(f"{SVC}/{svc}/FeatureServer/0/query", headers=UA, timeout=300, params={
                        "where": "1=1", "outFields": fields, "returnGeometry": "true", "outSR": 27700,
                        "resultOffset": offset, "resultRecordCount": page, "orderByFields": "FID",
                        "f": "geojson", **extra})
                    r.raise_for_status()
                    json.loads(r.content)
                    break
                except (requests.RequestException, ValueError) as e:
                    print("retry", key, offset, repr(e))
                    time.sleep(5 * 2 ** k)
            else:
                raise RuntimeError(key)
            f.write_bytes(r.content)
            time.sleep(1)
        n = len(json.loads(f.read_bytes())["features"])
        print(key, offset, n)
        if n < page:
            break
        offset += page


def main():
    for k in LAYERS:
        pull(k)
    url = ("https://www.nomisweb.co.uk/api/v01/dataset/NM_2021_1.data.csv?date=latest&geography=TYPE152"
           "&c2021_restype_3=0&measures=20100&select=geography_code,geography_name,obs_value")
    pages, off = [], 0
    while True:
        f = download(f"{url}&recordoffset={off}", RAW / "nomis" / f"census2021_ts001_msoa21_{off}.csv")
        p = pd.read_csv(f)
        pages.append(p)
        if len(p) < 25000:
            break
        off += 25000
    pop = pd.concat(pages)
    print("Census 2021 MSOA rows", len(pop))


if __name__ == "__main__":
    main()
