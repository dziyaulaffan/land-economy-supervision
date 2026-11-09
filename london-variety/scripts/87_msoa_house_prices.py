"""MSOA house-price event study, London 2017Q1 to the latest complete quarter of Land Registry data.

Sales: HM Land Registry Price Paid, Category A, property types D/S/T/F, matched to 2011 MSOAs by
postcode with the National Statistics Postcode Lookup, 2011 Census edition (August 2024; the last
NSPL edition carrying 2011 MSOA codes). Postcodes created after August 2024 are not in that edition;
they are placed in the 2011 MSOA of the nearest postcode that is, using coordinates from the current
NSPL (August 2026). Sales outside the 32 analysis boroughs are dropped.

    log p_imt = a_m + l_{b(m),t} + sum_{k != 2019Q4} beta_k 1[t=k] D_m
                + sum_c sum_k gamma_ck 1[t=k] X_cm + Z_i' phi [+ sum_k 1[t=k] Z_type,i' psi_k] + e_imt

a_m MSOA FE, l_bt borough-by-quarter FE, D_m standardised log MSOA amenity density, X_cm standardised
MSOA controls, Z_i property type (S, T, F vs D), new build, leasehold dummies. Optional control
blocks (each interacted with quarter): census/garden controls, log distance to Charing Cross,
log 2019 MSOA median price, and property type dummies.
FE are partialled out (pyfixest demean); both FE sets are nested in borough, so the borough-level
WCR bootstrap on the partialled data is exact (see es_core.py). Analytic SEs: CR1 clustered by MSOA.
Robustness: WCR bootstrap p-values clustered by borough (32 clusters). Baseline and the full
specification are re-run dropping 2021Q2 and 2021Q3 (stamp duty holiday deadlines).
"""
import gc
import textwrap
import zipfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyfixest.estimation import demean
from scipy.spatial import cKDTree

from config import CLEAN, OUT, RAW, download, london_frame
from es_core import fit_cluster, rademacher
from plot_events import event_key, mark_events, shade_provisional

NSPL_URL = "https://www.arcgis.com/sharing/rest/content/items/c5afedb9204a47e99559a4880feddcb1/data"
NSPL = RAW / "nspl" / "NSPL_2011CENSUS_AUG_2024.zip"
NSPL_NEW_URL = "https://www.arcgis.com/sharing/rest/content/items/9d8364ebae8b4439aa66cda440e54fc8/data"
NSPL_NEW = RAW / "nspl" / "NSPL_AUG_2026.zip"
LR_URL = "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-{y}.csv"
LR_COLS = ["txn_id", "price", "date", "postcode", "property_type", "old_new", "duration", "paon", "saon",
           "street", "locality", "town", "district", "county", "ppd_category", "record_status"]
YEARS = range(2017, 2027)
BASE = "2019Q4"
DROP_SDLT = ["2021Q2", "2021Q3"]
REPORT_Q = ["2020Q4", "2021Q4", "2022Q4", "2023Q4"]
WELL_COVERED_Q = "2025Q4"  # last quarter before the 2026 registration-lag shortfall (see msoa_quarterly_coverage.csv)
CONTROLS = {"telework": "X_telework_share", "garden": "X_garden_share", "age2039": "X_age20_39_share",
            "privrent": "X_private_rent_share", "dist": "X_log_dist_cc", "price19": "X_log_med_price_2019"}
ALL4 = ["telework", "garden", "age2039", "privrent"]
# "ptype" = property-type dummies (S, T, F) interacted with quarter
SPECS = {"baseline": [], **{f"+{k}": [k] for k in ALL4}, "+all4": ALL4,
         "+dist": ["dist"], "+all4+dist": ALL4 + ["dist"],
         "+ptype": ["ptype"], "+price19": ["price19"], "+ptype+price19": ["ptype", "price19"],
         "+everything": ALL4 + ["dist", "ptype", "price19"],
         # headline: centrality, teleworkability, gardens and property type; age and private renting are left
         # out because those shares are partly outcomes of amenity-driven sorting (possible mediators)
         "headline": ["dist", "telework", "garden", "ptype"],
         "headline+mediators": ["dist", "telework", "garden", "ptype", "age2039", "privrent"]}
