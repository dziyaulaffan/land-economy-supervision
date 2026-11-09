"""Distance from each 2011 MSOA to Charing Cross (monocentric control).

Centroids: ONS "Middle layer Super Output Areas (December 2011) EW Population Weighted Centroids"
(ArcGIS item c0e3f920e20e41b3a994dd7fc7333c91), requested in British National Grid (EPSG:27700).
Charing Cross: the conventional centre of London for road distances, at the statue of Charles I,
51.50741 N, 0.12783 W (WGS84), converted to British National Grid with pyproj.
Distance is straight-line, in km.
"""
import json

import numpy as np
import pandas as pd
import requests
from pyproj import Transformer

from config import CLEAN, RAW, UA

SERVICE = ("https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
           "MSOA_Dec_2011_PWC_in_England_and_Wales_2022/FeatureServer/0/query")
CHARING_CROSS_WGS84 = (51.50741, -0.12783)


def fetch_centroids():
    out = RAW / "ons_geography" / "msoa2011_pwc_bng.json"
    if out.exists():
        return pd.DataFrame(json.loads(out.read_text()))
    rows, offset = [], 0
    while True:
        r = requests.get(SERVICE, headers=UA, timeout=120, params={
            "where": "1=1", "outFields": "msoa11cd,msoa11nm", "returnGeometry": "true", "outSR": 27700,
            "resultOffset": offset, "resultRecordCount": 2000, "orderByFields": "OBJECTID", "f": "json"})
        r.raise_for_status()
        feats = r.json()["features"]
        rows += [{"msoa11_code": f["attributes"]["msoa11cd"], "msoa11_name": f["attributes"]["msoa11nm"],
                  "easting": f["geometry"]["x"], "northing": f["geometry"]["y"]} for f in feats]
        if len(feats) < 2000:
            break
        offset += 2000
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows))
    return pd.DataFrame(rows)


def main():
    c = fetch_centroids()
    assert len(c) == 7201 and c.msoa11_code.is_unique, len(c)
    e0, n0 = Transformer.from_crs(4326, 27700, always_xy=True).transform(CHARING_CROSS_WGS84[1], CHARING_CROSS_WGS84[0])
    c["dist_cc_km"] = np.hypot(c.easting - e0, c.northing - n0) / 1000
    m = pd.read_csv(CLEAN / "msoa_amenity_controls.csv", usecols=["msoa11_code", "la_code", "log_per1k_IR"])
    d = m.merge(c, on="msoa11_code", how="left")
    assert d.dist_cc_km.notna().all() and len(d) == 982
    d["log_dist_cc"] = np.log(d.dist_cc_km)
    d["X_log_dist_cc"] = (d.log_dist_cc - d.log_dist_cc.mean()) / d.log_dist_cc.std()
    d[["msoa11_code", "easting", "northing", "dist_cc_km", "log_dist_cc", "X_log_dist_cc"]].to_csv(
        CLEAN / "msoa_distance_charing_cross.csv", index=False)
    dm = d[["log_per1k_IR", "log_dist_cc"]] - d.groupby("la_code")[["log_per1k_IR", "log_dist_cc"]].transform("mean")
    print(f"Charing Cross BNG: E {e0:.0f}, N {n0:.0f}")
    print(d.dist_cc_km.describe().round(2).to_dict())
    print(f"corr(log amenity, log distance): overall {d.log_per1k_IR.corr(d.log_dist_cc):.3f}, "
          f"within borough {dm.log_per1k_IR.corr(dm.log_dist_cc):.3f}")


if __name__ == "__main__":
    main()
