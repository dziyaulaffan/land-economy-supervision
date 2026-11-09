"""S1 downloads: Census 2011 LA tables for all of England and Wales (Nomis API) and Census 2021 bulk
topic-summary tables (Nomis bulk zips). Files that the pilot or earlier extension blocks already hold
(ONS gardens April 2020, ONS homeworking 2020, NSPL, TS007/TS007A) are reused, not downloaded again.

Raw files go to ext_config.RAW / "s1". Nothing in the download folders is executed.
"""
import time
import zipfile

import pandas as pd
import requests

from ext_config import RAW, UA, download

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
BULK = "https://www.nomisweb.co.uk/output/census/2021"
ONS_API = "https://api.beta.ons.gov.uk/v1/population-types/UR/census-observations"
OUT11 = RAW / "s1" / "census2011_la"
OUT21 = RAW / "s1" / "census2021_bulk"
API = RAW / "s1" / "ons_api"
API.mkdir(parents=True, exist_ok=True)
GEO_LA2011 = "TYPE464"  # LA districts / unitaries prior to April 2015 (348 in England and Wales)

# table id, Nomis dataset, dimension filter, select columns
TABLES_2011 = {
    "qs103ew_age": ("NM_503_1", "c_age=0,21...40", "geography_code,geography_name,c_age,c_age_name,obs_value"),
    "ks402ew_tenure": ("NM_619_1", "cell=0,300", "geography_code,geography_name,cell,cell_name,obs_value"),
    "qs606ew_occupation": ("NM_561_1", "cell=0...124", "geography_code,geography_name,cell,cell_name,obs_value"),
    "ks501ew_students": ("NM_623_1", "cell=0,9", "geography_code,geography_name,cell,cell_name,obs_value"),
    "qs402ew_accommodation": ("NM_534_1", "dwelling_type=0...11",
                              "geography_code,geography_name,dwelling_type,dwelling_type_name,obs_value"),
}
TABLES_2021 = ["ts044", "ts054", "ts063", "ts068", "ts066"]


def nomis_paged(name: str, ds: str, extra: str, select: str) -> pd.DataFrame:
    """Nomis serves at most 25,000 rows per call without an API key; page with recordoffset."""
    out = OUT11 / f"{name}_la2011_ew.csv"
    if out.exists():
        return pd.read_csv(out)
    url = f"{NOMIS}/{ds}.data.csv?geography={GEO_LA2011}&rural_urban=0&{extra}&measures=20100&select={select}"
    pages, offset = [], 0
    while True:
        f = download(f"{url}&recordoffset={offset}", OUT11 / "pages" / f"{name}_{offset}.csv")
        page = pd.read_csv(f)
        pages.append(page)
        if len(page) < 25000:
            break
        offset += 25000
    d = pd.concat(pages, ignore_index=True)
    d.to_csv(out, index=False)
    return d


def bulk(t: str) -> list:
    z = download(f"{BULK}/census2021-{t}.zip", OUT21 / f"census2021-{t}.zip")
    dest = OUT21 / f"census2021-{t}"
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        for n in names:
            if n.endswith(".csv") and not (dest / n).exists():
                zf.extract(n, dest)  # CSV data only
    return names


def students_msoa(codes: list, chunk: int = 300) -> pd.DataFrame:
    """Census 2021 full-time students by age at MSOA from the ONS custom-dataset API (TS066/TS068 have no
    age split). economic_activity_status_7a x resident_age_7a: 49 cells per MSOA."""
    out = API / "msoa_economic_activity_status_7a_resident_age_7a.csv"
    if out.exists():
        return pd.read_csv(out)
    rows, blocked = [], []
    for i in range(0, len(codes), chunk):
        part = codes[i:i + chunk]
        url = f"{ONS_API}?area-type=msoa,{','.join(part)}&dimensions=economic_activity_status_7a,resident_age_7a"
        for attempt in range(5):
            try:
                r = requests.get(url, headers=UA, timeout=300)
                if r.status_code == 429 or r.status_code >= 500:
                    raise requests.HTTPError(r.status_code)
                break
            except (requests.ConnectionError, requests.HTTPError, requests.Timeout):
                time.sleep(10 * (attempt + 1))
        r.raise_for_status()
        got = set()
        for o in r.json()["observations"]:
            dd = {x["dimension_id"]: x["option_id"] for x in o["dimensions"]}
            rows.append((dd["msoa"], int(dd["economic_activity_status_7a"]), int(dd["resident_age_7a"]),
                         o["observation"]))
            got.add(dd["msoa"])
        blocked += [c for c in part if c not in got]
        print("students API", i, len(rows), "blocked", len(blocked), flush=True)
    d = pd.DataFrame(rows, columns=["msoa21cd", "econ7", "age7", "obs"])
    d.to_csv(out, index=False)
    pd.Series(blocked, name="msoa21cd").to_csv(API / "msoa_students_blocked.csv", index=False)
    return d


def main():
    codes = pd.read_csv(OUT21 / "census2021-ts068" / "census2021-ts068-msoa.csv")["geography code"].tolist()
    students_msoa(codes)
    for name, (ds, extra, select) in TABLES_2011.items():
        d = nomis_paged(name, ds, extra, select)
        print(f"{name}: {len(d):,} rows, {d.GEOGRAPHY_CODE.nunique()} LAs", flush=True)
    for t in TABLES_2021:
        print(t, [n for n in bulk(t) if "msoa" in n.lower() or "ltla" in n.lower()], flush=True)


if __name__ == "__main__":
    main()