GRID_SPECS = [k for k in SPECS if not k.startswith("headline")]
HEADLINE_SPECS = ["headline", "headline+mediators"]
SDLT_SPECS = ["baseline", "+everything"]
CLOSURE = ["2020Q1", "2020Q2", "2020Q3", "2020Q4", "2021Q1", "2021Q2", "2021Q3", "2021Q4"]
CLOSURE_LABEL = "avg_closure_2020Q1_2021Q4"
LABELS = {"baseline": "Baseline", "+telework": "+ teleworkability", "+garden": "+ garden access",
          "+age2039": "+ share aged 20-39", "+privrent": "+ private renting", "+all4": "+ all four census/garden",
          "+dist": "+ log distance to Charing Cross", "+all4+dist": "+ all four + distance",
          "+ptype": "+ property type x quarter", "+price19": "+ log 2019 MSOA median price",
          "+ptype+price19": "+ property type + 2019 price", "+everything": "+ everything",
          "headline": "Headline: + distance, teleworkability, garden, property type",
          "headline+mediators": "Headline + age 20-39 and private renting (mediator check)"}
B, SEED = 9999, 20261028
ES = OUT / "event_study"
MIN_PRICE = 10_000


def nspl_frames():
    download(NSPL_URL, NSPL)
    with zipfile.ZipFile(NSPL) as z:
        name = next(n for n in z.namelist() if n.startswith("Data/NSPL") and n.endswith(".csv"))
        old = pd.read_csv(z.open(name), usecols=["pcds", "laua", "msoa11", "oseast1m", "osnrth1m"], dtype=str)
    download(NSPL_NEW_URL, NSPL_NEW)
    with zipfile.ZipFile(NSPL_NEW) as z:
        name = next(n for n in z.namelist() if n.startswith("Data/NSPL") and n.endswith(".csv"))
        new = pd.read_csv(z.open(name), usecols=["pcds", "lad26cd", "east1m", "north1m"], dtype=str)
    return old, new


def build_sales(districts: set) -> pd.DataFrame:
    years = list(YEARS)
    out = CLEAN / f"msoa_sales_{years[0]}_{years[-1]}.parquet"
    if out.exists():
        return pd.read_parquet(out)
    old, new = nspl_frames()
    lon = london_frame()
    old_l = old[old.laua.isin(lon.la_code)].rename(columns={"pcds": "postcode"})

    frames = []
    for y in years:
        f = download(LR_URL.format(y=y), RAW / "land_registry" / f"pp-{y}.csv")
        d = pd.read_csv(f, header=None, names=LR_COLS,
                        usecols=["price", "date", "postcode", "property_type", "old_new", "duration", "district",
                                 "ppd_category"], dtype=str)
        frames.append(d[d.district.isin(districts)])
    s = pd.concat(frames, ignore_index=True)
    s["price"] = s.price.astype(float)
    s = s.merge(old_l[["postcode", "laua", "msoa11"]], on="postcode", how="left")
    s["msoa_match"] = np.where(s.msoa11.notna(), "nspl2011", None)

    # postcodes missing from the 2011 edition: nearest 2011-edition postcode within the same borough
    miss = s.loc[s.msoa11.isna() & s.postcode.notna(), "postcode"].unique()
    nn = new[new.pcds.isin(miss) & new.lad26cd.isin(lon.la_code)].dropna(subset=["east1m", "north1m"])
    ref = old_l.dropna(subset=["oseast1m", "osnrth1m", "msoa11"])
    assigned = []
    for la, g in nn.groupby("lad26cd"):
        r = ref[ref.laua == la]
        tree = cKDTree(r[["oseast1m", "osnrth1m"]].astype(float).values)
        dist, idx = tree.query(g[["east1m", "north1m"]].astype(float).values)
        assigned.append(pd.DataFrame({"postcode": g.pcds.values, "laua_nn": la,
                                      "msoa11_nn": r.msoa11.values[idx], "nn_dist_m": dist}))
    if assigned:
        a = pd.concat(assigned)
        s = s.merge(a, on="postcode", how="left")
        fill = s.msoa11.isna() & s.msoa11_nn.notna()
        s.loc[fill, "msoa11"] = s.loc[fill, "msoa11_nn"]
        s.loc[fill, "laua"] = s.loc[fill, "laua_nn"]
        s.loc[fill, "msoa_match"] = "nearest_postcode"
        s = s.drop(columns=["msoa11_nn", "laua_nn"])
    s["date"] = pd.to_datetime(s.date.str[:10])
    s["quarter"] = s.date.dt.to_period("Q").astype(str)
    s.to_parquet(out)
    return s


