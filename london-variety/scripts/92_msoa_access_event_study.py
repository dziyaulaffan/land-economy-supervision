"""Headline MSOA house-price event study with consumption access in place of own-MSOA amenity density.

Same sample, fixed effects, controls and inference as the headline specification in 87_msoa_house_prices.py
(MSOA and borough-by-quarter FE; property type, new build, leasehold; log distance to Charing Cross,
teleworkability and garden access each x quarter; property type x quarter; 2019Q4 omitted; CR1 by MSOA;
WCR bootstrap by borough, B = 9,999). Treatments, each x quarter:
    own      standardised log own-MSOA I+R density (the round 4 headline, re-run for the lagged window)
    access   standardised log access index, decay 1.5 km (main), 1 km and 3 km (robustness)
    rings    standardised log(1 + units) in 0-1, 1-2 and 2-5 km rings, entered together
Closure-window averages: 2020Q1-2021Q4 and, for the completion lag, 2020Q2-2022Q1 (Land Registry dates are
completion dates, typically weeks to months after the price is agreed).
"""
import gc
import importlib.util
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyfixest.estimation import demean

from config import CLEAN, OUT, london_frame
from es_core import fit_cluster, rademacher
from plot_events import event_key, mark_events, shade_provisional

_spec = importlib.util.spec_from_file_location("msoa87", __file__.replace("92_msoa_access_event_study.py",
                                                                           "87_msoa_house_prices.py"))
m87 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m87)

ES = OUT / "event_study"
HEADLINE_CTRLS = {"dist": "X_log_dist_cc", "telework": "X_telework_share", "garden": "X_garden_share"}
TREATMENTS = {
    "own_density": ["D_msoa"],
    "access_l15": ["D_access_l15"],
    "access_l10": ["D_access_l10"],
    "access_l30": ["D_access_l30"],
    "rings": ["X_ring_0_1", "X_ring_1_2", "X_ring_2_5"],
}
LABELS = {"own_density": "Own-MSOA amenity density (round 4 headline)",
          "access_l15": "Access index, decay 1.5 km (main)", "access_l10": "Access index, decay 1 km",
          "access_l30": "Access index, decay 3 km", "rings": "Ring counts entered together",
          "D_msoa": "own density", "D_access_l15": "access 1.5 km", "D_access_l10": "access 1 km",
          "D_access_l30": "access 3 km", "X_ring_0_1": "0-1 km ring", "X_ring_1_2": "1-2 km ring",
          "X_ring_2_5": "2-5 km ring"}
WINDOWS = {"closure_2020Q1_2021Q4": ("2020Q1", "2021Q4"), "lagged_2020Q2_2022Q1": ("2020Q2", "2022Q1")}
B, SEED = 9999, 20261028


def analysis_sample():
    dmap = pd.read_csv(CLEAN / "land_registry_district_to_la.csv")
    districts = set(dmap[dmap.la_code.isin(london_frame().la_code)].district) | {"CITY OF LONDON"}
    s = m87.build_sales(districts)
    end = m87.latest_complete_quarter(s)
    s = s[(s.quarter <= end) & (s.ppd_category == "A") & s.property_type.isin(["D", "S", "T", "F"])
          & (s.price >= m87.MIN_PRICE) & s.msoa11.notna() & s.duration.isin(["F", "L"])]
    m = pd.read_csv(CLEAN / "msoa_amenity_controls.csv")
    dist = pd.read_csv(CLEAN / "msoa_distance_charing_cross.csv")
    acc = pd.read_csv(CLEAN / "msoa_access_2019.csv")
    acc_cols = [c for c in acc.columns if c.startswith(("D_access", "X_ring"))]
    m = m.merge(dist[["msoa11_code", "X_log_dist_cc"]], on="msoa11_code").merge(
        acc[["msoa11_code", *acc_cols]], on="msoa11_code")
    s = s.merge(m[["msoa11_code", "la_code", "D_msoa", "X_telework_share", "X_garden_share", "X_log_dist_cc",
                   *acc_cols]], left_on="msoa11", right_on="msoa11_code", how="inner")
    s["y"] = np.log(s.price)
    for t in ["S", "T", "F"]:
        s[f"type_{t}"] = (s.property_type == t).astype(float)
    s["new_build"] = (s.old_new == "Y").astype(float)
    s["leasehold"] = (s.duration == "L").astype(float)
    s["msoa_id"] = pd.factorize(s.msoa11)[0]
    s["bq_id"] = pd.factorize(s.la_code + "_" + s.quarter)[0]
    return s.reset_index(drop=True), end


