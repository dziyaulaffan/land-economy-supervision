"""B1a. Parse the FHRS open data XML files (England and Wales) into one point file for three categories:
  restaurant_cafe  BusinessType "Restaurant/Cafe/Canteen"   (BusinessTypeID 1)
  pub_bar_club     BusinessType "Pub/bar/nightclub"         (7843)
  takeaway         BusinessType "Takeaway/sandwich shop"    (7844)

FHRS is a current register snapshot (extract date recorded per file), not a 2019 or 2022 stock.
Coordinates: FHRS geocode where present and inside a Great Britain box; otherwise filled from the NSPL
(August 2026, live or terminated postcodes) by exact normalised postcode. Counts of missing coordinates
before and after filling are written to the notes via the printed summary and fhrs_geocode_summary.csv.
"""
import glob

import numpy as np
import pandas as pd
from lxml import etree

from ext_config import CLEAN, RAW

BIG = __import__("pathlib").Path.home() / "research-data" / "london-variety-extension" / "clean"
CATS = {"Restaurant/Cafe/Canteen": "restaurant_cafe", "Pub/bar/nightclub": "pub_bar_club",
        "Takeaway/sandwich shop": "takeaway"}
FIELDS = ["FHRSID", "LocalAuthorityBusinessID", "BusinessName", "BusinessType", "BusinessTypeID", "AddressLine1",
          "AddressLine2", "AddressLine3", "AddressLine4", "PostCode", "RatingValue", "RatingDate",
          "LocalAuthorityCode", "LocalAuthorityName", "NewRatingPending"]


def parse(path):
    rows, extract = [], None
    for _, el in etree.iterparse(path, events=("end",), tag=("EstablishmentDetail", "ExtractDate")):
        if el.tag == "ExtractDate":
            extract = el.text
            continue
        r = {f: el.findtext(f) for f in FIELDS}
        r["Longitude"] = el.findtext("Geocode/Longitude")
        r["Latitude"] = el.findtext("Geocode/Latitude")
        el.clear()
        rows.append(r)
    df = pd.DataFrame(rows)
    df["extract_date"] = extract
    df["source_file"] = path.split("\\")[-1].split("/")[-1]
    return df


def main():
    files = sorted(glob.glob(str(RAW / "fhrs" / "FHRS*en-GB.xml")))
    allr = pd.concat([parse(f) for f in files], ignore_index=True)
    print(f"{len(files)} files, {len(allr):,} establishments of all types")
    print("extract dates:", allr.extract_date.value_counts().to_dict())
    bt = allr.BusinessType.value_counts()
    bt.to_csv(CLEAN / "fhrs_business_type_counts_ew.csv", header=["establishments"])
    d = allr[allr.BusinessType.isin(CATS)].copy()
    d["category"] = d.BusinessType.map(CATS)
    n0 = len(d)
    d = d.drop_duplicates("FHRSID")
    print(f"{n0:,} rows in the three categories, {len(d):,} after dropping duplicate FHRSIDs")
    for c in ["Longitude", "Latitude"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    bad = ~(d.Latitude.between(49.8, 56.0) & d.Longitude.between(-6.5, 2.0))
    d.loc[bad, ["Latitude", "Longitude"]] = np.nan
    d["pc_key"] = d.PostCode.fillna("").str.replace(r"\s+", "", regex=True).str.upper()
    n = pd.read_parquet(BIG / "nspl_ew.parquet", columns=["pc_key", "lat", "long", "live"])
    n = n.sort_values("live", ascending=False).drop_duplicates("pc_key")
    d = d.merge(n.rename(columns={"lat": "nspl_lat", "long": "nspl_long", "live": "nspl_pc_live"}),
                on="pc_key", how="left")
    d["coord_source"] = np.where(d.Latitude.notna(), "fhrs", np.where(d.nspl_lat.notna(), "nspl_postcode", "none"))
    miss_before = d.Latitude.isna()
    d["lat"] = d.Latitude.fillna(d.nspl_lat)
    d["long"] = d.Longitude.fillna(d.nspl_long)
    summ = d.groupby("category").agg(
        establishments=("FHRSID", "size"),
        missing_coords_before=("Latitude", lambda s: s.isna().sum()),
        missing_postcode=("pc_key", lambda s: (s == "").sum()),
        missing_coords_after=("lat", lambda s: s.isna().sum()))
    summ.loc["all"] = summ.sum()
    summ["pct_geocoded_after"] = 100 * (1 - summ.missing_coords_after / summ.establishments)
    summ["extract_date"] = d.extract_date.max()
    summ.to_csv(CLEAN / "fhrs_geocode_summary.csv")
    print(summ.to_string())
    keep = ["FHRSID", "category", "BusinessName", "BusinessType", "AddressLine1", "AddressLine2", "AddressLine3",
            "AddressLine4", "PostCode", "lat", "long", "coord_source", "RatingValue", "RatingDate",
            "LocalAuthorityCode", "LocalAuthorityName", "extract_date"]
    d[keep].to_parquet(BIG / "fhrs_points_ew.parquet", index=False)
    print(f"wrote {len(d):,} points, missing coords before fill {miss_before.sum():,}, after {d.lat.isna().sum():,}")


if __name__ == "__main__":
    main()