def latest_complete_quarter(s: pd.DataFrame) -> str:
    """Last quarter whose three months all contain sales."""
    months = s.date.dt.to_period("M").unique()
    q = sorted({str(m.asfreq("Q")) for m in months})
    full = [x for x in q if sum(str(m.asfreq("Q")) == x for m in months) == 3]
    return full[-1]


def coverage(s: pd.DataFrame, end: str) -> pd.DataFrame:
    """Category A sales per quarter against the same quarter a year earlier (registration lag check)."""
    c = s[s.ppd_category == "A"].groupby("quarter").size().rename("n_catA").to_frame()
    c["same_q_prev_year"] = [c.n_catA.get(str(pd.Period(q, "Q") - 4), np.nan) for q in c.index]
    c["ratio_to_prev_year"] = c.n_catA / c.same_q_prev_year
    nb = s[s.ppd_category == "A"].groupby("quarter").old_new.apply(lambda x: (x == "Y").mean())
    c["new_build_share"] = nb
    c["in_sample"] = c.index <= end
    return c.reset_index()


def msoa_price_2019(s: pd.DataFrame) -> pd.DataFrame:
    p = (s[s.quarter.str.startswith("2019")].groupby("msoa11").price.agg(["median", "size"])
         .rename(columns={"median": "med_price_2019", "size": "n_sales_2019"}))
    p["log_med_price_2019"] = np.log(p.med_price_2019)
    p["X_log_med_price_2019"] = (p.log_med_price_2019 - p.log_med_price_2019.mean()) / p.log_med_price_2019.std()
    return p.reset_index().rename(columns={"msoa11": "msoa11_code"})


