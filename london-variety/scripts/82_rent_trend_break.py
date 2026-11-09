"""Rent trend break: deviations from a pre-2020 linear amenity-by-time trend.

    y_bt = a_b + l_t + delta * D_b * tau_t + sum_{k >= 2020Q1} theta_k * 1[t = k] * D_b + e_bt

tau_t = quarters since 2019Q4 (2019Q4 = 0). Every post-2020 quarter has its own D_b interaction, so
delta is identified only from the pre-2020 quarters (2015Q1-2019Q4). theta_k is the post-2020 deviation
from the extrapolated pre-trend, delta * tau_k, in the baseline specification (no controls).
Inference: CR1 clustered by borough and WCR bootstrap p-values, as in 80_event_study.py.
Return measure: average deviation over 2022Q1 to the latest quarter, and over mid-2023 (2023Q3) onwards,
each tested as a linear contrast with the same bootstrap.
"""
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from config import CLEAN, OUT
from es_core import fit_cluster, rademacher
from plot_events import event_key, mark_events, shade_provisional

ES = OUT / "event_study"
B, SEED = 9999, 20261028
C1, C2, INK, INK2, GRID, PRE = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#efeeea"
BASE, FIRST_POST = "2019Q4", "2020Q1"
RETURN_WINDOWS = {"avg_2022Q1_latest": "2022Q1", "avg_2023Q3_latest": "2023Q3"}


