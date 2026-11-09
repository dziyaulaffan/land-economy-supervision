"""V8. Robustness of the headline (plan Section 4.6): Welsh MSOAs added (Welsh closure dates), 1 km and 3 km decay,
London excluded. Same specification as the headline otherwise.

Output: extension/venue_mix/data/v8_robustness.csv and .md
"""
import pandas as pd

from vm_common import DATA
from vm_core import CONTROLS, RESULT_COLS, est, msoa_frame
from v5_main import write_md


def ctrl_for(lk):
    return [f"log_total_access_fhrs_{lk}" if c == "log_total_access" else c for c in CONTROLS]


def main():
    e = msoa_frame(("E",))
    ew = msoa_frame(("E", "W"))
    rows = [
        est(e, "dy_2534", "T_main_fhrs_l15", CONTROLS, "Headline (England, 1.5 km)"),
        est(ew, "dy_2534", "T_main_fhrs_l15", CONTROLS, "England and Wales (Welsh closure dates)"),
        est(e, "dy_2534", "T_main_fhrs_l10", ctrl_for("l10"), "1 km decay"),
        est(e, "dy_2534", "T_main_fhrs_l30", ctrl_for("l30"), "3 km decay"),
        est(e[e.region != "London"], "dy_2534", "T_main_fhrs_l15", CONTROLS, "England excluding London"),
    ]
    r = pd.DataFrame(rows)[RESULT_COLS]
    r.to_csv(DATA / "v8_robustness.csv", index=False)
    write_md(r, DATA / "v8_robustness.md", "Step 8 robustness of the headline (25-34, 2011-2021; per 10 variety-days lost)")
    pd.set_option("display.width", 250)
    print(r[RESULT_COLS[:12] + ["n_obs", "n_clusters"]].round(3).to_string(index=False))
    print("Welsh MSOAs in the E&W sample:", int((ew.dropna(subset=["dy_2534"]).nation == "W").sum()))


if __name__ == "__main__":
    main()