def main():
    dmap = pd.read_csv(CLEAN / "land_registry_district_to_la.csv")
    districts = set(dmap[dmap.la_code.isin(london_frame().la_code)].district) | {"CITY OF LONDON"}
    s = build_sales(districts)
    end = latest_complete_quarter(s)
    cov = coverage(s, end)
    cov.to_csv(ES / "msoa_quarterly_coverage.csv", index=False)
    print(f"latest complete quarter: {end}")
    print(cov.tail(8).round(3).to_string(index=False))

    steps = [(f"London district sales {s.quarter.min()}-{s.quarter.max()} (all categories, incl. City)", len(s))]
    s = s[s.quarter <= end]; steps.append((f"Quarters up to {end}", len(s)))
    s = s[s.ppd_category == "A"]; steps.append(("Category A", len(s)))
    s = s[s.property_type.isin(["D", "S", "T", "F"])]; steps.append(("Property type D/S/T/F", len(s)))
    s = s[s.price >= MIN_PRICE]; steps.append((f"Price >= {MIN_PRICE:,}", len(s)))
    s = s[s.msoa11.notna()]; steps.append(("Postcode placed in a 2011 MSOA in the 32 boroughs", len(s)))
    nn_share = (s.msoa_match == "nearest_postcode").mean()
    m = pd.read_csv(CLEAN / "msoa_amenity_controls.csv")
    dist = pd.read_csv(CLEAN / "msoa_distance_charing_cross.csv")
    p19 = msoa_price_2019(s)
    p19.to_csv(CLEAN / "msoa_median_price_2019.csv", index=False)
    m = m.merge(dist[["msoa11_code", "X_log_dist_cc", "dist_cc_km"]], on="msoa11_code").merge(
        p19, on="msoa11_code", how="left")
    assert m.X_log_med_price_2019.notna().all(), "MSOA without 2019 sales"
    s = s.merge(m[["msoa11_code", "la_code", "D_msoa", *CONTROLS.values()]], left_on="msoa11",
                right_on="msoa11_code", how="inner", suffixes=("", "_m"))
    steps.append(("Merged to MSOA amenity and controls", len(s)))
    mism = (s.laua != s.la_code).mean()
    s = s[s.duration.isin(["F", "L"])]; steps.append(("Tenure F or L (drops U)", len(s)))
    sample = pd.DataFrame(steps, columns=["step", "n"])
    sample.to_csv(ES / "msoa_sample_construction.csv", index=False)
    print(sample.to_string(index=False))
    print(f"nearest-postcode placements: {nn_share:.4f} of sample; NSPL LA vs MSOA LA mismatch: {mism:.5f}; "
          f"MSOAs: {s.msoa11.nunique()}; 2019 sales per MSOA min {p19.n_sales_2019.min()}, "
          f"median {p19.n_sales_2019.median():.0f}")
    corr = m[["D_msoa", "X_log_dist_cc", "X_log_med_price_2019"]].corr().round(3)
    print(corr)

    s["y"] = np.log(s.price)
    for t in ["S", "T", "F"]:
        s[f"type_{t}"] = (s.property_type == t).astype(float)
    s["new_build"] = (s.old_new == "Y").astype(float)
    s["leasehold"] = (s.duration == "L").astype(float)
    s["msoa_id"] = pd.factorize(s.msoa11)[0]
    s["bq_id"] = pd.factorize(s.la_code + "_" + s.quarter)[0]
    w = rademacher(B, 32, SEED)

    rows, ok_check = [], None
    runs = [("all_quarters", [], list(SPECS)), ("drop_2021Q2_Q3", DROP_SDLT, SDLT_SPECS)]
    for sample_name, drop, specs in runs:
        d = s[~s.quarter.isin(drop)].reset_index(drop=True)
        ev = [q for q in sorted(d.quarter.unique()) if q != BASE]
        Q = pd.get_dummies(d.quarter, dtype=float)[ev].values
        fl = d[["msoa_id", "bq_id"]].to_numpy().astype(np.uint64)
        for spec in specs:
            ctrls = SPECS[spec]
            cols = [("D_msoa", d.D_msoa.values)]
            for c in ctrls:
                if c == "ptype":
                    cols += [(f"type{t}", d[f"type_{t}"].values) for t in ["S", "T", "F"]]
                else:
                    cols.append((c, d[CONTROLS[c]].values))
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
            Xy_dm, conv = demean(Xy, fl, np.ones(len(d)), tol=1e-10)
            assert conv, "demeaning did not converge"
            del Xy
            gc.collect()
            tested = [f"D_msoa:{q}" for q in ev]
            win = [q for q in CLOSURE if q in ev]  # the stamp-duty sample lacks 2021Q2-Q3
            con = {CLOSURE_LABEL: {f"D_msoa:{q}": 1 / len(win) for q in win}}
            tab, _ = fit_cluster(Xy_dm[:, 1:], Xy_dm[:, 0], names, tested, cl_se=d.msoa_id.values,
                                 cl_boot=d.la_code.values, w=w, k_absorbed_counted=d.bq_id.nunique() - 1,
                                 contrasts=con)
            tab["period"] = tab.name.str.split(":").str[1].fillna(tab.name)
            tab["closure_quarters"] = len(win)
            tab.insert(0, "spec", spec)
            tab.insert(0, "sample", sample_name)
            tab["n_obs"], tab["n_msoa_clusters"], tab["k"] = tab.attrs["n_obs"], tab.attrs["n_clusters"], tab.attrs["k"]
            tab["n_boot_clusters"] = 32
            tab["end_quarter"] = end
            rows.append(tab)
            print(f"{sample_name:15s} {spec:15s} N={len(d):,} K={tab.attrs['k']}", flush=True)
            if sample_name == "all_quarters" and spec == "baseline":
                ok_check = (d, ev, tab)
            del Xy_dm
            gc.collect()
    res = pd.concat(rows, ignore_index=True).rename(columns={"t_bootcluster": "t_borough_cluster"})
    res.to_csv(ES / "msoa_regression_table.csv", index=False)
    summary(res, end)

    # cross-check baseline against pyfixest (coefficients and MSOA-clustered SEs)
    import pyfixest as pf
    d, ev, tab = ok_check
    for q in ev:
        d[f"Dq_{q}"] = (d.quarter == q) * d.D_msoa
    fml = ("y ~ " + " + ".join(f"Dq_{q}" for q in ev)
           + " + type_S + type_T + type_F + new_build + leasehold | msoa_id + bq_id")
    f = pf.feols(fml, data=d, vcov={"CRV1": "msoa_id"})
    tq = tab[tab.name.str.startswith("D_msoa:")]
    cmp = np.abs(f.coef()[[f"Dq_{q}" for q in ev]].values - tq.coef.values).max()
    cmp_se = np.abs(f.se()[[f"Dq_{q}" for q in ev]].values / tq.se_cluster.values - 1).max()
    print(f"pyfixest check: max |coef diff| {cmp:.2e}, max relative SE diff {cmp_se:.4f}")
    pd.DataFrame([{"max_abs_coef_diff": cmp, "max_rel_se_diff": cmp_se}]).to_csv(ES / "msoa_pyfixest_check.csv",
                                                                                 index=False)
    plot(res, end)
    headline(res, end)


