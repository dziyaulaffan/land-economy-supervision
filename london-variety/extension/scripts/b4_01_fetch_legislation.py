"""B4 step 1: download the COVID-19 restriction regulations (England and Wales) from legislation.gov.uk.

Two kinds of download, both saved under RAW/restrictions/legislation/:
  made/<type>_<year>_<number>.xml        the regulations as made (coming-into-force date, area schedules)
  pit/<type>_<year>_<number>_<part>_<date>.xml  point-in-time versions of the schedules that list
                                          the areas in each tier, one per day over the tier periods
legislation.gov.uk publishes revised (point-in-time) versions of these SIs, so the daily pull gives the
area lists in force on each date, including every amendment, without our reading each amending SI.
Compiled datasets used for verification are downloaded by b4_02_fetch_compiled.py.
"""
import time
from datetime import date, timedelta

import requests

from ext_config import RAW, UA

OUT = RAW / "restrictions" / "legislation"
BASE = "https://www.legislation.gov.uk"

# Regulations whose "made" text we keep (coming-into-force dates and area schedules)
MADE = [
    # England national
    "uksi/2020/327", "uksi/2020/350", "uksi/2020/684", "uksi/2020/1008", "uksi/2020/1029", "uksi/2020/1046",
    "uksi/2020/1200", "uksi/2020/1374", "uksi/2021/8", "uksi/2021/364", "uksi/2021/585", "uksi/2021/848",
    # England local measures, July to October 2020
    "uksi/2020/685", "uksi/2020/754", "uksi/2020/787", "uksi/2020/800", "uksi/2020/822", "uksi/2020/823",
    "uksi/2020/824", "uksi/2020/828", "uksi/2020/846", "uksi/2020/865", "uksi/2020/875", "uksi/2020/897",
    "uksi/2020/898", "uksi/2020/930", "uksi/2020/931", "uksi/2020/935", "uksi/2020/954", "uksi/2020/974",
    "uksi/2020/987", "uksi/2020/988", "uksi/2020/1010", "uksi/2020/1012", "uksi/2020/1019", "uksi/2020/1041",
    "uksi/2020/1057", "uksi/2020/1074",
    # England tiers, October 2020
    "uksi/2020/1103", "uksi/2020/1104", "uksi/2020/1105", "uksi/2020/1128", "uksi/2020/1131", "uksi/2020/1154",
    "uksi/2020/1176", "uksi/2020/1183", "uksi/2020/1189", "uksi/2020/1192",
    # England tiers, December 2020
    "uksi/2020/1533", "uksi/2020/1572", "uksi/2020/1611", "uksi/2020/1646", "uksi/2020/1654",
    # Wales
    "wsi/2020/326", "wsi/2020/334", "wsi/2020/353", "wsi/2020/725", "wsi/2020/1149", "wsi/2020/1219",
    "wsi/2020/1609", "wsi/2020/985", "wsi/2020/1007", "wsi/2020/1022", "wsi/2020/1035", "wsi/2020/1040",
    "wsi/2020/1043", "wsi/2020/1049", "wsi/2020/1066", "wsi/2020/1079", "wsi/2020/1102", "wsi/2020/1130",
    "wsi/2020/752", "wsi/2020/803", "wsi/2020/820", "wsi/2020/1409", "wsi/2020/1610", "wsi/2020/1623",
    "wsi/2021/57", "wsi/2021/307", "wsi/2021/413", "wsi/2021/457", "wsi/2021/502", "wsi/2021/542",
    "wsi/2021/583", "wsi/2021/668", "wsi/2021/686", "wsi/2021/722", "wsi/2021/862", "wsi/2021/925",
    "wsi/2021/970", "wsi/2021/1468", "wsi/2021/1477", "wsi/2021/1485", "wsi/2021/1490",
    "uksi/2021/321", "uksi/2021/1416",
]

# Point-in-time schedules: (SI, schedule path, first date, last date)
PIT = [
    ("uksi/2020/1104", "schedule/2", date(2020, 10, 14), date(2020, 11, 4)),    # High (Tier 2) area
    ("uksi/2020/1105", "schedule/2", date(2020, 10, 14), date(2020, 11, 4)),    # Very High (Tier 3) area
    ("uksi/2020/1105", "schedule/2A", date(2020, 10, 14), date(2020, 11, 4)),   # local closures in Tier 3
    ("uksi/2020/1374", "schedule/4", date(2020, 12, 2), date(2021, 1, 5)),      # Tier 2, 3 and 4 areas
    ("wsi/2020/725", "schedule/4A", date(2020, 9, 7), date(2020, 10, 23)),      # Welsh local health protection areas
]

# England 2021 Steps: Schedule 4 lists the Step 1/2/3 areas
STEP_DATES = ["2021-03-29", "2021-04-11", "2021-04-12", "2021-05-16", "2021-05-17", "2021-07-18"]

# England local regulations, July to October 2020: whole text in force on each date on which any of them
# changed (coming-into-force dates of the SIs in MADE), so the protected areas can be read off directly.
LOCAL = ["uksi/2020/685", "uksi/2020/800", "uksi/2020/822", "uksi/2020/824", "uksi/2020/828", "uksi/2020/974",
         "uksi/2020/988", "uksi/2020/1010"]
LOCAL_DATES = ["2020-07-04", "2020-07-18", "2020-07-24", "2020-07-25", "2020-08-01", "2020-08-03", "2020-08-05",
               "2020-08-08", "2020-08-15", "2020-08-19", "2020-08-26", "2020-09-02", "2020-09-03", "2020-09-08",
               "2020-09-10", "2020-09-15", "2020-09-18", "2020-09-22", "2020-09-24", "2020-09-26", "2020-09-30",
               "2020-10-03", "2020-10-13"]


def get(url: str, dest) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    r = requests.get(url, headers=UA, timeout=120)
    time.sleep(0.4)
    if r.status_code != 200:
        print("  ", r.status_code, url)
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    return True


def main():
    for si in MADE:
        get(f"{BASE}/{si}/made/data.xml", OUT / "made" / (si.replace("/", "_") + ".xml"))
    for si, part, d0, d1 in PIT:
        d = d0
        while d <= d1:
            name = f"{si.replace('/', '_')}_{part.replace('/', '')}_{d.isoformat()}.xml"
            get(f"{BASE}/{si}/{part}/{d.isoformat()}/data.xml", OUT / "pit" / name)
            d += timedelta(days=1)
    for d in STEP_DATES:
        get(f"{BASE}/uksi/2021/364/schedule/4/{d}/data.xml", OUT / "pit" / f"uksi_2021_364_schedule4_{d}.xml")
    for si in LOCAL:
        for d in LOCAL_DATES:
            get(f"{BASE}/{si}/{d}/data.xml", OUT / "pit_local" / f"{si.replace('/', '_')}_{d}.xml")
    print("done:", sum(1 for _ in OUT.rglob("*.xml")), "files in", OUT)


if __name__ == "__main__":
    main()
