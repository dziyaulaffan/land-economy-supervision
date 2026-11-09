"""B1d helper. UK Business Counts local units (Nomis NM_141_1) by SIC 2007 subclass for local authorities
(TYPE424, April 2023 boundaries), March 2019, 2022 and the latest year, plus ONS mid-year population
(NM_2002_1) for 2019 and 2022 on the same geography. Raw files in RAW/nomis.
"""
import pandas as pd

from ext_config import RAW, download

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
SUBCLASSES = {
    "134273829": "56101", "134273830": "56102", "134273831": "56103", "134273938": "56210", "134274018": "56290",
    "134274029": "56301", "134274030": "56302", "134276868": "59140", "134307738": "90010", "134307748": "90020",
    "134307758": "90030", "134307768": "90040", "134310838": "93110", "134310858": "93130",
}


def main():
    for yr in ["2019", "2022", "latest"]:
        url = (f"{NOMIS}/NM_141_1.data.csv?geography=TYPE424&date={yr}&industry={','.join(SUBCLASSES)}"
               "&employment_sizeband=0&legal_status=0&measures=20100"
               "&select=date_name,geography_name,geography_code,industry,industry_name,obs_value,obs_status_name")
        f = download(url, RAW / "nomis" / f"ukbc_local_units_{yr}_subclasses_la2023.csv")
        u = pd.read_csv(f)
        print(yr, len(u), u.DATE_NAME.unique(), u.OBS_STATUS_NAME.value_counts().to_dict())
    for yr in ["2019", "2022"]:
        url = (f"{NOMIS}/NM_2002_1.data.csv?geography=TYPE424&date={yr}&gender=0&c_age=200&measures=20100"
               "&select=date_name,geography_name,geography_code,obs_value")
        f = download(url, RAW / "nomis" / f"mye_population_mid{yr}_la2023.csv")
        print("pop", yr, len(pd.read_csv(f)))


if __name__ == "__main__":
    main()
