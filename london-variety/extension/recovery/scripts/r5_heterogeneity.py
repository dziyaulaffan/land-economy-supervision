"""R5. Heterogeneity of the headline recovery coefficient (plan Section 4.6): terciles of log population density,
terciles of measure (c), London against the rest of England and Wales. Headline IV specification with LA fixed
effects within each subsample. Terciles are cut over the headline sample.

Output: extension/recovery/data/r5_heterogeneity.csv and .md
"""
import pandas as pd

from rc_common import DATA
from rc_core import md, prep, run, table
from r4_estimation import ctrl

MS = dict(fe="lad23cd", cluster="lad23cd")
ARGS = ("recovery_a2534", "shock_a2534", "Z_c", ctrl("a2534"))


def main():
    m = pd.read_csv(DATA / "r2_msoa.csv")
    base = prep(m, *ARGS, **MS)["frame"]                     # headline sample (singleton LAs dropped)
    h = m[m.msoa21cd.isin(base.msoa21cd)].copy()
    h["dens_t"] = pd.qcut(h.log_pop_density, 3, labels=["low", "middle", "high"])
    h["acc_t"] = pd.qcut(h.Z_c, 3, labels=["low", "middle", "high"])
    rows = []
    for col, name in [("dens_t", "population density"), ("acc_t", "measure (c) access")]:
        for t in ["low", "middle", "high"]:
            rows.append(run(h[h[col] == t], *ARGS, f"{name} tercile: {t}", **MS))
            print(name, t, round(rows[-1]["beta"], 3), round(rows[-1]["fs_F"], 1), rows[-1]["classification"], flush=True)
    rows.append(run(h[h.london], *ARGS, "London", **MS))
    rows.append(run(h[~h.london], *ARGS, "Rest of England and Wales", **MS))
    t = table(rows)
    cuts = (f"Density tercile cuts (residents per km2): {h.groupby('dens_t', observed=True).log_pop_density.max().map(lambda v: f'{2.718281828**v:,.0f}').to_dict()}; "
            f"measure (c) tercile cuts: {h.groupby('acc_t', observed=True).Z_c.max().round(2).to_dict()}.")
    t.to_csv(DATA / "r5_heterogeneity.csv", index=False)
    (DATA / "r5_heterogeneity.md").write_text(md(t, "Step 5: heterogeneity of the recovery coefficient (MSOA, 25-34, IV measure (c))")
                                              + "\n" + cuts + "\n", encoding="utf-8")
    pd.set_option("display.width", 260)
    print(t[["label", "beta", "ci_lo", "ci_hi", "fs_F", "ar_set", "ar_p_m1_wcb", "ar_p_0_wcb", "classification", "n", "G"]]
          .round(3).to_string(index=False))
    print(cuts)


if __name__ == "__main__":
    main()