def estimate(d, treat_cols, w):
    ev = [q for q in sorted(d.quarter.unique()) if q != m87.BASE]
    Q = pd.get_dummies(d.quarter, dtype=float)[ev].values
    cols = [(t, d[t].values) for t in treat_cols] + [(c, d[v].values) for c, v in HEADLINE_CTRLS.items()]
    cols += [(f"type{t}", d[f"type_{t}"].values) for t in ["S", "T", "F"]]
    static = ["type_S", "type_T", "type_F", "new_build", "leasehold"]
    k = 1 + len(cols) * len(ev) + len(static)
    Xy = np.empty((len(d), k))
    Xy[:, 0] = d.y.values
    names, j = [], 1
    for nm, v in cols:
        Xy[:, j:j + len(ev)] = Q * v[:, None]
        names += [f"{nm}:{q}" for q in ev]
        j += len(ev)
    Xy[:, j:] = d[static].values
    names += static
    Xy_dm, conv = demean(Xy, d[["msoa_id", "bq_id"]].to_numpy().astype(np.uint64), np.ones(len(d)), tol=1e-10)
    assert conv
    del Xy
    gc.collect()
    tested = [f"{t}:{q}" for t in treat_cols for q in ev]
    con = {}
    for t in treat_cols:
        for wl, (a, b) in WINDOWS.items():
            win = [q for q in ev if a <= q <= b]
            con[f"{t}|{wl}"] = {f"{t}:{q}": 1 / len(win) for q in win}
    tab, _ = fit_cluster(Xy_dm[:, 1:], Xy_dm[:, 0], names, tested, cl_se=d.msoa_id.values,
                         cl_boot=d.la_code.values, w=w, k_absorbed_counted=d.bq_id.nunique() - 1, contrasts=con)
    del Xy_dm
    gc.collect()
    is_q = tab.name.str.contains(":")
    tab["treatment_var"] = np.where(is_q, tab.name.str.split(":").str[0], tab.name.str.split("|").str[0])
    tab["period"] = np.where(is_q, tab.name.str.split(":").str[1], tab.name.str.split("|").str[1])
    return tab


def main():
    s, end = analysis_sample()
    print(f"N = {len(s):,}, MSOAs = {s.msoa11.nunique()}, quarters 2017Q1-{end}", flush=True)
    w = rademacher(B, 32, SEED)
    rows = []
    for spec, tcols in TREATMENTS.items():
        tab = estimate(s, tcols, w)
        tab.insert(0, "spec", spec)
        tab["n_obs"], tab["k"], tab["n_msoa_clusters"] = tab.attrs["n_obs"], tab.attrs["k"], tab.attrs["n_clusters"]
        rows.append(tab)
        print(f"{spec:12s} N={tab.attrs['n_obs']:,} K={tab.attrs['k']}", flush=True)
    res = pd.concat(rows, ignore_index=True).drop(columns=["t_bootcluster"])
    res.to_csv(ES / "msoa_access_regression_table.csv", index=False)
    tables(res, end)
    plot(res, end)


def tables(res, end):
    q = res[res.period.str.match(r"^\d{4}Q\d$")]
    piv = q.pivot_table(index="period", columns="treatment_var", values=["coef", "p_wcb"], aggfunc="first")
    order = [t for ts in TREATMENTS.values() for t in ts]
    lines = ["| Quarter | " + " | ".join(LABELS[t] for t in order) + " |", "|---|" + "---|" * len(order)]
    for per in piv.index:
        lab = per + (" (provisional)" if per.startswith("2026") else "")
        lines.append(f"| {lab} | " + " | ".join(
            f"{100 * piv.loc[per, ('coef', t)]:.2f} ({piv.loc[per, ('p_wcb', t)]:.3f})" for t in order) + " |")
    win = res[~res.period.str.match(r"^\d{4}Q\d$")]
    wl = ["| Treatment | Specification | 2020Q1-2021Q4 average | Lagged 2020Q2-2022Q1 average | N | K |",
          "|---|---|---|---|---|---|"]
    for spec, tcols in TREATMENTS.items():
        for t in tcols:
            r = win[(win.spec == spec) & (win.treatment_var == t)].set_index("period")
            cells = [f"{100 * r.loc[k, 'coef']:.2f} (CI {100 * r.loc[k, 'ci_low']:.2f} to {100 * r.loc[k, 'ci_high']:.2f};"
                     f" WCB p {r.loc[k, 'p_wcb']:.3f})" for k in WINDOWS]
            wl.append(f"| {LABELS[t]} | {LABELS[spec]} | " + " | ".join(cells)
                      + f" | {int(r.n_obs.iloc[0]):,} | {int(r.k.iloc[0])} |")
    text = ("Coefficient x 100: log price per SD of the treatment, by quarter; borough wild cluster bootstrap p in "
            "brackets. Headline controls (distance, teleworkability, garden, property type, each x quarter). "
            f"2019Q4 omitted; sample 2017Q1-{end}.\n\n" + "\n".join(lines)
            + "\n\nWindow averages (CI: MSOA-clustered 95%):\n\n" + "\n".join(wl) + "\n")
    (ES / "msoa_access_table.md").write_text(text, encoding="utf-8")
    print("\n".join(wl))


