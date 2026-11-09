"""R4. Headline and Step 4 estimates (plan Sections 2 and 4.1-4.5).

Output: extension/recovery/data/r4_estimation.csv and .md
"""
import pandas as pd

from rc_common import DATA
from rc_core import md, run, table

CTRL = ["telework_share", "garden_share", "student_share"]


def ctrl(g):
    return [f"trend_{g}"] + CTRL


def main():
    m = pd.read_csv(DATA / "r2_msoa.csv")
    a = pd.read_csv(DATA / "r2_la.csv")
    MS = dict(fe="lad23cd", cluster="lad23cd")
    LA = dict(fe=None, cluster="la_code", region_fe="region")
    rows = [run(m, "recovery_a2534", "shock_a2534", "Z_c", ctrl("a2534"), "HEADLINE: MSOA 25-34, IV measure (c)", **MS)]
    r = rows[0]
    print(f"headline beta {r['beta']:.3f} [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}], F {r['fs_F']:.1f}, AR {r['ar_set']}, "
          f"{r['classification']}", flush=True)
    rows += [
        run(m, "recovery_a2534", "shock_a2534", "Z_c", ctrl("a2534"), "MSOA 25-34, OLS", ols=True, **MS),
        run(m, "recovery_a2534", "shock_a2534", "Z_vdl", ctrl("a2534"), "MSOA 25-34, IV VDL", **MS),
        run(m, "recovery_a2029", "shock_a2029", "Z_c", ctrl("a2029"), "MSOA 20-29, IV measure (c)", **MS),
        run(m, "recovery_a2029", "shock_a2029", "Z_c", ctrl("a2029"), "MSOA 20-29, OLS", ols=True, **MS),
        run(m, "recovery_a2029", "shock_a2029", "Z_vdl", ctrl("a2029"), "MSOA 20-29, IV VDL", **MS),
    ]
    for g, lab in [("a2534", "25-34"), ("a2029", "20-29")]:
        rows += [
            run(a, f"recovery_{g}", f"shock_{g}", "Z_c", ctrl(g), f"LA {lab}, IV measure (c), to 2025", **LA),
            run(a, f"recovery_{g}", f"shock_{g}", "Z_c", ctrl(g), f"LA {lab}, OLS, to 2025", ols=True, **LA),
            run(a, f"recovery_{g}", f"shock_{g}", "Z_vdl", ctrl(g), f"LA {lab}, IV VDL, to 2025", **LA),
            run(a, f"recovery24_{g}", f"shock_{g}", "Z_c", ctrl(g), f"LA {lab}, IV measure (c), to 2024", **LA),
            run(a, f"recovery24_{g}", f"shock_{g}", "Z_c", ctrl(g), f"LA {lab}, OLS, to 2024", ols=True, **LA),
        ]
    t = table(rows)
    t.to_csv(DATA / "r4_estimation.csv", index=False)
    (DATA / "r4_estimation.md").write_text(md(t, "Step 4: recovery coefficients (Davis-Weinstein beta)"), encoding="utf-8")
    pd.set_option("display.width", 260)
    print(t[["label", "beta", "ci_lo", "ci_hi", "fs_coef", "fs_F", "ar_set", "ar_p_m1_wcb", "ar_p_0_wcb",
             "classification", "n", "G"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
