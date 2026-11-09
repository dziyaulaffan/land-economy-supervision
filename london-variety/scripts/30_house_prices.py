"""House prices: HM Land Registry Price Paid Data, yearly files 2017-2023.

Output: monthly median price and transaction counts by local authority (2023 boundaries)
and property type, for London, South East and East of England.

District names in Price Paid are matched to ONS 2023 LA names. Districts abolished in
2019-2020 reorganisations are mapped to their successor authority so the panel is on
consistent 2023 boundaries. City of London is excluded from the analysis panel; its sales
fall into no LA and are dropped.
"""
import re

import pandas as pd

from config import CITY, CLEAN, RAW, download, la_region_lookup

YEARS = range(2017, 2024)
URL = "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-{y}.csv"
COLS = ["txn_id", "price", "date", "postcode", "property_type", "old_new", "duration", "paon", "saon",
        "street", "locality", "town", "district", "county", "ppd_category", "record_status"]
USE = ["price", "date", "property_type", "old_new", "duration", "district", "ppd_category"]
PTYPE = {"D": "Detached", "S": "Semi-detached", "T": "Terraced", "F": "Flat/maisonette", "O": "Other"}

# pre-2023 districts in South East / East of England (merged or renamed) -> 2023 LA name
SUCCESSOR = {
    "AYLESBURY VALE": "Buckinghamshire", "CHILTERN": "Buckinghamshire", "SOUTH BUCKS": "Buckinghamshire",
    "WYCOMBE": "Buckinghamshire", "SUFFOLK COASTAL": "East Suffolk", "WAVENEY": "East Suffolk",
    "FOREST HEATH": "West Suffolk", "ST EDMUNDSBURY": "West Suffolk",
    "SHEPWAY": "Folkestone and Hythe",  # renamed April 2018
}


def norm(s: str) -> str:
    s = s.upper().replace("&", "AND")
    s = re.sub(r"^CITY OF ", "", s)
    s = re.sub(r", CITY OF$", "", s)
    s = re.sub(r"[^A-Z ]", "", s.replace("-", " "))
    s = s.replace("ST ", "ST ").replace("SAINT ", "ST ")
    return re.sub(r"\s+", " ", s).strip()


def main():
    raw = RAW / "land_registry"
    frames = []
    for y in YEARS:
        f = download(URL.format(y=y), raw / f"pp-{y}.csv")
        d = pd.read_csv(f, header=None, names=COLS, usecols=USE, dtype=str)
        d["price"] = d.price.astype(int)
        frames.append(d)
    pp = pd.concat(frames, ignore_index=True)
    pp["month"] = pd.to_datetime(pp.date.str[:10]).dt.to_period("M").dt.to_timestamp()
    pp = pp[(pp.month >= "2017-01-01") & (pp.month <= "2023-12-01")]

    lk = la_region_lookup()
    lk = lk[lk.region.isin(["London", "South East", "East of England"]) & (lk.la_code != CITY)].copy()
    lk["key"] = lk.la_name.map(norm)
    keymap = dict(zip(lk.key, lk.la_code))
    succ = {k: keymap[norm(v)] for k, v in SUCCESSOR.items()}

    districts = pd.Series(pp.district.unique())
    dmap = {d: succ.get(d, keymap.get(norm(d))) for d in districts}
    pp["la_code"] = pp.district.map(dmap)
    matched = {d for d, c in dmap.items() if c}
    unmatched_in_lk = set(lk.la_code) - set(dmap.values())
    assert not unmatched_in_lk, f"LAs with no Price Paid district: {unmatched_in_lk}"
    pd.DataFrame({"district": sorted(matched), "la_code": [dmap[d] for d in sorted(matched)]}).to_csv(
        CLEAN / "land_registry_district_to_la.csv", index=False)

    pp = pp[pp.la_code.notna()].merge(lk[["la_code", "la_name", "region"]], on="la_code")
    pp["property_type"] = pp.property_type.map(PTYPE)
    keys = ["la_code", "la_name", "region", "month"]

    def agg(df, ptype_label=None):
        by = keys + ([] if ptype_label else ["property_type"])
        out = df.groupby(by).agg(n_all=("price", "size")).join(
            df[df.ppd_category == "A"].groupby(by).agg(median_price_catA=("price", "median"),
                                                           mean_price_catA=("price", "mean"),
                                                           n_catA=("price", "size")))
        out = out.reset_index()
        if ptype_label:
            out["property_type"] = ptype_label
        return out

    panel = pd.concat([agg(pp), agg(pp, "All")], ignore_index=True)
    # balance: every LA x month x type, zero counts where no sales
    full = pd.MultiIndex.from_product(
        [panel.la_code.unique(), pd.date_range("2017-01-01", "2023-12-01", freq="MS"),
         list(PTYPE.values()) + ["All"]], names=["la_code", "month", "property_type"]).to_frame(index=False)
    full = full.merge(lk[["la_code", "la_name", "region"]], on="la_code")
    panel = full.merge(panel, on=["la_code", "la_name", "region", "month", "property_type"], how="left")
    panel[["n_all", "n_catA"]] = panel[["n_all", "n_catA"]].fillna(0).astype(int)
    panel = panel.sort_values(["region", "la_code", "property_type", "month"])
    panel.to_csv(CLEAN / "house_prices_monthly_la_type_2017_2023.csv", index=False)
    print(panel.groupby("region").la_code.nunique(), panel.shape)
    print("transactions kept:", len(pp))


if __name__ == "__main__":
    main()
