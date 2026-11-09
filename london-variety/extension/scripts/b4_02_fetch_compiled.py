"""B4 step 2: download the compiled restriction datasets used for verification, plus geography lookups.

Saved under RAW/restrictions/:
  zenodo/abel_siraj_tiers.csv          Abel & Siraj (2022), Zenodo 8191880: LTLA x day tier, 2 Dec 2020 - 5 Jan 2021
  zenodo/uk_tier_data-0.0.2.zip        Gibbs, Jarvis & Eggo (2021), Zenodo 4421649: daily scrapes of the Commons
                                       Library and Wikipedia tier tables, 25 Oct - 29 Nov 2020
  odileeds/snapshots/*.csv             every committed version (7 Oct 2020 - 21 Dec 2020) of the House of Commons
                                       Library local restrictions table, as mirrored by ODI Leeds on GitHub
  odileeds/populations.csv             ONS 2018-based subnational population projections by 2020 LTLA (ODI Leeds copy)
  wayback/utla_alertlevel_20210511.csv Wayback Machine copy of the UK coronavirus dashboard API (alertLevel, UTLA).
                                       The alertLevel column is empty in the archived copy, so it is not used.
  geography/ltla20_utla20.csv          ONS LTLA (Dec 2020) to UTLA lookup, England and Wales
  geography/wd20_lad20_partial.csv     ONS ward (Dec 2020) to LAD lookup, for the LAs where a regulation covered
                                       only listed wards / electoral divisions
  geography/ward_pop_mid2019.csv       ONS mid-2019 ward population estimates (Nomis NM_2010_1, 2019 wards)
  oxcgrt/OxCGRT_compact_subnational_v1.csv  OxCGRT subnational (UK nations only; no local authority detail)
"""
import subprocess
from pathlib import Path

import requests

from ext_config import RAW, UA

R = RAW / "restrictions"

FILES = {
    "zenodo/abel_siraj_tiers.csv":
        "https://zenodo.org/api/records/8191880/files/Covid-19%20UK%20government%20winter%202020%20tiered%20system%20data.csv/content",
    "zenodo/uk_tier_data-0.0.2.zip": "https://zenodo.org/api/records/4421649/files/uk_tier_data-0.0.2.zip/content",
    "wayback/utla_alertlevel_20210511.csv":
        "http://web.archive.org/web/20210511210848id_/https://api.coronavirus.data.gov.uk/v2/data?areaType=utla"
        "&metric=alertLevel&metric=newCasesBySpecimenDate&metric=newDeathsByDeathDate&format=csv",
}
LOOKUP = ("https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LTLA20_UTLA20_EW_LU_3791afa41dcc4daeab025767e16fcb93"
          "/FeatureServer/0/query?where=1%3D1&outFields=LTLA20CD,LTLA20NM,UTLA20CD,UTLA20NM&f=json&resultRecordCount=2000")
# LAs with ward-defined partial areas: BwD, Bradford, Calderdale, Kirklees, High Peak, Carmarthenshire, Gwynedd
PARTIAL_LAS = ["E06000008", "E08000032", "E08000033", "E08000034", "E07000037", "W06000010", "W06000002"]
WARD_LOOKUP = ("https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/WD20_LAD20_CTY20_OTH_UK_LU_v2_"
               "27715a77546b4b5a9746baf703dd9a05/FeatureServer/0/query?where=LAD20CD%20IN%20({})"
               "&outFields=WD20CD,WD20NM,LAD20CD,LAD20NM&f=json&resultRecordCount=2000")
WARD_POP = ("https://www.nomisweb.co.uk/api/v01/dataset/NM_2010_1.data.csv?geography=TYPE395&date=2019&gender=0"
            "&c_age=200&measures=20100&select=geography_name,geography_code,obs_value")
OXCGRT = "https://raw.githubusercontent.com/OxCGRT/covid-policy-dataset/main/data/OxCGRT_compact_subnational_v1.csv"
COMMONS_FILE = "LocalAuthorities/data/commonslibrary-coronavirus-restrictions-data.csv"


def get(url, dest: Path):
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, headers=UA, timeout=300)
    r.raise_for_status()
    dest.write_bytes(r.content)


def odileeds_snapshots():
    repo = R / "odileeds_git"
    if not repo.exists():
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout",
                        "https://github.com/odileeds/covid-19.git", str(repo)], check=True)
    out = R / "odileeds" / "snapshots"
    out.mkdir(parents=True, exist_ok=True)
    log = subprocess.run(["git", "-C", str(repo), "log", "--format=%h %ad", "--date=format:%Y%m%dT%H%M", "--",
                          COMMONS_FILE], capture_output=True, text=True, check=True).stdout.split("\n")
    for line in filter(None, log):
        h, d = line.split()
        dest = out / f"commonslib_{d}_{h}.csv"
        if not dest.exists():
            blob = subprocess.run(["git", "-C", str(repo), "show", f"{h}:{COMMONS_FILE}"], capture_output=True, check=True)
            dest.write_bytes(blob.stdout)
    pop = R / "odileeds" / "populations.csv"
    if not pop.exists():
        blob = subprocess.run(["git", "-C", str(repo), "show", "HEAD:LocalAuthorities/data/populations.csv"],
                              capture_output=True, check=True)
        pop.write_bytes(blob.stdout)


def main():
    for rel, url in FILES.items():
        get(url, R / rel)
    lk = R / "geography" / "ltla20_utla20.csv"
    if not lk.exists():
        import pandas as pd
        js = requests.get(LOOKUP, headers=UA, timeout=120).json()
        lk.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([f["attributes"] for f in js["features"]]).to_csv(lk, index=False)
    wl = R / "geography" / "wd20_lad20_partial.csv"
    if not wl.exists():
        import pandas as pd
        q = WARD_LOOKUP.format(",".join(f"'{c}'" for c in PARTIAL_LAS))
        js = requests.get(q, headers=UA, timeout=120).json()
        pd.DataFrame([f["attributes"] for f in js["features"]]).to_csv(wl, index=False)
    get(WARD_POP, R / "geography" / "ward_pop_mid2019.csv")
    get(OXCGRT, R / "oxcgrt" / "OxCGRT_compact_subnational_v1.csv")
    odileeds_snapshots()
    import zipfile
    z = R / "zenodo" / "uk_tier_data"
    if not z.exists():
        zipfile.ZipFile(R / "zenodo" / "uk_tier_data-0.0.2.zip").extractall(z)
    print("compiled sources in", R)


if __name__ == "__main__":
    main()
