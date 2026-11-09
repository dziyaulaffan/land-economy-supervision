"""Run the national extension end to end, or selected steps.

    python run_all.py                      # every step in order (downloads are skipped when files exist)
    python run_all.py --only s2_national_ddd.py s5_national_rents.py
    python run_all.py --start s1_download.py

Order: data assembly (B1-B5, S1, S3/S4 data), then the feasibility correlations (B6), then the pre-registered
estimation steps (S2-S5; see PRE_ANALYSIS_PLAN.md). Library modules (ext_config, e_core, b4_common, venue_mix vm_common and vm_core, recovery rc_common and rc_core) are not steps.
The venue-mix steps (venue_mix/scripts/v*.py) and recovery steps (recovery/scripts/r*.py) come last.
"""
import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent / "scripts"
STEPS = [
    # B1 point-level amenities
    "b1_fhrs_download.py", "b1_nspl_extract.py", "b1_geography.py", "b1_ukbc_download.py", "b1_fhrs_clean.py",
    "b1_osm_ohsome.py", "b1_assign_access.py", "b1_validate.py",
    # B2 Census 2021 migration
    "b2_download_census_migration.py", "b2_lookup_msoa_lad23.py", "b2_build_census_migration.py",
    "b2_validate_census_migration.py",
    # B3 national LA panel, B5 mobility closure intensity
    "b3_migration.py", "b3_rents.py", "b3_mobility.py", "b3_crosssection.py", "b3_quarter_panel.py",
    "b3_validate_london.py", "b5_closure_intensity.py",
    # B4 restriction history
    "b4_01_fetch_legislation.py", "b4_02_fetch_compiled.py", "b4_03_parse_legislation.py", "b4_04_build_panel.py",
    "b4_05_validate.py",
    # S1 national controls
    "s1_download.py", "s1_controls_la.py", "s1_controls_msoa.py", "s1_correlations.py",
    # S3 and S4 data
    "s3_download_cases.py", "s3_build_case_rates.py", "s4_download_census.py", "s4_download_lookups.py",
    "s4_build_census_inflows.py",
    # B6 feasibility correlations
    "b6_feasibility.py",
    # pre-registered estimation
    "s2_national_ddd.py", "s2b_student_check.py", "s3_tier_design.py", "s4_census_msoa.py", "s5_national_rents.py",
    # departure 8 (decided after the registered results)
    "s8_urban_measures.py", "s8_pound_values.py", "s8b_density_check.py", "s8c_corrected_ab.py", "s8d_pretrend_check.py",
    # venue-mix extension (venue_mix/, own plan venue_mix/PRE_ANALYSIS_PLAN.md): closure calendar, treatment,
    # diagnostics (before outcomes), then registered estimation
    "../venue_mix/scripts/v1_fetch_regs.py", "../venue_mix/scripts/v1_closure_calendar.py",
    "../venue_mix/scripts/v2_treatment.py", "../venue_mix/scripts/v3_diagnostics.py",
    "../venue_mix/scripts/v5_main.py", "../venue_mix/scripts/v6_placebo_age.py",
    "../venue_mix/scripts/v7_la_panel.py", "../venue_mix/scripts/v8_robustness.py",
    # recovery extension (recovery/, own plan recovery/PRE_ANALYSIS_PLAN.md): stocks, descriptives, then estimation
    "../recovery/scripts/r1_population.py", "../recovery/scripts/r2_shock_exposure.py",
    "../recovery/scripts/r4_estimation.py", "../recovery/scripts/r5_heterogeneity.py",
    "../recovery/scripts/r6_placebos.py",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", metavar="STEP")
    ap.add_argument("--start", metavar="STEP")
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
        f = (SCRIPTS / s).resolve()
        subprocess.run([sys.executable, f.name], cwd=f.parent, check=True)


if __name__ == "__main__":
    main()
