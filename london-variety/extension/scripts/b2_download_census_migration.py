"""B2: download public Census 2021 migration (address one year ago) tables.

Sources
- Nomis Census 2021 origin-destination bulk zips (ODMG, ODST series):
  https://www.nomisweb.co.uk/sources/census_2021_od
- Nomis Census 2021 bulk topic summaries (TS019 migrant indicator, TS007A age):
  https://www.nomisweb.co.uk/sources/census_2021_bulk
- ONS census-observations API (custom datasets, migrant indicator x age):
  https://api.beta.ons.gov.uk/v1/population-types/UR/census-observations

Data assembly only. Zips are extracted with zipfile (no code from the downloads is run).
"""
import json
import time
import zipfile

import requests

from ext_config import RAW, UA, download

OUT = RAW / "census2021_migration"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "ons_api").mkdir(exist_ok=True)

NOMIS_OD = "https://www.nomisweb.co.uk/output/census/2021/{}.zip"
OD_TABLES = ["odmg01ew", "odmg01ew_non_uk", "odmg02ew", "odmg02ew_non_uk", "odmg10ew",
             "odst01ew", "odst02ew"]
NOMIS_TS = "https://www.nomisweb.co.uk/output/census/2021/census2021-{}.zip"
TS_TABLES = ["ts019", "ts007a", "ts007"]

ONS_API = "https://api.beta.ons.gov.uk/v1/population-types/UR/census-observations"


def fetch_zip(url, name):
    dest = OUT / f"{name}.zip"
    try:
        download(url, dest)
    except Exception as e:  # record and move on
        print("FAILED", url, e)
        return None
    d = OUT / name
    if not d.exists():
        with zipfile.ZipFile(dest) as z:
            z.extractall(d)
    print("ok", name, dest.stat().st_size, sorted(p.name for p in d.rglob("*"))[:12])
    return d


MAX_ROWS = 45000   # the API refuses queries above roughly 50,000 observations (403 'Too many rows')


def _parse(js, age_dim):
    rows = []
    for o in js.get("observations", []):
        dd = {x["dimension_id"]: x["option_id"] for x in o["dimensions"]}
        area = [v for k, v in dd.items() if k not in ("migrant_ind", age_dim)][0]
        rows.append((area, dd["migrant_ind"], dd[age_dim], o["observation"]))
    return rows


def ons_custom(area_type, codes, age_dim, n_age):
    """ONS 'create a custom dataset' API (census-observations), queried in chunks of areas.

    Writes raw JSON (gzipped) per chunk, a parsed long CSV, and the list of areas the API
    blocked under its disclosure rules.
    """
    import gzip
    import pandas as pd
    d = OUT / "ons_api" / f"{area_type}_migrant_ind_{age_dim}"
    d.mkdir(parents=True, exist_ok=True)
    out_csv = d.parent / f"{area_type}_migrant_ind_{age_dim}.csv"
    if out_csv.exists():
        return pd.read_csv(out_csv, dtype=str)
    step = max(1, MAX_ROWS // (5 * n_age))
    all_rows, blocked = [], []
    for i in range(0, len(codes), step):
        chunk = codes[i:i + step]
        f = d / f"chunk_{i:05d}.json.gz"
        if f.exists():
            js = json.loads(gzip.decompress(f.read_bytes()))
        else:
            url = f"{ONS_API}?area-type={area_type},{','.join(chunk)}&dimensions=migrant_ind,{age_dim}"
            for attempt in range(4):
                try:
                    r = requests.get(url, headers=UA, timeout=600)
                    if r.status_code == 200:
                        break
                    if r.status_code == 400:   # the API answers 400 when every requested area is blocked
                        break
                    print("status", r.status_code, r.text[:200])
                except requests.RequestException as e:
                    print("retry", e)
                time.sleep(5 * (attempt + 1))
            if r.status_code == 400:
                print("400: all areas in chunk blocked (or bad request)", r.text[:200])
                js = {"observations": []}
                time.sleep(0.5)
            else:
                r.raise_for_status()
                f.write_bytes(gzip.compress(r.content))
                js = r.json()
            time.sleep(0.5)
        rows = _parse(js, age_dim)
        got = {a for a, *_ in rows}
        blocked += [c for c in chunk if c not in got]
        all_rows += rows
        print(area_type, age_dim, i, len(rows), "blocked so far", len(blocked))
    df = pd.DataFrame(all_rows, columns=["area_code", "migrant_ind", "age_code", "count"])
    df.to_csv(out_csv, index=False)
    pd.Series(blocked, name="area_code").to_csv(d.parent / f"{area_type}_migrant_ind_{age_dim}_blocked.csv", index=False)
    return df.astype(str)


def api_categories(dim):
    """Save the category labels for an API classification."""
    dest = OUT / "ons_api" / f"categories_{dim}.json"
    if not dest.exists():
        url = f"https://api.beta.ons.gov.uk/v1/population-types/UR/dimensions/{dim}/categorisations?limit=100"
        r = requests.get(url, headers=UA, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)


if __name__ == "__main__":
    import pandas as pd
    for t in OD_TABLES:
        fetch_zip(NOMIS_OD.format(t), t)
    for t in TS_TABLES:
        fetch_zip(NOMIS_TS.format(t), f"census2021-{t}")
    api_categories("migrant_ind")
    api_categories("resident_age_101a")
    msoa = pd.read_csv(OUT / "census2021-ts019" / "census2021-ts019-msoa.csv")["geography code"].tolist()
    ltla = pd.read_csv(OUT / "census2021-ts019" / "census2021-ts019-ltla.csv")["geography code"].tolist()
    # LA: single year of age (finest) and the 23-band classification matching ODMG02EW.
    ons_custom("ltla", ltla, "resident_age_101a", 101)
    ons_custom("ltla", ltla, "resident_age_23a", 23)
    # MSOA: 23 bands (matches ODMG02EW bands) then single year (finest, some areas blocked).
    ons_custom("msoa", msoa, "resident_age_23a", 23)
    ons_custom("msoa", msoa, "resident_age_86a", 86)
    # Fallbacks for MSOAs the API blocks at 23 bands: progressively coarser classifications.
    blocked = pd.read_csv(OUT / "ons_api" / "msoa_migrant_ind_resident_age_23a_blocked.csv")["area_code"].tolist()
    for dim, n in [("resident_age_18b", 18), ("resident_age_11a", 11), ("resident_age_8c", 8), ("resident_age_6a", 6)]:
        if not blocked:
            break
        df = ons_custom(f"msoa", blocked, dim, n)
        blocked = pd.read_csv(OUT / "ons_api" / f"msoa_migrant_ind_{dim}_blocked.csv")["area_code"].tolist()
    print("MSOAs still blocked after fallbacks:", len(blocked))
