"""Event-study plots and a specification summary from outputs/event_study/regression_table.csv.

One figure per outcome x treatment type, one panel per specification. Bars are 95% intervals from
borough-clustered CR1 standard errors (t with G-1 df). Filled markers: wild cluster bootstrap
p < 0.05; hollow markers: p >= 0.05. The omitted period is drawn at zero. Pre-2020 periods sit on a
shaded background.
"""
import textwrap

import matplotlib.pyplot as plt
import pandas as pd

from config import OUT

ES = OUT / "event_study"
C1, C2 = "#2a78d6", "#eb6834"
INK, INK2, GRID, PRE = "#0b0b0b", "#52514e", "#e4e3df", "#efeeea"
SPEC_ORDER = ["baseline", "+garden", "+telework", "+age2039", "+privrent", "+all"]
SPEC_LABEL = {"baseline": "Baseline", "+garden": "+ garden access x period",
              "+telework": "+ teleworkability x period", "+age2039": "+ share aged 20-39 x period",
              "+privrent": "+ private renting share x period", "+all": "+ all four controls x period"}
TERM = {"D_cont": ("Std. log amenity density", C1), "T2": ("Middle tercile vs bottom", C1),
        "T3": ("Top tercile vs bottom", C2)}
YLAB = {"migration": "Effect on net migration per 1,000\n(per SD of log amenity density)",
        "rents": "Effect on 100 x log rent index\n(per SD of log amenity density)"}
YLAB_BIN = {"migration": "Net migration per 1,000, vs bottom tercile",
            "rents": "100 x log rent index, vs bottom tercile"}

plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "legend.frameon": False})


def panel(ax, d, base, terms, periods):
    pos = {p: i for i, p in enumerate(periods)}
    first_post = next(i for i, p in enumerate(periods) if p > base)
    ax.axvspan(-0.5, first_post - 0.5, color=PRE, lw=0, zorder=0)
    ax.axhline(0, color=INK2, lw=0.8, zorder=1)
    ax.axvline(first_post - 0.5, color=INK2, lw=0.8, ls="--", zorder=1)
    off = {1: [0.0], 2: [-0.18, 0.18]}[len(terms)]
    for term, dx in zip(terms, off):
        lab, col = TERM[term]
        s = d[d.term == term].copy()
        s = pd.concat([s, pd.DataFrame([{"period": base, "coef": 0.0, "ci_low": 0.0, "ci_high": 0.0, "p_wcb": 1.0}])])
        x = s.period.map(pos) + dx
        ax.vlines(x, s.ci_low, s.ci_high, color=col, lw=1.4, zorder=2)
        sig = s.p_wcb < 0.05
        ax.scatter(x[sig], s.coef[sig], s=22, color=col, zorder=3, label=f"{lab} (WCB p<0.05)")
        ax.scatter(x[~sig], s.coef[~sig], s=22, facecolor="#fcfcfb", edgecolor=col, lw=1.2, zorder=3,
                   label=f"{lab} (WCB p>=0.05)")
    step = 1 if len(periods) <= 12 else 4
    ticks = [i for i, p in enumerate(periods) if (i % step == 0 if step == 1 else p.endswith("Q1"))]
    ax.set_xticks(ticks)
    ax.set_xticklabels([periods[i][:4] if step > 1 else periods[i] for i in ticks], rotation=0)
    ax.set_xlim(-0.6, len(periods) - 0.4)
    ax.grid(axis="y", color=GRID, lw=0.6)


def main():
    t = pd.read_csv(ES / "regression_table.csv", dtype={"period": str, "base_period": str})
    for (outcome, ttype), d in t.groupby(["outcome", "treatment"]):
        base = d.base_period.iloc[0]
        periods = sorted(set(d.period) | {base})
        terms = ["D_cont"] if ttype == "continuous" else ["T2", "T3"]
        fig, axes = plt.subplots(2, 3, figsize=(14 if outcome == "rents" else 12, 7.2), sharey=True)
        for ax, spec in zip(axes.flat, SPEC_ORDER):
            s = d[d.spec == spec]
            panel(ax, s, base, terms, periods)
            pre = s[s.term == terms[-1]].iloc[0]
            ax.set_title(f"{SPEC_LABEL[spec]}\nN={int(pre.n_obs)}, clusters={int(pre.n_clusters)}, "
                         f"pre-trend Wald p={pre.pretrend_p:.3f}", fontsize=8.5, color=INK, loc="left")
        for ax in axes[:, 0]:
            ax.set_ylabel((YLAB if ttype == "continuous" else YLAB_BIN)[outcome])
        h, l = axes.flat[0].get_legend_handles_labels()
        fig.legend(h, l, loc="upper center", ncol=len(l), fontsize=8, bbox_to_anchor=(0.5, 1.0))
        what = "standardised log amenity density" if ttype == "continuous" else \
            "within-zone amenity terciles (Inner 4/4/5, Outer 6/6/7 boroughs)"
        note = (f"{outcome.title()} event study on {what}. Borough and period FE. Omitted period {base} (plotted "
                f"at 0). Shaded = pre-period; dashed line = start of 2020. Bars: 95% CI, borough-clustered CR1, "
                "t(31). Filled: wild cluster restricted bootstrap p<0.05 (Rademacher, B=9,999). Pre-trend Wald: "
                "cluster-robust F test that all pre-period coefficients are zero; unreliable when the number of "
                "restrictions is large relative to 32 clusters (rents: 19).")
        fig.text(0.01, 0.005, "\n".join(textwrap.wrap(note, 190)), fontsize=7, color=INK2, va="bottom")
        fig.tight_layout(rect=(0, 0.045, 1, 0.95))
        fig.savefig(ES / f"es_{outcome}_{ttype}.png", dpi=150)
        plt.close(fig)

    # specification summary
    key = t.drop_duplicates(["outcome", "treatment", "spec", "term"])
    key = key[["outcome", "treatment", "spec", "term", "n_obs", "n_clusters", "k", "pretrend_q", "pretrend_F",
               "pretrend_p"]]
    key.to_csv(ES / "spec_summary.csv", index=False)
    print(key.to_string(index=False))


if __name__ == "__main__":
    main()
