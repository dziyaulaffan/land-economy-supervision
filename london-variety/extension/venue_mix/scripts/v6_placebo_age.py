"""V6. Placebo and age comparison (plan Sections 3 and 4.2-4.3).

Placebo: headline specification on the 2001 to 2011 change (2001 rate excluding no usual address; version
including it alongside), ages 25-34 and 20-34.
Age 50+: headline specification on the 2011 to 2021 change for ages 50 and over.
Stacked: MSOA x age group (25-34, 50+), MSOA and age-group fixed effects, VDL/10 x young and controls x young.
With two rows per MSOA and MSOA fixed effects, this regression is estimated in its exact differenced form:
(dy_25-34 - dy_50+) on a constant (the age-group effect), VDL/10 and the controls; the LA-by-age version adds
LA fixed effects to the differenced regression. Clustered by LA, WCR bootstrap.

Output: extension/venue_mix/data/v6_placebo_age.csv and .md
"""
import pandas as pd

from vm_common import DATA
from vm_core import CONTROLS, RESULT_COLS, est, msoa_frame
from v5_main import write_md

TREAT = "T_main_fhrs_l15"


def main():
    d = msoa_frame(("E",))
    d["stack_diff"] = d.dy_2534 - d.dy_50p
    rows = [
        est(d, "pl_2534", TREAT, CONTROLS, "PLACEBO: 2001-2011 change, 25-34 (2001 excl. no usual address)"),
        est(d, "pl_incl_2534", TREAT, CONTROLS, "Placebo: 2001-2011, 25-34 (2001 incl. no usual address)"),
        est(d, "pl_2034", TREAT, CONTROLS, "Placebo: 2001-2011, 20-34 (excl. no usual address)"),
        est(d, "dy_50p", TREAT, CONTROLS, "AGE 50+: 2011-2021 change"),
        est(d, "stack_diff", TREAT, CONTROLS, "STACKED difference 25-34 minus 50+ (MSOA and age-group FE)", fe=None),
        est(d, "stack_diff", TREAT, CONTROLS, "Stacked difference with LA-by-age-group FE"),
    ]
    r = pd.DataFrame(rows)[RESULT_COLS]
    r.to_csv(DATA / "v6_placebo_age.csv", index=False)
    write_md(r, DATA / "v6_placebo_age.md", "Step 6 placebo and age comparison (England MSOAs; per 10 variety-days lost)")
    pd.set_option("display.width", 250)
    print(r[RESULT_COLS[:12] + ["y_mean", "n_obs", "n_clusters"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
