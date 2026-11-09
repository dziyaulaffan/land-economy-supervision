"""S3: download weekly-able COVID-19 cases by specimen date by lower-tier LA.

England: UKHSA data dashboard API, metric COVID-19_cases_casesByDay (cases by specimen date), years 2020-2021.
Wales: tried in order (see notes): UKHSA API (does not carry Wales), Public Health Wales rapid surveillance
workbook, archived coronavirus.data.gov.uk downloads.
Raw JSON pages are saved under RAW/covid_cases/ukhsa/.
"""
import json
import sys
import time
import urllib.parse
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ext_config import RAW, UA  # noqa: E402

OUT = RAW / "covid_cases" / "ukhsa"
OUT.mkdir(parents=True, exist_ok=True)
BASE = ("https://api.ukhsa-dashboard.data.gov.uk/themes/infectious_disease/sub_themes/respiratory/topics/COVID-19/"
        "geography_types/Lower%20Tier%20Local%20Authority/geographies")
METRIC = "COVID-19_cases_casesByDay"


def get(url, tries=5):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=120)
            if r.status_code == 200:
                return r.json()
            print("HTTP", r.status_code, url, flush=True)
        except requests.RequestException as e:
            print("ERR", e, flush=True)
        time.sleep(3 * (i + 1))
    raise RuntimeError(url)


def main():
    geos = get(BASE)
    (OUT / "geographies.json").write_text(json.dumps(geos))
    print(len(geos), "LTLA geographies", flush=True)
    for g in geos:
        name = g["name"]
        for year in (2020, 2021):
            dest = OUT / f"{METRIC}_{year}_{name.replace('/', '_').replace(',', '')}.json"
            if dest.exists() and dest.stat().st_size > 0:
                continue
            url = f"{BASE}/{urllib.parse.quote(name)}/metrics/{METRIC}?page_size=1000&year={year}"
            rows = []
            while url:
                d = get(url)
                rows += d["results"]
                url = d["next"]
            dest.write_text(json.dumps(rows))
            time.sleep(0.2)
        print("done", name, flush=True)


def nation():
    """England national series for validation."""
    dest = OUT.parent / "ukhsa_nation_england.json"
    if dest.exists():
        return
    url = (BASE.replace("Lower%20Tier%20Local%20Authority/geographies", "Nation/geographies")
           + f"/England/metrics/{METRIC}?page_size=1000")
    rows = []
    for year in (2020, 2021):
        u = url + f"&year={year}"
        while u:
            d = get(u)
            rows += d["results"]
            u = d["next"]
    dest.write_text(json.dumps(rows))


def population():
    """ONS mid-2020 population estimates, April 2023 LADs (Nomis NM_2002_1, geography TYPE424)."""
    dest = RAW / "nomis" / "mye_population_mid2020_la2023.csv"
    if dest.exists():
        return
    url = ("https://www.nomisweb.co.uk/api/v01/dataset/NM_2002_1.data.csv?geography=TYPE424&date=2020&gender=0"
           "&c_age=200&measures=20100&select=date_name,geography_name,geography_code,obs_value")
    r = requests.get(url, headers=UA, timeout=300)
    r.raise_for_status()
    dest.write_text(r.text)


if __name__ == "__main__":
    if sys.argv[1:] == ["nation"]:
        nation()
    elif sys.argv[1:] == ["population"]:
        population()
    else:
        main()
        nation()
