"""Shared paths, geography lists and helpers for the London consumption-variety pilot."""
import os
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
# Raw downloads (~2.5 GB) live outside the OneDrive-synced project folder.
# Override with the LONDON_VARIETY_RAW environment variable.
RAW = Path(os.environ.get("LONDON_VARIETY_RAW", Path.home() / "research-data" / "london-variety" / "raw"))
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "outputs"
FIG = OUT / "figures"
for p in (RAW, CLEAN, OUT, FIG):
    p.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (research data pull)"}

# 33 London boroughs (incl. City of London), 2023 GSS codes
LONDON = {
    "E09000001": "City of London", "E09000002": "Barking and Dagenham", "E09000003": "Barnet",
    "E09000004": "Bexley", "E09000005": "Brent", "E09000006": "Bromley", "E09000007": "Camden",
    "E09000008": "Croydon", "E09000009": "Ealing", "E09000010": "Enfield", "E09000011": "Greenwich",
    "E09000012": "Hackney", "E09000013": "Hammersmith and Fulham", "E09000014": "Haringey",
    "E09000015": "Harrow", "E09000016": "Havering", "E09000017": "Hillingdon", "E09000018": "Hounslow",
    "E09000019": "Islington", "E09000020": "Kensington and Chelsea", "E09000021": "Kingston upon Thames",
    "E09000022": "Lambeth", "E09000023": "Lewisham", "E09000024": "Merton", "E09000025": "Newham",
    "E09000026": "Redbridge", "E09000027": "Richmond upon Thames", "E09000028": "Southwark",
    "E09000029": "Sutton", "E09000030": "Tower Hamlets", "E09000031": "Waltham Forest",
    "E09000032": "Wandsworth", "E09000033": "Westminster",
}

# Inner London, ONS statistical (ITL/NUTS) definition: includes Haringey and Newham, excludes Greenwich.
INNER_ONS = {
    "E09000001", "E09000007", "E09000012", "E09000013", "E09000014", "E09000019", "E09000020",
    "E09000022", "E09000023", "E09000025", "E09000028", "E09000030", "E09000032", "E09000033",
}
# Inner London as coded in the Centre for Cities lookup (2024_Inner_London_lookup.xlsx):
# includes Greenwich and Newham, excludes Haringey.
INNER_CFC = (INNER_ONS - {"E09000014"}) | {"E09000011"}

# City of London is excluded from the analysis panel: resident population under 10,000 makes
# per-resident measures extreme, and PIPR publishes no rents for it. It is still a London
# counterpart in the migration flows.
CITY = "E09000001"
ANALYSIS = {k: v for k, v in LONDON.items() if k != CITY}

REGION_CODES = {"E12000007": "London", "E12000008": "South East", "E12000006": "East of England"}


def london_frame() -> pd.DataFrame:
    """One row per analysis borough (32, City of London excluded) with both Inner/Outer definitions."""
    df = pd.DataFrame({"la_code": list(ANALYSIS), "la_name": list(ANALYSIS.values())})
    df["inner_ons"] = df.la_code.isin(INNER_ONS)
    df["inner_cfc"] = df.la_code.isin(INNER_CFC)
    df["london_zone"] = df.inner_ons.map({True: "Inner London", False: "Outer London"})
    return df


def la_region_lookup() -> pd.DataFrame:
    """ONS 2023-boundary LA to region lookup shipped with the internal migration release."""
    f = RAW / "ons_internal_migration" / "lasregionew2023lookup.xlsx"
    df = pd.read_excel(f, header=None)
    # find header row
    hdr = df.index[df.apply(lambda r: r.astype(str).str.contains("LA code", case=False).any(), axis=1)][0]
    df.columns = df.iloc[hdr].astype(str).str.strip()
    df = df.iloc[hdr + 1:].dropna(how="all")
    cols = {c: c for c in df.columns}
    code = next(c for c in cols if "LA code" in c)
    name = next(c for c in cols if "LA name" in c)
    reg = next(c for c in cols if "Region name" in c)
    df = df[[code, name, reg]].set_axis(["la_code", "la_name", "region"], axis=1).reset_index(drop=True)
    df["region"] = df.region.replace({"East": "East of England"})  # match PIPR naming
    return df


def download(url: str, dest: Path, timeout: int = 600) -> Path:
    """Download url to dest unless dest already exists and is non-empty."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, headers=UA, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    tmp.replace(dest)
    return dest
