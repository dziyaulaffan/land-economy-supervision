"""V1a. Download the extra regulation texts needed to date closures by venue type (England and Wales).

The B4 restriction history (extension/scripts/b4_01) already holds the made texts of every regulation it used,
plus point-in-time copies of the area schedules. Venue-level dates need two more things:
  made/  two amending SIs that B4 did not keep (2020/788 gyms and pools, 2020/863 other leisure, England)
  pit/   point-in-time copies of the closure schedules on the dates when venue lists changed
Saved under RAW/venue_mix/legislation/.
"""
import time

import requests

from vm_common import UA, VRAW

OUT = VRAW / "legislation"
BASE = "https://www.legislation.gov.uk"
MADE = ["uksi/2020/788", "uksi/2020/863", "uksi/2020/1611", "wsi/2020/803", "wsi/2020/820"]
PIT = {
    # England: No. 2 Regulations closure list (Schedule 2), 4 Jul to 4 Nov 2020
    "uksi/2020/684": ["2020-07-04", "2020-07-24", "2020-07-25", "2020-08-14", "2020-08-15", "2020-09-14",
                      "2020-10-14", "2020-11-04"],
    # England: Leicester (No. 2), whole text, to date the end of the Leicester gym closure (gone on 8 Sep in B4's copy)
    "uksi/2020/824": ["2020-09-04", "2020-09-05", "2020-09-06", "2020-09-07"],
    # England: December tiers incl. Tier 4 (inserted 20 Dec), whole text
    "uksi/2020/1374": ["2020-12-02", "2020-12-19", "2020-12-20", "2020-12-31", "2021-01-05"],
    # England: Steps regulations, whole text
    "uksi/2021/364": ["2021-03-29", "2021-04-11", "2021-04-12", "2021-05-16", "2021-05-17", "2021-07-18"],
    # Wales: No. 2 Regulations, whole text, July to October 2020
    "wsi/2020/725": ["2020-07-13", "2020-07-20", "2020-07-27", "2020-08-03", "2020-08-10", "2020-08-17",
                     "2020-08-31", "2020-09-14", "2020-10-01", "2020-10-22"],
    # Wales: No. 4 Regulations (after the firebreak), whole text
    "wsi/2020/1219": ["2020-11-09", "2020-12-03", "2020-12-04", "2020-12-19"],
    # Wales: No. 5 Regulations (alert levels), whole text
    "wsi/2020/1609": ["2020-12-20", "2021-01-15", "2021-03-13", "2021-03-27", "2021-04-12", "2021-04-26",
                      "2021-05-03", "2021-05-17", "2021-06-07", "2021-07-17", "2021-08-06", "2021-08-07"],
}


def get(url, dest):
    if dest.exists() and dest.stat().st_size > 1000:
        return "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    for k in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=120)
            if r.status_code == 200 and len(r.content) > 1000:
                dest.write_bytes(r.content)
                time.sleep(0.5)
                return "ok"
            last = r.status_code
        except requests.RequestException as e:
            last = repr(e)
        time.sleep(2 + 3 * k)
    return f"failed {last}"


def main():
    for si in MADE:
        print(si, get(f"{BASE}/{si}/made/data.xml", OUT / "made" / f"{si.replace('/', '_')}.xml"))
    for si, dates in PIT.items():
        for d in dates:
            print(si, d, get(f"{BASE}/{si}/{d}/data.xml", OUT / "pit" / f"{si.replace('/', '_')}_{d}.xml"))


if __name__ == "__main__":
    main()