def summary(res: pd.DataFrame, end: str):
    """Amenity coefficient (log points x 100) at REPORT_Q and the latest quarter, with borough WCB p."""
    qs = [CLOSURE_LABEL] + REPORT_Q + [WELL_COVERED_Q, end]
    t = res[res.period.isin(qs)].copy()
    t["cell"] = t.apply(lambda r: f"{100 * r.coef:.2f} ({r.p_wcb:.3f})", axis=1)
    long = t[["sample", "spec", "period", "coef", "se_cluster", "p_cluster", "p_wcb", "n_obs", "k"]]
    long.to_csv(ES / "msoa_summary_table.csv", index=False)
    wide = t.pivot_table(index=["sample", "spec"], columns="period", values="cell", aggfunc="first")[qs]
    n = t.groupby(["sample", "spec"]).n_obs.first()
    wide["N"] = n.map("{:,}".format)
    order = ([("all_quarters", s) for s in GRID_SPECS] + [("all_quarters", s) for s in HEADLINE_SPECS]
             + [("drop_2021Q2_Q3", s) for s in SDLT_SPECS])
    wide = wide.reindex(order)
    lines = ["| Sample | Specification | 2020Q1-2021Q4 average | " + " | ".join(REPORT_Q)
             + f" | {WELL_COVERED_Q} (last well-covered) | {end} (latest, provisional) | N |",
             "|---|---|" + "---|" * (len(qs) + 1)]
    for (smp, spec), r in wide.iterrows():
        smp_l = "All quarters" if smp == "all_quarters" else "Drop 2021Q2-Q3"
        lines.append(f"| {smp_l} | {LABELS[spec]} | " + " | ".join(r[q] for q in qs) + f" | {r.N} |")
    (ES / "msoa_summary_table.md").write_text(
        "Amenity coefficient x 100 (log points per SD of log MSOA amenity density), borough wild cluster "
        "bootstrap p in brackets. The closure-window average is over 2020Q1-2021Q4 (over the 6 remaining quarters in "
        "the stamp-duty sample).\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def plot(res, end):
    C1, INK, INK2, GRID, PRE = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df", "#efeeea"
    quarters = sorted(set(res.period) | {BASE} | set(DROP_SDLT))
    pos = {q: i for i, q in enumerate(quarters)}
    res = res[res.period.str.match(r"^\d{4}Q\d$")]
    for sample_name, g in res.groupby("sample"):
        specs = GRID_SPECS if sample_name == "all_quarters" else SDLT_SPECS
        nr, nc = (3, 4) if len(specs) > 2 else (1, 2)
        fig, axes = plt.subplots(nr, nc, figsize=(17, 3.4 * nr + 0.8), sharey=True, squeeze=False)
        for ax, spec in zip(axes.flat, specs):
            t = g[g.spec == spec].copy()
            t = pd.concat([t, pd.DataFrame([{"period": BASE, "coef": 0.0, "ci_low": 0.0, "ci_high": 0.0,
                                             "p_wcb": 1.0}])])
            x = t.period.map(pos)
            first_post = pos["2020Q1"]
            ax.axvspan(-0.5, first_post - 0.5, color=PRE, lw=0, zorder=0)
            ax.axhline(0, color=INK2, lw=0.8)
            ax.axvline(first_post - 0.5, color=INK2, lw=0.8, ls="--")
            for q in DROP_SDLT:
                ax.axvline(pos[q], color="#d9d8d3", lw=4, zorder=0)
            sig = t.p_wcb < 0.05
            ax.vlines(x, t.ci_low, t.ci_high, color=C1, lw=1.1, zorder=2)
            ax.scatter(x[sig], t.coef[sig], s=14, color=C1, zorder=3, label="Borough WCB p<0.05")
            ax.scatter(x[~sig], t.coef[~sig], s=14, facecolor="#fcfcfb", edgecolor=C1, zorder=3,
                       label="Borough WCB p>=0.05")
            ticks = [i for i, q in enumerate(quarters) if q.endswith("Q1")]
            ax.set_xticks(ticks)
            ax.set_xticklabels([quarters[i][2:4] for i in ticks])
            ax.grid(axis="y", color=GRID, lw=0.6)
            ax.spines[["top", "right"]].set_visible(False)
            r0 = t.dropna(subset=["n_obs"]).iloc[0]
            ax.set_title(f"{LABELS[spec]}\nN={int(r0.n_obs):,}, K={int(r0.k)}", fontsize=8.5, color=INK, loc="left")
        for ax in axes[:, 0]:
            ax.set_ylabel("Log price per SD of\nlog MSOA amenity density")
        h, l = axes.flat[0].get_legend_handles_labels()
        fig.legend(h, l, loc="upper center", ncol=2, fontsize=8, frameon=False)
        what = "all quarters" if sample_name == "all_quarters" else "2021Q2 and 2021Q3 dropped (stamp duty deadlines)"
        note = (f"MSOA house-price event study, 2017Q1-{end}, {what}. MSOA and borough-by-quarter FE; property type, "
                "new build and leasehold controls; named controls interacted with quarter. Omitted 2019Q4. Bars: 95% "
                "CI, CR1 clustered by MSOA (982). Filled: WCR bootstrap p<0.05 clustered by borough (32, B=9,999). "
                "Grey bars mark 2021Q2-Q3. X axis: two-digit year at Q1.")
        fig.text(0.01, 0.005, "\n".join(textwrap.wrap(note, 220)), fontsize=7, color=INK2, va="bottom")
        fig.tight_layout(rect=(0, 0.04, 1, 0.96))
        fig.savefig(ES / f"es_msoa_prices_{sample_name}.png", dpi=150)
        plt.close(fig)


def headline(res: pd.DataFrame, end: str):
    """Headline and mediator-check coefficients for every quarter, and the headline event-study plot."""
    h = res[(res["sample"] == "all_quarters") & res.spec.isin(HEADLINE_SPECS)]
    h.to_csv(ES / "msoa_headline_table.csv", index=False)
    w = h.pivot_table(index="period", columns="spec", values=["coef", "p_wcb"], aggfunc="first")
    rows = [q for q in w.index if q != CLOSURE_LABEL] + [CLOSURE_LABEL]
    lines = ["| Quarter | Headline | Headline + mediators |", "|---|---|---|"]
    for q in rows:
        if q == CLOSURE_LABEL:
            lab = "**2020Q1-2021Q4 average (closure window)**"
        else:
            lab = q + (" (provisional)" if q.startswith("2026") else "")
        cells = [f"{100 * w.loc[q, ('coef', s)]:.2f} ({w.loc[q, ('p_wcb', s)]:.3f})" for s in HEADLINE_SPECS]
        lines.append(f"| {lab} | " + " | ".join(cells) + " |")
    (ES / "msoa_headline_table.md").write_text(
        "Amenity coefficient x 100 (log points per SD of log MSOA amenity density) by quarter, borough wild cluster "
        "bootstrap p in brackets. 2019Q4 omitted.\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    C1, C2, INK, INK2, GRID, PRE = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#efeeea"
    q_only = h[h.period.str.match(r"^\d{4}Q\d$")]
    quarters = sorted(set(q_only.period) | {BASE})
    pos = {q: i for i, q in enumerate(quarters)}
    fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True, sharey=True)
    for ax, spec, col in zip(axes, HEADLINE_SPECS, (C1, C2)):
        t = q_only[q_only.spec == spec]
        t = pd.concat([t, pd.DataFrame([{"period": BASE, "coef": 0.0, "ci_low": 0.0, "ci_high": 0.0, "p_wcb": 1.0}])])
        x = t.period.map(pos)
        ax.axvspan(-0.5, pos["2020Q1"] - 0.5, color=PRE, lw=0, zorder=0)
        ax.axvspan(pos[CLOSURE[0]] - 0.5, pos[CLOSURE[-1]] + 0.5, color="#dce9f8", lw=0, zorder=0)
        ax.axhline(0, color=INK2, lw=0.8)
        sig = t.p_wcb < 0.05
        ax.vlines(x, t.ci_low, t.ci_high, color=col, lw=1.2, zorder=2)
        ax.scatter(x[sig], t.coef[sig], s=18, color=col, zorder=3, label="Borough WCB p<0.05")
        ax.scatter(x[~sig], t.coef[~sig], s=18, facecolor="#fcfcfb", edgecolor=col, zorder=3,
                   label="Borough WCB p>=0.05")
        a = h[(h.spec == spec) & (h.period == CLOSURE_LABEL)].iloc[0]
        ax.hlines(a.coef, pos[CLOSURE[0]] - 0.5, pos[CLOSURE[-1]] + 0.5, color=col, lw=2, ls="--", zorder=2)
        ax.set_ylim(-0.065, 0.04)
        mark_events(ax, quarters)
        shade_provisional(ax, quarters)
        ax.set_title(f"{LABELS[spec]}\nClosure-window average 2020Q1-2021Q4: {100 * a.coef:.2f} log points "
                     f"(MSOA-clustered 95% CI {100 * a.ci_low:.2f} to {100 * a.ci_high:.2f}; borough WCB p = "
                     f"{a.p_wcb:.3f}). N={int(a.n_obs):,}, K={int(a.k)}", fontsize=9, color=INK, loc="left", pad=14)
        ax.set_ylabel("Log price per SD of\nlog MSOA amenity density")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(fontsize=7.5, frameon=False, loc="lower left")
    ticks = [i for i, q in enumerate(quarters) if q.endswith("Q1")]
    axes[1].set_xticks(ticks)
    axes[1].set_xticklabels([quarters[i][:4] for i in ticks])
    note = ("MSOA house-price event study, 2017Q1-" + end + ". MSOA and borough-by-quarter FE; property type, new "
            "build and leasehold controls. Omitted 2019Q4. Blue band: closure window 2020Q1-2021Q4 with its average "
            "(dashed). Hatched: 2026, provisional (registration lag). Bars: 95% CI, CR1 clustered by MSOA (982). "
            "Filled: WCR bootstrap p<0.05 clustered by borough (32, B=9,999). " + event_key())
    fig.text(0.01, 0.005, "\n".join(textwrap.wrap(note, 200)), fontsize=7, color=INK2, va="bottom")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(ES / "es_msoa_headline.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
