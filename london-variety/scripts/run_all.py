"""Run every step in order. Downloads are skipped when the raw file already exists.

Usage:
    python run_all.py                       # all steps; HonestDiD skipped if its inputs are unchanged
    python run_all.py --force-honestdid     # rerun HonestDiD even if cached
    python run_all.py --only 76_msoa_distance.py 87_msoa_house_prices.py
    python run_all.py --from 80_event_study.py

HonestDiD (83_honestdid.R, ~50 minutes) is cached: its inputs are hashed (the R script, the baseline
continuous event-study coefficients from regression_table.csv and the two covariance files, numbers
rounded to 10 decimals) and stored in outputs/event_study/honestdid_cache.json after a successful run.
"""
import argparse
import hashlib
import json
import os
import runpy
import shutil
import subprocess
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
ROOT = HERE.parent
ES = ROOT / "outputs" / "event_study"
STEPS = ["10_migration.py", "20_rents.py", "30_house_prices.py", "40_amenity_density.py", "50_mobility.py",
         "60_charts.py", "70_controls.py", "75_msoa_amenity.py", "76_msoa_distance.py", "77_msoa_access.py", "80_event_study.py",
         "82_rent_trend_break.py", "83_honestdid.R", "85_contdid.R", "87_msoa_house_prices.py", "88_price_to_rent.py",
         "89_pound_values.py", "92_msoa_access_event_study.py",
         "94_migration_age.py", "95_reversal.py", "96_age_ddd.py", "97_preperiod_check.py", "98_rent_tests.py", "98_within_london.py", "98_students_25_29.py", "98_robustness_final.py", "98_international.py", "99_report.py",
         "90_event_study_plots.py"]
# arguments for R steps, relative to the project root
R_ARGS = {"83_honestdid.R": ["outputs/event_study"],
          "85_contdid.R": ["data/clean", "outputs/event_study"]}
HONEST_CACHE = ES / "honestdid_cache.json"
HONEST_OUTPUT = ES / "honestdid_breakdown.csv"


def rscript() -> str:
    """Rscript from RSCRIPT, PATH, or the default per-user Windows install."""
    cand = os.environ.get("RSCRIPT") or shutil.which("Rscript")
    if cand:
        return cand
    found = sorted((Path.home() / "AppData/Local/Programs/R").glob("R-*/bin/Rscript.exe"))
    if not found:
        raise FileNotFoundError("Rscript not found; set RSCRIPT to its path")
    return str(found[-1])


def honestdid_input_hash() -> str:
    h = hashlib.sha256((HERE / "83_honestdid.R").read_bytes())
    t = pd.read_csv(ES / "regression_table.csv", dtype={"period": str})
    t = t[(t.treatment == "continuous") & (t.spec == "baseline")].sort_values(["outcome", "period"])
    h.update(t[["outcome", "period", "coef"]].round(10).to_csv(index=False).encode())
    for outcome in ("migration", "rents"):
        v = pd.read_csv(ES / f"vcov_{outcome}_continuous_baseline.csv", index_col=0)
        h.update(v.round(10).to_csv().encode())
    return h.hexdigest()


def write_honestdid_cache():
    HONEST_CACHE.write_text(json.dumps({"input_sha256": honestdid_input_hash()}, indent=1))


def honestdid_is_current() -> bool:
    if not (HONEST_CACHE.exists() and HONEST_OUTPUT.exists()):
        return False
    return json.loads(HONEST_CACHE.read_text()).get("input_sha256") == honestdid_input_hash()


def run_step(s: str):
    if s.endswith(".R"):
        subprocess.run([rscript(), str(HERE / s), *[str(ROOT / a) for a in R_ARGS[s]]], check=True)
    else:
        runpy.run_path(str(HERE / s), run_name="__main__")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force-honestdid", action="store_true", help="rerun HonestDiD even if its inputs are unchanged")
    ap.add_argument("--only", nargs="+", metavar="STEP", help="run only these steps")
    ap.add_argument("--from", dest="start", metavar="STEP", help="run from this step onwards")
    a = ap.parse_args()
    steps = STEPS
    if a.only:
        unknown = set(a.only) - set(STEPS)
        assert not unknown, f"unknown steps: {unknown}"
        steps = [s for s in STEPS if s in a.only]
    elif a.start:
        steps = STEPS[STEPS.index(a.start):]
    for s in steps:
        print(f"\n=== {s}", flush=True)
        if s == "83_honestdid.R":
            if not a.force_honestdid and honestdid_is_current():
                print("HonestDiD inputs unchanged; skipping (use --force-honestdid to rerun)", flush=True)
                continue
            run_step(s)
            write_honestdid_cache()
        else:
            run_step(s)


if __name__ == "__main__":
    main()
