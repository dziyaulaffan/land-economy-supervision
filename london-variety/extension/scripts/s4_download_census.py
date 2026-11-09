"""S4: download Census 2011 and 2001 migration-by-age and population tables from the Nomis API.

Nomis returns at most 25,000 rows per anonymous call, so each query is paged with recordoffset.
Raw CSVs go to RAW/nomis/s4/. Tables:
  2011 UKMIG001 (NM_1280_1) Migration by sex by age, 2011 MSOA (TYPE297) and England and Wales.
  2001 ST008  (NM_1808_1) Resident type and sex and age by migration, 2003 ST wards (TYPE311),
       pre-2009 districts (TYPE464) and England and Wales.
  2001 KS024  (NM_1632_1) Migration, 2001 output areas (TYPE310) and England and Wales.
  2001 UV004  (NM_1637_1) Age (single year), 2001 MSOA (TYPE305) and England and Wales.
  2011 UKMIG008 (NM_1287_1) Migration, countries (published national totals for validation).
  2011 KS101EW (NM_144_1) Usual residents, 2011 output areas (TYPE299, apportionment weights) and E&W.
"""
import io
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ext_config import RAW, UA  # noqa: E402

OUT = RAW / "nomis" / "s4"
OUT.mkdir(parents=True, exist_ok=True)
API = "https://www.nomisweb.co.uk/api/v01/dataset/{}.data.csv"
EW = "2092957703"

QUERIES = {
    # name: (dataset, params)
    "ukmig001_msoa11": ("NM_1280_1", dict(geography="TYPE297", c_sex="0", c_age="0...9", c_migr="0...9")),
    "ukmig001_ew": ("NM_1280_1", dict(geography=EW, c_sex="0", c_age="0...9", c_migr="0...9")),
    "st008_stward03": ("NM_1808_1", dict(geography="TYPE311", c_res="0", c_sex="0", c_age="0...23", c_migr="0...5")),
    "st008_lad": ("NM_1808_1", dict(geography="TYPE464", c_res="0", c_sex="0", c_age="0...23", c_migr="0...5")),
    "st008_ew": ("NM_1808_1", dict(geography=EW, c_res="0", c_sex="0", c_age="0...23", c_migr="0...8")),
    "ks024_oa01": ("NM_1632_1", dict(geography="TYPE310", c_migr="0...6")),
    "ks024_ew": ("NM_1632_1", dict(geography=EW, c_migr="0...13")),
    "uv004_msoa01": ("NM_1637_1", dict(geography="TYPE305", c_age="0...81")),
    "uv004_ew": ("NM_1637_1", dict(geography=EW, c_age="0...81")),
    "ukmig008_ctry": ("NM_1287_1", dict(geography="TYPE499", c_migr="0...6")),
    "ks101ew_oa11": ("NM_144_1", dict(geography="TYPE299", cell="0", rural_urban="0")),
    "ks101ew_ew": ("NM_144_1", dict(geography=EW, cell="0", rural_urban="0")),
}
SELECT = {
    "NM_1280_1": "geography_code,geography_name,c_age,c_age_name,c_migr,c_migr_name,obs_value",
    "NM_1808_1": "geography_code,geography_name,c_age,c_age_name,c_migr,c_migr_name,obs_value",
    "NM_1632_1": "geography_code,c_migr,c_migr_name,obs_value",
    "NM_1637_1": "geography_code,geography_name,c_age,c_age_name,obs_value",
    "NM_1287_1": "geography_code,geography_name,c_migr,c_migr_name,obs_value",
    "NM_144_1": "geography_code,obs_value",
}


def get(url, params):
    for attempt in range(6):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=300)
            if r.status_code == 200:
                return r.text
            print("HTTP", r.status_code, r.text[:200], flush=True)
        except requests.RequestException as e:
            print("ERR", e, flush=True)
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(url)


def run(name, ds, params):
    dest = OUT / f"{name}.csv"
    if dest.exists() and dest.stat().st_size > 0:
        print("have", name)
        return
    parts, offset = [], 0
    while True:
        p = dict(params, measures="20100", select=SELECT[ds], recordoffset=str(offset))
        df = pd.read_csv(io.StringIO(get(API.format(ds), p)))
        parts.append(df)
        if len(df) < 25000:
            break
        offset += len(df)
        print(name, offset, flush=True)
        time.sleep(1)
    out = pd.concat(parts, ignore_index=True)
    out.to_csv(dest, index=False)
    print("saved", name, len(out), flush=True)


if __name__ == "__main__":
    only = sys.argv[1:]
    for k, (ds, prm) in QUERIES.items():
        if not only or k in only:
            run(k, ds, prm)
