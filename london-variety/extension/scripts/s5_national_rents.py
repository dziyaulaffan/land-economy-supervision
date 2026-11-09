"""Step 5: national rents (pre-analysis plan, Design 4).

y_bq = 100 x log of the quarterly mean PIPR index, 2015Q1 to the latest complete quarter, 316 LADs.
Event study:  y = LA FE + (quarter or region x quarter) FE + sum_{k != 2019Q4} theta_k D 1[q=k] + controls x quarter.
Trend break (as 82_rent_trend_break.py): delta D tau_q + sum_{k >= 2020Q1} theta_k D 1[q=k], tau = quarters since
2019Q4, with the same FE and controls; theta_k is the deviation from the extrapolated pre-2020 amenity trend.
Headline: average trend-break deviation 2020Q2-2021Q2, region x quarter FE, six controls x quarter.
CR1 and WCR bootstrap clustered by LA (B = 9,999).
"""
import numpy as np
import pandas as pd

from e_core import B, SEED, fit_cluster, rademacher
from ext_config import CLEAN

DROP = {"E09000001", "E06000053"}
CTRL = ["X_telework_share", "X_garden_share", "X_flat_share", "X_private_rent_share", "X_age20_39_share",
        "X_student_share"]
BASE = "2019Q4"
SPECS = {"(i) LA + quarter FE": ((), False), "(ii) region x quarter FE": ((), True),
         "(iii) region x quarter FE + controls": (tuple(CTRL), True)}


def fit(df, model, controls, region_q, w):
    periods = sorted(df.quarter.unique())
    df = df.sort_values(["la_code", "quarter"]).reset_index(drop=True)
    q = df.quarter.values
    unit = pd.get_dummies(df.la_code, dtype=float)
    blocks, names = [unit.values], [f"fe_{c}" for c in unit.columns]
    if region_q:
        rq = pd.get_dummies(df.region + "_" + df.quarter, dtype=float)
        rq = rq.drop(columns=[c for c in rq.columns if c.endswith(f"_{BASE}")])
        blocks.append(rq.values); names += [f"rq_{c}" for c in rq.columns]
    else:
        tq = [p for p in periods if p != BASE]
        blocks.append(np.column_stack([(q == p).astype(float) for p in tq])); names += [f"q_{p}" for p in tq]
    if model == "event":
        ks = [p for p in periods if p != BASE]
    else:
        idx = {p: i for i, p in enumerate(periods)}
        tau = np.array([idx[p] - idx[BASE] for p in q], dtype=float)
        blocks.append((df.D.values * tau)[:, None]); names.append("D:trend")
        ks = [p for p in periods if p >= "2020Q1"]
    blocks.append(np.column_stack([(q == p) * df.D.values for p in ks])); names += [f"D:{p}" for p in ks]
    other = [p for p in periods if p != BASE]
    for c in controls:
        blocks.append(np.column_stack([(q == p) * df[c].values for p in other])); names += [f"{c}:{p}" for p in other]
    avg = lambda lo, hi: {f"D:{p}": 1.0 for p in ks if lo <= p <= hi}
    con = {}
    for lab, (lo, hi) in {"closure_avg_2020Q2_2021Q2": ("2020Q2", "2021Q2"),
                          "avg_2023Q3_latest": ("2023Q3", periods[-1])}.items():
        c = avg(lo, hi)
        con[lab] = {k: v / len(c) for k, v in c.items()}
    tested = (["D:trend"] if model == "trend" else []) + [f"D:{p}" for p in ks if p >= "2019Q1"]
    tab, _ = fit_cluster(np.hstack(blocks), df.y.values, names, tested, cl_se=df.la_code.values, w=w,
                         k_nested=unit.shape[1], contrasts=con)
    tab["term"] = tab.name.str.replace("D:", "", regex=False)
    return tab.assign(n_obs=len(df), n_clusters=df.la_code.nunique())


def main():
    r = pd.read_csv(CLEAN / "b3_la_quarter_panel.csv")
    r = r[~r.la_code.isin(DROP) & r.rent_y.notna() & (r.rent_n_months == 3)]
    last = r.groupby("quarter").la_code.nunique()
    r = r[r.quarter.isin(last[last >= 300].index)]
    c = pd.read_csv(CLEAN / "b3_la_crosssection.csv")[["la_code", "z_log_per1k_IR"]].rename(columns={"z_log_per1k_IR": "D"})
    s = pd.read_csv(CLEAN / "s1_controls_la2023.csv")[["la_code"] + CTRL]
    df = r[["la_code", "region", "quarter", "rent_y"]].rename(columns={"rent_y": "y"}).merge(c, on="la_code").merge(
        s, on="la_code")
    print("LAs", df.la_code.nunique(), "quarters", df.quarter.min(), df.quarter.max())
    w = rademacher(B, df.la_code.nunique(), SEED)
    out, L = [], []
    for model in ("event", "trend"):
        for spec, (ctrl, rq) in SPECS.items():
            t = fit(df, model, ctrl, rq, w)
            out.append(t.assign(model=model, spec=spec))
            g = t.set_index("term")
            L.append(f"| {model} | {spec} | " + " | ".join(
                f"{g.loc[k, 'coef']:.2f} ({g.loc[k, 'p_wcb']:.3f})" for k in
                ["2020Q2", "2021Q2", "closure_avg_2020Q2_2021Q2", "avg_2023Q3_latest"])
                + (f" | {g.loc['trend', 'coef']:.3f} ({g.loc['trend', 'p_wcb']:.3f})" if model == "trend" else " | ")
                + f" | {int(t.n_clusters.iloc[0])} |")
            print(L[-1], flush=True)
    res = pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore")
    res.to_csv(CLEAN / "s5_national_rents.csv", index=False)
    hdr = ["| Model | Spec | 2020Q2 | 2021Q2 | Closure avg 2020Q2-2021Q2 | Avg 2023Q3-latest | Pre-trend per quarter | LAs |",
           "|---|---|---|---|---|---|---|---|"]
    (CLEAN / "s5_national_rents.md").write_text("\n".join(hdr + L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
