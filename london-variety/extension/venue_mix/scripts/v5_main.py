"""V5. Main estimation (plan Sections 2 and 4.1): headline, other ages, controls one at a time, student decile, OSM.

Output: extension/venue_mix/data/v5_main.csv and v5_main.md
"""
import pandas as pd

from vm_common import DATA
from vm_core import CONTROLS, RESULT_COLS, est, msoa_frame

TREAT = "T_main_fhrs_l15"


def main():
    d = msoa_frame(("E",))
    rows = [est(d, "dy_2534", TREAT, CONTROLS, "HEADLINE: 25-34, all controls")]
    print(pd.DataFrame(rows)[RESULT_COLS[:12]].round(3).to_string(index=False), flush=True)
    rows.append(est(d, "dy_2024", TREAT, CONTROLS, "20-24, all controls"))
    rows.append(est(d, "dy_2034", TREAT, CONTROLS, "20-34, all controls"))
    rows.append(est(d, "dy_2534", TREAT, [], "25-34, LA FE only"))
    for c in CONTROLS:
        rows.append(est(d, "dy_2534", TREAT, [c], f"25-34, LA FE + {c} only"))
    q = d.dropna(subset=["dy_2534"])
    cut = q.student_share.quantile(0.9)
    rows.append(est(d[d.student_share <= cut], "dy_2534", TREAT, CONTROLS,
                    f"25-34, all controls, top student-share decile dropped (> {cut:.3f})"))
    osm_ctrl = ["log_total_access_osm_l15" if c == "log_total_access" else c for c in CONTROLS]
    rows.append(est(d, "dy_2534", "T_main_osm_l15", osm_ctrl, "25-34, all controls, OSM treatment"))
    r = pd.DataFrame(rows)[RESULT_COLS]
    r.to_csv(DATA / "v5_main.csv", index=False)
    write_md(r, DATA / "v5_main.md", "Step 5 main estimation (England MSOAs; coefficient per 10 variety-days lost)")
    pd.set_option("display.width", 250)
    print(r[RESULT_COLS[:12] + ["n_obs", "n_clusters"]].round(3).to_string(index=False))


def write_md(r, path, title):
    L = [f"# {title}", "", "| Specification | Coef per 10 days | 95% CI | p (CR1) | p (WCB) | Per SD | Treatment SD (days) | Outcome mean | MSOAs | LAs |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for _, x in r.iterrows():
        L.append(f"| {x.label} | {x.coef:.2f} | [{x.ci_lo:.2f}, {x.ci_hi:.2f}] | {x.p_cr1:.3f} | {x.p_wcb:.3f} | "
                 f"{x.coef_per_sd:.2f} | {x.treat_sd_days:.1f} | {x.y_mean:.1f} | {int(x.n_obs)} | {int(x.n_clusters)} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
