"""B1a. Download FSA Food Hygiene Rating Scheme open data XML files for every LA in England and Wales.

Authority list from the FHRS API (api.ratings.food.gov.uk/Authorities, x-api-version 2); one English-language
XML file per authority from ratings.food.gov.uk. Polite: 1.5 s between requests, retries with backoff,
skips files already on disk (resumable). Writes the authority list and a download log to RAW/fhrs.
"""
import json
import time
from datetime import date

import pandas as pd
import requests

from ext_config import RAW, UA

OUT = RAW / "fhrs"
OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.ratings.food.gov.uk"
HDR = {**UA, "x-api-version": "2", "Accept": "application/json"}


def get(url, headers, tries=5, timeout=300):
    for k in range(tries):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                return r
            print(f"  HTTP {r.status_code} {url}")
        except requests.RequestException as e:
            print(f"  error {e!r} {url}")
        time.sleep(5 * 2 ** k)
    raise RuntimeError(f"failed: {url}")


def main():
    af = OUT / "authorities.json"
    if not af.exists():
        af.write_bytes(get(f"{API}/Authorities", HDR).content)
    auth = pd.DataFrame(json.loads(af.read_text(encoding="utf-8"))["authorities"])
    ew = auth[~auth.RegionName.isin(["Scotland", "Northern Ireland"])].copy()
    print(f"{len(auth)} authorities, {len(ew)} in England and Wales")
    log = []
    for _, a in ew.iterrows():
        dest = OUT / f"FHRS{a.LocalAuthorityIdCode}en-GB.xml"
        if dest.exists() and dest.stat().st_size > 0:
            log.append(dict(code=a.LocalAuthorityIdCode, name=a.Name, file=dest.name, status="already on disk"))
            continue
        r = get(a.FileName, UA)
        tmp = dest.with_suffix(".part")
        tmp.write_bytes(r.content)
        tmp.replace(dest)
        log.append(dict(code=a.LocalAuthorityIdCode, name=a.Name, file=dest.name, status="downloaded",
                        date=str(date.today()), bytes=len(r.content)))
        print(a.Name, len(r.content))
        time.sleep(1.5)
    pd.DataFrame(log).to_csv(OUT / "download_log.csv", index=False, mode="a",
                             header=not (OUT / "download_log.csv").exists())
    ew.drop(columns="links").to_csv(OUT / "authorities_ew.csv", index=False)


if __name__ == "__main__":
    main()
