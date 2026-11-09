"""R6. Placebos (plan Section 4.7): ages 50 and over; pseudo shock 2015-17 with recovery 2017-19 (trend 2011-15).
The headline minus the pseudo coefficient is reported with a CR1 interval from the joint cluster-robust covariance
of the two IV estimates on the same MSOAs.

Output: extension/recovery/data/r6_placebos.csv and .md
"""
import numpy as np
import pandas as pd
from scipy import stats

from rc_common import DATA
from rc_core import md, prep, run, table
from r4_estimation import CTRL, ctrl

MS = dict(fe="lad23cd", cluster="lad23cd")


def main():
    m = pd.read_csv(DATA / "r2_msoa.csv")
    pseudo_ctrl = ["ptrend_a2534"] + CTRL
    # common sample for the difference
    keep = set(prep(m, "recovery_a2534", "shock_a2534", "Z_c", ctrl("a2534"), **MS)["frame"].msoa21cd) & \
        set(prep(m, "precovery_a2534", "pshock_a2534", "Z_c", pseudo_ctrl, **MS)["frame"].msoa21cd)
    c = m[m.msoa21cd.isin(keep)]
    h = run(c, "recovery_a2534", "shock_a2534", "Z_c", ctrl("a2534"), "Headline (common sample)", **MS)
    rows = [
        run(m, "recovery_a50p", "shock_a50p", "Z_c", ctrl("a50p"), "PLACEBO: ages 50+, 2019-21 shock, 2021-24 recovery", **MS),
        run(m, "precovery_a2534", "pshock_a2534", "Z_c", pseudo_ctrl,
            "PLACEBO: 25-34 pseudo shock 2015-17, recovery 2017-19 (trend 2011-15)", **MS),
        run(m, "precovery_a2534", "pshock_a2534", "Z_c", pseudo_ctrl, "Pseudo, OLS", ols=True, **MS),
        run(m, "recovery_a50p", "shock_a50p", "Z_c", ctrl("a50p"), "Ages 50+, OLS", ols=True, **MS),
    ]
    p = run(c, "precovery_a2534", "pshock_a2534", "Z_c", pseudo_ctrl, "pseudo (common sample)", **MS)
    (cl1, f1), (cl2, f2) = h["influence"], p["influence"]
    assert (cl1 == cl2).all()
    g, inv = np.unique(cl1, return_inverse=True)
    s = np.bincount(inv, weights=f1 - f2, minlength=len(g))
    G, n, k = len(g), h["n"], 3 + len(CTRL) + 1
    se = np.sqrt(G / (G - 1) * (n - 1) / (n - k) * (s ** 2).sum())
    diff = h["beta"] - p["beta"]
    crit = stats.t.ppf(0.975, G - 1)
    dtxt = (f"Headline minus pseudo coefficient (common sample of {n} MSOAs, {G} LAs): {diff:.3f} "
            f"(95% CI {diff - crit * se:.3f} to {diff + crit * se:.3f}; p {2 * stats.t.sf(abs(diff / se), G - 1):.3f}). "
            f"Headline on the common sample {h['beta']:.3f}; pseudo {p['beta']:.3f}.")
    t = table(rows)
    t.to_csv(DATA / "r6_placebos.csv", index=False)
    (DATA / "r6_placebos.md").write_text(md(t, "Step 6: placebos (MSOA, LA fixed effects)") + "\n" + dtxt + "\n",
                                         encoding="utf-8")
    pd.set_option("display.width", 260)
    print(t[["label", "beta", "ci_lo", "ci_hi", "fs_coef", "fs_F", "ar_set", "ar_p_m1_wcb", "ar_p_0_wcb",
             "classification", "n"]].round(3).to_string(index=False))
    print(dtxt)


if __name__ == "__main__":
    main()