def main():
    df = pd.read_csv(CLEAN / "event_study_rents_quarterly.csv")
    periods = sorted(df.period.unique())
    pidx = {p: i for i, p in enumerate(periods)}
    df["tau"] = df.period.map(pidx) - pidx[BASE]
    post = [p for p in periods if p >= FIRST_POST]

    unit = pd.get_dummies(df.la_code, dtype=float)
    per = pd.get_dummies(df.period, dtype=float)
    tfe = per[[p for p in periods if p != BASE]]
    dev = per[post].values * df.D_cont.values[:, None]
    X = np.hstack([unit.values, tfe.values, (df.D_cont * df.tau).values[:, None], dev])
    names = ([f"fe_{c}" for c in unit.columns] + [f"t_{p}" for p in tfe.columns] + ["trend"]
             + [f"D_cont:{p}" for p in post])
    tested = ["trend"] + [f"D_cont:{p}" for p in post]
    w = rademacher(B, 32, SEED)
    con = {}
    for lab, start in RETURN_WINDOWS.items():
        win = [q for q in post if q >= start]
        con[lab] = {f"D_cont:{q}": 1 / len(win) for q in win}
    tab, V = fit_cluster(X, df.y.values, names, tested, cl_se=df.la_code.values, w=w, k_nested=unit.shape[1],
                         contrasts=con)
    tab = tab.drop(columns="t_bootcluster")
    windows = [f"{RETURN_WINDOWS[k]}-{post[-1]} ({len(con[k])} quarters)" for k in RETURN_WINDOWS]
    tab.insert(0, "period", ["(slope per quarter)"] + post + windows)
    tab.insert(0, "term", ["pre-2020 linear trend"] + ["deviation from extrapolated trend"] * len(post)
               + ["average deviation"] * len(RETURN_WINDOWS))
    tab["n_obs"], tab["n_clusters"], tab["k"] = tab.attrs["n_obs"], tab.attrs["n_clusters"], tab.attrs["k"]
    tab.to_csv(ES / "rent_trend_break.csv", index=False)
    d = tab.iloc[0]
    avg = tab[tab.term == "average deviation"]
    avg.to_csv(ES / "rent_return_summary.csv", index=False)
    print(f"pre-trend slope {d.coef:.3f} per quarter (se {d.se_cluster:.3f}, WCB p {d.p_wcb:.4f})")
    print(tab.iloc[1:][["period", "coef", "se_cluster", "p_cluster", "p_wcb", "ci_low", "ci_high"]].round(3)
          .to_string(index=False))
    dev_tab = tab[tab.term == "deviation from extrapolated trend"]

    # plot: baseline event study with extrapolated trend, and deviations
    es = pd.read_csv(ES / "regression_table.csv", dtype={"period": str})
    es = es[(es.outcome == "rents") & (es.treatment == "continuous") & (es.spec == "baseline")]
    es = pd.concat([es, pd.DataFrame([{"period": BASE, "coef": 0, "ci_low": 0, "ci_high": 0, "p_wcb": 1}])])
    es["x"] = es.period.map(pidx)
    tau = np.arange(len(periods)) - pidx[BASE]
    crit = stats.t.ppf(0.975, 31)
    # Borough FE absorb the trend's intercept, so the fitted line is delta * tau + c, not anchored at
    # 2019Q4. Recover c on the event-study scale (relative to 2019Q4) from the post periods, where
    # beta_k - theta_k = delta * tau_k + c holds exactly in this balanced panel without controls.
    post_es = es.set_index("period").coef.reindex(post).values
    c_k = post_es - dev_tab.coef.values - d.coef * (np.array([pidx[p] for p in post]) - pidx[BASE])
    assert np.ptp(c_k) < 1e-6, f"intercept not constant across post periods: {np.ptp(c_k)}"
    c0 = c_k.mean()
    print(f"trend intercept on event-study scale: {c0:.3f}")
    line, band = d.coef * tau + c0, crit * d.se_cluster * np.abs(tau - tau.mean())

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 5.6), sharey=True)
    for ax in (a1, a2):
        ax.axvspan(-0.5, pidx[FIRST_POST] - 0.5, color=PRE, lw=0, zorder=0)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.axvline(pidx[FIRST_POST] - 0.5, color=INK2, lw=0.8, ls="--")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.spines[["top", "right"]].set_visible(False)
        ticks = [i for i, p in enumerate(periods) if p.endswith("Q1")]
        ax.set_xticks(ticks)
        ax.set_xticklabels([periods[i][:4] for i in ticks])
    a1.fill_between(np.arange(len(periods)), line - band, line + band, color=C2, alpha=0.15, lw=0)
    a1.plot(np.arange(len(periods)), line, color=C2, lw=2,
            label=f"Pre-2020 linear trend, extrapolated ({d.coef:.2f} per quarter)")
    sig = es.p_wcb < 0.05
    a1.vlines(es.x, es.ci_low, es.ci_high, color=C1, lw=1.2)
    a1.scatter(es.x[sig], es.coef[sig], color=C1, s=18, zorder=3, label="Event-study coefficient (WCB p<0.05)")
    a1.scatter(es.x[~sig], es.coef[~sig], facecolor="#fcfcfb", edgecolor=C1, s=18, zorder=3,
               label="Event-study coefficient (WCB p>=0.05)")
    a1.set_title("Baseline rent event study and extrapolated pre-2020 trend", loc="left", fontsize=9, color=INK, pad=14)
    a1.set_ylabel("100 x log rent index, per SD of log amenity density")
    a1.legend(fontsize=7.5, frameon=False, loc="lower left")

    t = dev_tab.copy()
    t["x"] = t.period.map(pidx)
    sig = t.p_wcb < 0.05
    a2.vlines(t.x, t.ci_low, t.ci_high, color=C1, lw=1.2)
    a2.scatter(t.x[sig], t.coef[sig], color=C1, s=18, zorder=3, label="WCB p<0.05")
    a2.scatter(t.x[~sig], t.coef[~sig], facecolor="#fcfcfb", edgecolor=C1, s=18, zorder=3, label="WCB p>=0.05")
    for (lab, start), r, ls in zip(RETURN_WINDOWS.items(), avg.itertuples(), ("--", "-.")):
        a2.hlines(r.coef, pidx[start] - 0.5, len(periods) - 0.5, color=C2, lw=1.8, ls=ls, zorder=2,
                  label=f"Average {start}-{post[-1]}: {r.coef:.2f} (WCB p = {r.p_wcb:.3f})")
    a2.set_title("Post-2020 deviation from extrapolated trend", loc="left", fontsize=9, color=INK, pad=14)
    a2.legend(fontsize=7.5, frameon=False, loc="lower left")
    for ax in (a1, a2):
        mark_events(ax, periods)
        shade_provisional(ax, periods)
    note = ("Trend fitted on 2015Q1-2019Q4 only: borough and quarter FE, one D x quarters-since-2019Q4 term, "
            "separate D x quarter terms from 2020Q1. Borough FE absorb the trend's level, so the line is the "
            "least-squares fit to all pre-2020 coefficients and need not pass through 0 at 2019Q4; deviations "
            "(right) are measured from it. Bars: 95% CI, borough-clustered CR1, t(31). Shaded band: slope "
            "uncertainty only. N=1,504, 32 clusters, WCR bootstrap B=9,999. Orange lines (right): average deviation "
            "from 2022Q1 and from 2023Q3 to the latest quarter. Hatched: 2026, provisional (PIPR revises recent "
            "months). " + event_key())
    fig.text(0.01, 0.01, "\n".join(textwrap.wrap(note, 200)), fontsize=7, color=INK2, va="bottom")
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(ES / "rent_trend_break.png", dpi=150)


if __name__ == "__main__":
    main()