def plot(res, end):
    C = {"D_msoa": "#52514e", "D_access_l15": "#2a78d6", "D_access_l10": "#1baf7a", "D_access_l30": "#6250d6",
         "X_ring_0_1": "#2a78d6", "X_ring_1_2": "#eb6834", "X_ring_2_5": "#1baf7a"}
    INK, INK2, GRID, PRE = "#0b0b0b", "#52514e", "#e4e3df", "#efeeea"
    q = res[res.period.str.match(r"^\d{4}Q\d$")]
    quarters = sorted(set(q.period) | {m87.BASE})
    pos = {p: i for i, p in enumerate(quarters)}
    panels = [("access_l15", ["D_access_l15"]), ("own_density", ["D_msoa"]),
              ("access_l10/30", ["D_access_l10", "D_access_l30"]), ("rings", ["X_ring_0_1", "X_ring_1_2", "X_ring_2_5"])]
    fig, axes = plt.subplots(2, 2, figsize=(16, 9))
    for ax, (pname, tvars) in zip(axes.flat, panels):
        n = len(tvars)
        offs = np.linspace(-0.2, 0.2, n) if n > 1 else [0.0]
        ax.axvspan(-0.5, pos["2020Q1"] - 0.5, color=PRE, lw=0, zorder=0)
        ax.axvspan(pos["2020Q1"] - 0.5, pos["2021Q4"] + 0.5, color="#dce9f8", lw=0, zorder=0)
        ax.axhline(0, color=INK2, lw=0.8)
        for t, dx in zip(tvars, offs):
            spec = "rings" if t.startswith("X_ring") else next(k for k, v in TREATMENTS.items() if v == [t])
            r = q[(q.spec == spec) & (q.treatment_var == t)]
            r = pd.concat([r, pd.DataFrame([{"period": m87.BASE, "coef": 0.0, "ci_low": 0.0, "ci_high": 0.0,
                                             "p_wcb": 1.0}])])
            x = r.period.map(pos) + dx
            sig = r.p_wcb < 0.05
            ax.vlines(x, r.ci_low, r.ci_high, color=C[t], lw=1.0, zorder=2)
            ax.scatter(x[sig], r.coef[sig], s=14, color=C[t], zorder=3, label=f"{LABELS[t]} (WCB p<0.05)")
            ax.scatter(x[~sig], r.coef[~sig], s=14, facecolor="#fcfcfb", edgecolor=C[t], zorder=3,
                       label=f"{LABELS[t]} (WCB p>=0.05)")
        mark_events(ax, quarters)
        shade_provisional(ax, quarters)
        ticks = [i for i, p in enumerate(quarters) if p.endswith("Q1")]
        ax.set_xticks(ticks)
        ax.set_xticklabels([quarters[i][:4] for i in ticks])
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.spines[["top", "right"]].set_visible(False)
        title = {"access_l15": LABELS["access_l15"], "own_density": LABELS["own_density"],
                 "access_l10/30": "Access index, decay 1 km and 3 km (robustness)",
                 "rings": LABELS["rings"]}[pname]
        ax.set_title(title, loc="left", fontsize=9, color=INK, pad=14)
        ax.legend(fontsize=6.5, frameon=False, loc="lower left", ncol=2 if n > 1 else 1)
    for ax in axes.flat:
        ax.set_ylabel("Log price per SD of treatment")
    note = (f"MSOA house-price event studies, 2017Q1-{end}, N = {int(res.n_obs.iloc[0]):,}. Headline controls: MSOA and "
            "borough-by-quarter FE; log distance to Charing Cross, teleworkability, garden access and property type, "
            "each x quarter; new build and leasehold. Omitted 2019Q4. Blue band: closure window 2020Q1-2021Q4. Bars: "
            "95% CI, CR1 clustered by MSOA. Filled: WCR bootstrap p<0.05 by borough (32, B=9,999). Hatched: 2026 "
            "provisional. Y axes differ across panels. The access index correlates -0.85 with log distance to Charing Cross within boroughs. "
            + event_key())
    fig.text(0.01, 0.005, "\n".join(textwrap.wrap(note, 230)), fontsize=7, color=INK2, va="bottom")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(ES / "es_msoa_access.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
