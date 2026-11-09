"""Build outputs/report/report.tex from scripts/report_template.tex and the estimation outputs.

The template holds the prose. Every <<KEY>> placeholder is replaced by a LaTeX fragment built here from the CSV
outputs in outputs/event_study/ and data/clean/: pgfplots coordinates for the figures and booktabs table bodies.
The result is a single self-contained .tex file for Overleaf (pdflatex).
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

from config import CLEAN, OUT

HERE = Path(__file__).parent
ES = OUT / "event_study"
REPORT = OUT / "report"
REPORT.mkdir(parents=True, exist_ok=True)
START = 2016  # migration sample start used in the report (see ESTIMATION_NOTES.md section 17)
EXT = HERE.parent / "extension" / "data" / "clean"  # England and Wales extension outputs
VM = HERE.parent / "extension" / "venue_mix" / "data"  # venue-mix extension outputs
REC = HERE.parent / "extension" / "recovery" / "data"  # recovery extension outputs


def num(x, d=2):
    """Number in math mode with a proper minus sign."""
    s = f"{x:.{d}f}"
    return f"${s.replace('-', '-')}$" if not s.startswith("-") else f"$-{s[1:]}$"


def pv(p):
    return "$<0.001$" if p < 0.0005 else f"${p:.3f}$"


def cell(coef, p, d=2):
    return f"{num(coef, d)} ({pv(p)})"


def coords(xs, ys, es):
    return " ".join(f"({x},{y:.4f}) +- (0,{e:.4f})" for x, y, e in zip(xs, ys, es))


def coords_plain(xs, ys):
    return " ".join(f"({x},{y:.4f})" for x, y in zip(xs, ys))


def es_series(df, base_x, xcol="x", scale=1.0):
    """Coordinates with symmetric 95% CI half-widths; adds the omitted base period at zero."""
    df = df.copy()
    df["half"] = (df.ci_high - df.ci_low) / 2
    df = pd.concat([df, pd.DataFrame([{xcol: base_x, "coef": 0.0, "half": 0.0}])]).sort_values(xcol)
    return coords(df[xcol], df.coef * scale, df.half * scale)


def qx(q: str) -> float:
    """Quarter label to a decimal year at the quarter midpoint."""
    return int(q[:4]) + (int(q[-1]) - 1) / 4 + 0.125


def build() -> dict:
    f = {}
    # ---------------- figures ----------------
    rt = pd.read_csv(ES / "regression_table.csv", dtype={"period": str})
    # migration models re-estimated on the 2016-2025 sample by 97_preperiod_check.py
    rep = pd.read_csv(ES / "report_migration_2016.csv", dtype={"term": str})
    rep = rep[rep.term.str.fullmatch(r"\d{4}")].assign(x=lambda d: d.term.astype(int))
    es16 = rep[(rep.analysis == "event study") & (rep.control == "none") & (rep["sample"] == "32 boroughs")]
    f["FIG_MIG_ALL"] = es_series(es16[es16.group == "all"], 2019)
    age = es16.copy()
    offs = {"age20_29": -0.21, "age30_39": -0.07, "family_0_15_30_49": 0.07, "age50plus": 0.21}
    for g, key in (("age20_29", "A2029"), ("age30_39", "A3039"), ("family_0_15_30_49", "AFAM"), ("age50plus", "A50")):
        t = age[age.group == g].copy()
        t["x"] = t.x + offs[g]
        f[f"FIG_{key}"] = es_series(t, 2019 + offs[g])

    ddd = pd.read_csv(ES / "preperiod_check.csv", dtype={"term": str})
    ddd = ddd[ddd["sample"] == f"{START}-2025"]
    for model, key, off in (("DDD vs family proxy, yearly", "DDDFAM", -0.1), ("DDD vs 50+, yearly", "DDD50", 0.1)):
        t = ddd[(ddd.model == model) & ddd.term.str.fullmatch(r"\d{4}")].copy()
        t["x"] = t.term.astype(int) + off
        f[f"FIG_{key}"] = es_series(t, 2019 + off)

    rent = rt[(rt.outcome == "rents") & (rt.treatment == "continuous") & (rt.spec == "baseline")].copy()
    rent["x"] = rent.period.map(qx)
    f["FIG_RENT"] = es_series(rent, qx("2019Q4"))
    tb = pd.read_csv(ES / "rent_trend_break.csv")
    slope = tb[tb.term == "pre-2020 linear trend"].coef.iloc[0]
    dev = tb[tb.term == "deviation from extrapolated trend"].copy()
    dev["x"] = dev.period.map(qx)
    dev["half"] = (dev.ci_high - dev.ci_low) / 2
    f["FIG_RENTDEV"] = coords(dev.x, dev.coef, dev.half)
    # trend line on the event-study scale: delta * tau + c, c recovered as in 82_rent_trend_break.py
    es_post = rent.set_index("period").coef
    c0 = np.mean([es_post[p] - r.coef - slope * (qx(p) - qx("2019Q4")) * 4 for p, r in dev.set_index("period").iterrows()])
    xs = [qx("2015Q1"), qx("2026Q3")]
    f["FIG_RENTTREND"] = coords_plain(xs, [slope * (x - qx("2019Q4")) * 4 + c0 for x in xs])
    f["RENT_SLOPE"] = f"{slope:.2f}"
    f["RENT_INTERCEPT"] = f"{c0:.2f}"
    avg = tb[tb.term == "average deviation"]

    hp = pd.read_csv(ES / "msoa_headline_table.csv")
    h = hp[(hp.spec == "headline") & hp.period.str.match(r"^\d{4}Q\d$")].copy()
    h["x"] = h.period.map(qx)
    f["FIG_HP"] = es_series(h, qx("2019Q4"), scale=100)

    ptr = pd.read_csv(ES / "price_to_rent_groups.csv")
    ptr["x"] = ptr.period.map(qx)
    for g, key in (("Inner, high amenity", "PTRIH"), ("Inner, low amenity", "PTRIL"),
                   ("Outer, high amenity", "PTROH"), ("Outer, low amenity", "PTROL")):
        t = ptr[ptr.zone_amenity_group == g].sort_values("x")
        f[f"FIG_{key}"] = coords_plain(t.x, t.ptr_index_2019)

    # ---------------- tables ----------------
    f["TAB_DESC"] = desc_table()
    f["TAB_CORR"] = corr_table()
    f["TAB_DECOMP"] = decomp_table()
    f["TAB_DDD"] = ddd_table(ddd)
    f["TAB_ROBUST"] = robust_table()
    f["TAB_RENTTESTS"] = rent_tests_table()
    f["TAB_DDD2529"] = ddd2529_table()
    f["TAB_IDLIM"] = idlim_table()
    f["TAB_NATREG"] = natreg_table()
    f["TAB_MEASURES"] = measures_table()
    f["TAB_DENS"] = density_table()
    f["FIG_NATD"], f["FIG_NATC"] = national_series()
    f["TAB_VM"] = vm_table()
    f["TAB_REC"] = rec_table()
    f["FIG_REC"], f["FIG_REC_TICKS"] = rec_series()
    f["TAB_HONEST"] = honest_table()
    f["TAB_HP"] = hp_table()
    f["TAB_ACCESS"] = access_table()
    f["TAB_RENTRET"] = rent_return_table(avg)
    f["RENT_CLOSURE"] = rent_closure_text()
    return f


def desc_table() -> str:
    a = pd.read_csv(CLEAN / "london_amenity_density_2019.csv")
    c = pd.read_csv(CLEAN / "controls_borough.csv")
    s = pd.read_csv(CLEAN / "borough_student_hospitality_2011.csv")
    b = a.merge(c, on="la_code", suffixes=("", "_c")).merge(s, on="la_code")
    m = pd.read_csv(CLEAN / "msoa_amenity_controls.csv").merge(pd.read_csv(CLEAN / "msoa_access_2019.csv")[
        ["msoa11_code", "access_l15"]], on="msoa11_code").merge(pd.read_csv(CLEAN / "msoa_distance_charing_cross.csv")[
            ["msoa11_code", "dist_cc_km"]], on="msoa11_code")
    mig = pd.read_csv(CLEAN / "migration_net_by_age_group.csv")
    mig = mig[mig.year_ending_june.between(START, 2019)]
    rows = [
        ("Boroughs ($n=32$)", None),
        ("Hospitality and leisure units per 1,000 residents, 2019", b.per1k_IR),
        ("Share of addresses with private outdoor space, 2020", b.garden_share),
        ("Share of employed residents in teleworkable jobs, 2011", b.telework_share),
        ("Share of residents aged 20 to 39, 2011", b.age20_39_share),
        ("Share of households renting privately, 2011", b.private_rent_share),
        ("Full-time students aged 18+ per resident aged 16+, 2011", b.student_share),
        ("Hospitality and other-services share of employed 16--34s, 2011", b.hosp_share_I_RSTU),
        ("Net migration with rest of UK per 1,000, all ages, 2016--2019", mig[mig.group == "all"].net_per1k_group),
        ("Net migration with rest of UK per 1,000, ages 20--29, 2016--2019", mig[mig.group == "age20_29"].net_per1k_group),
        ("MSOAs ($n=982$)", None),
        ("Hospitality and leisure units per 1,000 residents, 2019", m.per1k_IR),
        ("Access index, decay 1.5 km (units)", m.access_l15),
        ("Distance to Charing Cross (km)", m.dist_cc_km),
    ]
    out = []
    for lab, v in rows:
        if v is None:
            out.append(f"\\multicolumn{{6}}{{l}}{{\\textit{{{lab}}}}} \\\\")
            continue
        out.append(f"{lab} & {num(v.mean())} & {num(v.std())} & {num(v.min())} & {num(v.median())} & {num(v.max())} \\\\")
    return "\n".join(out)


def corr_table() -> str:
    b = pd.read_csv(CLEAN / "event_study_borough_vars.csv")
    labs = {"telework_share": "Teleworkability", "garden_share": "Garden access",
            "age20_39_share": "Share aged 20 to 39", "private_rent_share": "Private renting share"}
    mc = pd.read_csv(ES / "msoa_correlations.csv").set_index("variable")
    ac = pd.read_csv(ES / "msoa_access_correlations.csv")
    md = pd.read_csv(CLEAN / "msoa_amenity_controls.csv").merge(
        pd.read_csv(CLEAN / "msoa_distance_charing_cross.csv")[["msoa11_code", "log_dist_cc"]], on="msoa11_code")
    dm = md[["log_per1k_IR", "log_dist_cc"]] - md.groupby("la_code")[["log_per1k_IR", "log_dist_cc"]].transform("mean")
    out = []
    for v, lab in labs.items():
        r = mc.loc[v]
        out.append(f"{lab} & {num(np.log(b.per1k_IR).corr(b[v]))} & {num(r.corr_overall)} & "
                   f"{num(r.corr_within_borough)} \\\\")
    out.append(f"Log distance to Charing Cross & & {num(md.log_per1k_IR.corr(md.log_dist_cc))} & "
               f"{num(dm.log_per1k_IR.corr(dm.log_dist_cc))} \\\\")
    out.append("\\midrule")
    r = ac[(ac.measure.str.contains("1.5")) & ac.against.str.contains("distance")].iloc[0]
    out.append(f"Access index (1.5 km) against log distance & & {num(r.corr_overall)} & {num(r.corr_within_borough)} \\\\")
    r = ac[(ac.measure.str.contains("1.5")) & ac.against.str.contains("own")].iloc[0]
    out.append(f"Access index (1.5 km) against log own density & & {num(r.corr_overall)} & {num(r.corr_within_borough)} \\\\")
    return "\n".join(out)


def prow(ps) -> str:
    """Row of bootstrap p-values in brackets, placed beneath a coefficient row."""
    return " & " + " & ".join(f"({pv(p)})" for p in ps) + " \\\\[3pt]"


def crow(label, coefs, d=2, extra="") -> str:
    return f"{label} & " + " & ".join(num(c, d) for c in coefs) + extra + " \\\\"


def decomp_table() -> str:
    d = pd.read_csv(ES / "preperiod_check_decomposition.csv")
    d = d[d["sample"] == f"{START}-2025"]
    r = pd.read_csv(ES / "reversal_decomposition.csv")
    keys = ["D:C", "D:R", "D:L", "R_minus_C"]
    out = ["\\multicolumn{5}{@{}l}{\\textit{Migration, net moves per 1,000 group residents}} \\\\"]
    labels = [("Migration, all ages", "All ages"), ("Migration, ages 20-29", "Ages 20 to 29"),
              ("Migration, ages 30-39", "Ages 30 to 39"),
              ("Migration, family proxy (0-15 and 30-49)", "Family proxy"),
              ("Migration, ages 50+", "Ages 50 and over")]
    for o, lab in labels:
        t = d[d.outcome == o].set_index("name")
        out.append(crow(lab, [t.loc[k, "coef"] for k in keys]))
        out.append(prow([t.loc[k, "p_wcb"] for k in keys]))
    out.append("\\multicolumn{5}{@{}l}{\\textit{Prices, log points}} \\\\")
    for o, lab, sc in (("Rents (PIPR), no trend", "Rents", 1),
                       ("Rents (PIPR), pre-trend projected (secondary, not requested)", "Rents, trend projected", 1),
                       ("MSOA house prices, headline spec", "House prices, headline", 100)):
        t = r[r.outcome == o].set_index("name")
        out.append(crow(lab, [t.loc[k, "coef"] * sc for k in keys]))
        out.append(prow([t.loc[k, "p_wcb"] for k in keys]))
    return "\n".join(out)


def ddd_table(ddd) -> str:
    yrs = ["2016", "2017", "2018", "2020", "2021", "2022", "2023", "2024"]
    per = ["C", "R", "L", "reopening_minus_closure"]
    rows_a, rows_b = [], []
    for comp, lab in (("family proxy", "Family proxy"), ("50+", "Ages 50 and over")):
        y = ddd[ddd.model == f"DDD vs {comp}, yearly"].set_index("term")
        p = ddd[ddd.model == f"DDD vs {comp}, periods"].set_index("term")
        rows_a += [crow(lab, [y.loc[k, "coef"] for k in yrs]), prow([y.loc[k, "p_wcb"] for k in yrs])]
        rows_b += [crow(lab, [p.loc[k, "coef"] for k in per]), prow([p.loc[k, "p_wcb"] for k in per])]
    a = ("\\begin{tabularx}{\\linewidth}{@{}L*{8}{c}@{}}\n\\toprule\n\\multicolumn{9}{@{}l}{\\textit{Panel A. Yearly "
         "coefficients, year ending June (2019 omitted)}} \\\\\n & " + " & ".join(yrs) + " \\\\\n\\midrule\n"
         + "\n".join(rows_a) + "\n\\bottomrule\n\\end{tabularx}")
    b = ("\\begin{tabularx}{\\linewidth}{@{}L*{4}{c}@{}}\n\\toprule\n\\multicolumn{5}{@{}l}{\\textit{Panel B. Period "
         "model (reference 2016 to 2019)}} \\\\\n & Closure & Reopening & Later & Reopening minus closure \\\\\n"
         "\\midrule\n" + "\n".join(rows_b) + "\n\\bottomrule\n\\end{tabularx}")
    return a + "\n\n\\medskip\n" + b


def robust_table() -> str:
    a = pd.read_csv(ES / "report_migration_2016.csv", dtype={"term": str})
    y = a[a.analysis == "event study"]
    keys = ["2020", "2022", "reopening_minus_closure"]
    rows = [("age20_29", "none", "32 boroughs", "(1) Ages 20 to 29"),
            ("age20_29", "student share", "32 boroughs", "(2) Ages 20 to 29, students"),
            ("age20_29", "none", "drop top-5 student boroughs", "(3) Ages 20 to 29, drop five"),
            ("age20_29", "hospitality I+RSTU", "32 boroughs", "(4) Ages 20 to 29, hospitality"),
            ("age20_24", "none", "32 boroughs", "(5) Ages 20 to 24"),
            ("age20_24", "student share", "32 boroughs", "(6) Ages 20 to 24, students"),
            ("age20_24", "none", "drop top-5 student boroughs", "(7) Ages 20 to 24, drop five"),
            ("age25_29", "none", "32 boroughs", "(8) Ages 25 to 29"),
            ("age25_29", "student share", "32 boroughs", "(9) Ages 25 to 29, students"),
            ("age25_29", "none", "drop top-5 student boroughs", "(10) Ages 25 to 29, drop five")]
    out = ["\\multicolumn{5}{@{}l}{\\textit{Event studies}} \\\\"]
    for g, c, s, lab in rows:
        t = y[(y.group == g) & (y.control == c) & (y["sample"] == s)].set_index("term")
        out.append(crow(lab, [t.loc[k, "coef"] for k in keys], extra=f" & {int(t.n_obs.iloc[0])}"))
        out.append(prow([t.loc[k, "p_wcb"] for k in keys])[:-7] + " & \\\\[3pt]")
    d = a[a.analysis == "triple difference"]
    out.append("\\multicolumn{5}{@{}l}{\\textit{Triple differences}} \\\\")
    i = 11
    for comp, lab in (("family_0_15_30_49", "family proxy"), ("age50plus", "ages 50+")):
        for c, clab in (("none", ""), ("hospitality I+RSTU", ", hospitality")):
            t = d[(d.group == comp) & (d.control == c) & (d["sample"] == "32 boroughs")].set_index("term")
            out.append(crow(f"({i}) Against {lab}{clab}", [t.loc[k, "coef"] for k in keys],
                            extra=f" & {int(t.n_obs.iloc[0])}"))
            out.append(prow([t.loc[k, "p_wcb"] for k in keys])[:-7] + " & \\\\[3pt]")
            i += 1
    return "\n".join(out)


def rent_tests_table() -> str:
    r = pd.read_csv(ES / "rent_tests.csv", dtype={"term": str})
    a = r[r.test == "1 rent-change control"]
    keys = ["2020", "2021", "2022", "reopening_minus_closure"]
    rows_a = []
    i = 1
    for comp, lab in (("family_0_15_30_49", "family proxy"), ("age50plus", "ages 50+")):
        for c, clab in (("none", ""), ("rent change 2019Q4-2021Q4 x young x year", ", rent change")):
            t = a[(a.group == comp) & (a.control == c)].set_index("term")
            rows_a += [crow(f"({i}) Against {lab}{clab}", [t.loc[k, "coef"] for k in keys]),
                       prow([t.loc[k, "p_wcb"] for k in keys])]
            i += 1
    b = r[r.test == "2 pre-pandemic"]
    rows_b = []
    for g, lab in (("age20_29", "Ages 20 to 29"), ("family_0_15_30_49", "Against family proxy")):
        t = b[b.group == g].set_index("control")
        cs = ["dlr_lag 2017-2019", "dlr_contemp 2016-2019"]
        rows_b += [crow(f"({i}) {lab}", [t.loc[c, "coef"] for c in cs], d=3,
                        extra=" & " + " & ".join(str(int(t.loc[c, "n_obs"])) for c in cs)),
                   " & " + " & ".join(f"({pv(t.loc[c, 'p_wcb'])})" for c in cs) + " & & \\\\[3pt]"]
        i += 1
    e = pd.read_csv(ES / "report_migration_2016.csv", dtype={"term": str})
    e = e[(e.analysis == "event study") & (e.control == "none") & (e["sample"] == "32 boroughs")]
    rows_c = []
    for g, lab in (("age20_29", "Ages 20 to 29"), ("age30_39", "Ages 30 to 39")):
        t = e[e.group == g].set_index("term")
        rows_c += [crow(f"({i}) {lab}", [t.loc[k, "coef"] for k in ("2021", "2022")]),
                   prow([t.loc[k, "p_wcb"] for k in ("2021", "2022")])]
        i += 1
    pa = ("\\begin{tabularx}{\\linewidth}{@{}L*{4}{c}@{}}\n\\toprule\n\\multicolumn{5}{@{}l}{\\textit{Panel A. Triple "
          "difference with the rent-change control, 2016 to 2025}} \\\\\n & 2020 & 2021 & 2022 & Reopening minus closure "
          "\\\\\n\\midrule\n" + "\n".join(rows_a) + "\n\\bottomrule\n\\end{tabularx}")
    pb = ("\\begin{tabularx}{\\linewidth}{@{}L*{4}{c}@{}}\n\\toprule\n\\multicolumn{5}{@{}l}{\\textit{Panel B. Rent "
          "responsiveness before the pandemic}} \\\\\n & Lagged & Same year & N lagged & N same year \\\\\n\\midrule\n"
          + "\n".join(rows_b) + "\n\\bottomrule\n\\end{tabularx}")
    pc = ("\\begin{tabularx}{\\linewidth}{@{}L*{2}{c}@{}}\n\\toprule\n\\multicolumn{3}{@{}l}{\\textit{Panel C. Event "
          "studies by age group, 2016 to 2025}} \\\\\n & 2021 & 2022 \\\\\n\\midrule\n" + "\n".join(rows_c)
          + "\n\\bottomrule\n\\end{tabularx}")
    return pa + "\n\n\\medskip\n" + pb + "\n\n\\medskip\n" + pc


def ddd2529_table() -> str:
    r = pd.read_csv(ES / "students_25_29.csv", dtype={"term": str})
    r = r[(r.test == "25-29") & (r.control == "none") & (r["sample"] == "2016-2025")]
    yrs = ["2016", "2017", "2018", "2020", "2021", "2022", "2023", "2024"]
    per = ["C", "R", "L", "reopening_minus_closure"]
    tst = ["2022", "2022_minus_2020", "2020_dev_from_trend", "2022_dev_from_trend"]
    ra, rb, rc = [], [], []
    for comp, lab in (("family_0_15_30_49", "Family proxy"), ("age50plus", "Ages 50 and over")):
        y = r[(r.group == comp) & (r.model == "yearly")].set_index("term")
        q = r[(r.group == comp) & (r.model == "periods")].set_index("term")
        ra += [crow(lab, [y.loc[k, "coef"] for k in yrs]), prow([y.loc[k, "p_wcb"] for k in yrs])]
        rb += [crow(lab, [q.loc[k, "coef"] for k in per]), prow([q.loc[k, "p_wcb"] for k in per])]
        rc += [crow(lab, [y.loc[k, "coef"] for k in tst]), prow([y.loc[k, "p_wcb"] for k in tst])]
    a = ("\\begin{tabularx}{\\linewidth}{@{}L*{8}{c}@{}}\n\\toprule\n\\multicolumn{9}{@{}l}{\\textit{Panel A. Yearly "
         "coefficients, year ending June (2019 omitted)}} \\\\\n & " + " & ".join(yrs) + " \\\\\n\\midrule\n"
         + "\n".join(ra) + "\n\\bottomrule\n\\end{tabularx}")
    b = ("\\begin{tabularx}{\\linewidth}{@{}L*{4}{c}@{}}\n\\toprule\n\\multicolumn{5}{@{}l}{\\textit{Panel B. Period "
         "model (reference 2016 to 2019)}} \\\\\n & Closure & Reopening & Later & Reopening minus closure \\\\\n"
         "\\midrule\n" + "\n".join(rb) + "\n\\bottomrule\n\\end{tabularx}")
    c = ("\\begin{tabularx}{\\linewidth}{@{}L*{4}{c}@{}}\n\\toprule\n\\multicolumn{5}{@{}l}{\\textit{Panel C. Tests "
         "and deviations from the linear pre-trend}} \\\\\n & 2022 & 2022 minus 2020 & 2020 from trend & 2022 from "
         "trend \\\\\n\\midrule\n" + "\n".join(rc) + "\n\\bottomrule\n\\end{tabularx}")
    return a + "\n\n\\medskip\n" + b + "\n\n\\medskip\n" + c


def _block(header, rows, keys, ncol):
    out = [f"\\multicolumn{{{ncol + 1}}}{{@{{}}l}}{{\\textit{{{header}}}}} \\\\"]
    for lab, t in rows:
        out += [crow(lab, [t.loc[k, "coef"] for k in keys]), prow([t.loc[k, "p_wcb"] for k in keys])]
    return out


def _tabx(ncol, head, body):
    return (f"\\begin{{tabularx}}{{\\linewidth}}{{@{{}}L*{{{ncol}}}{{c}}@{{}}}}\n\\toprule\n & " + " & ".join(head)
            + " \\\\\n\\midrule\n" + "\n".join(body) + "\n\\bottomrule\n\\end{tabularx}")


def idlim_table() -> str:
    r = pd.read_csv(ES / "robustness_final.csv", dtype={"term": str})
    r = r[r.part == "A1"]
    keys = ["2020", "2021", "2022", "2022_minus_2020"]
    body = []
    for young, yl in (("age20_29", "20 to 29"), ("age25_29", "25 to 29")):
        for comp, cl in (("family_0_15_30_49", "the family proxy"), ("age50plus", "ages 50 and over")):
            rows = [(lab, r[(r.young == young) & (r.group == comp) & (r.control == c)].set_index("term"))
                    for c, lab in (("none", "No added control"), ("teleworkability", "Teleworkability"),
                                   ("garden access", "Garden access"), ("both", "Both"))]
            body += _block(f"Ages {yl} against {cl}", rows, keys, 4)
    return _tabx(4, ["2020", "2021", "2022", "2022 minus 2020"], body)


def natreg_table() -> str:
    r = pd.read_csv(EXT / "s2_national_ddd.csv", dtype={"term": str})
    r = r[r.outcome == "internal"]
    keys = ["2016", "2017", "2018", "2020", "2021", "2022", "2022_minus_2020"]
    labs = {"(a) none": "(a) No controls", "(b) teleworkability": "(b) Teleworkability",
            "(c) garden": "(c) Garden access", "(d) both": "(d) Both", "(e) region x year": "(e) Region by year",
            "(f) both + region x year": "(f) Both and region by year"}
    a = r[(r["sample"] == "all 316") & (r.young == "age20_29") & (r.comp == "family_0_15_30_49")]
    body = _block("Panel A. Ages 20 to 29 against the family proxy, 316 authorities", [
        (lab, a[a.spec == sp].set_index("term")) for sp, lab in labs.items()], keys, 7)
    pa = _tabx(7, ["2016", "2017", "2018", "2020", "2021", "2022", "2022 minus 2020"], body)
    keys_b = ["2020", "2022", "2022_minus_2020", "X_telework:2020", "X_garden:2020"]
    f = r[r.spec == "(f) both + region x year"]
    rows = []
    for smp, sl in (("all 316", "316"), ("outside London", "284")):
        for young, yl in (("age20_29", "20 to 29"), ("age25_29", "25 to 29")):
            for comp, cl in (("family_0_15_30_49", "family"), ("age50plus", "50+")):
                if smp == "all 316" and young == "age20_29" and comp == "family_0_15_30_49":
                    continue
                t = f[(f["sample"] == smp) & (f.young == young) & (f.comp == comp)].set_index("term")
                rows.append((f"{yl} vs {cl} ({sl})", t))
    body_b = _block("Panel B. Specification (f), other groups and samples", rows, keys_b, 5)
    pb = _tabx(5, ["2020", "2022", "2022 minus 2020", "Telework $\\times$ 2020", "Garden $\\times$ 2020"], body_b)
    return pa + "\n\n\\medskip\n" + pb


def measures_table() -> str:
    s2r = pd.read_csv(EXT / "s2_national_ddd.csv", dtype={"term": str})
    s2r = s2r[(s2r.outcome == "internal") & (s2r.young == "age20_29") & (s2r.comp == "family_0_15_30_49")
              & (s2r.spec == "(f) both + region x year")]
    cor = pd.read_csv(EXT / "s8c_corrected_ab.csv", dtype={"term": str})
    urb = pd.read_csv(EXT / "s8_urban_ddd.csv", dtype={"term": str})
    keys = ["2020", "2021", "2022", "2022_minus_2020", "X_garden:2020"]
    body = []
    for smp, hdr in (("all 316", "316 authorities"), ("outside London", "284 authorities outside London")):
        rows = [("Registered measure, units per resident", s2r[s2r["sample"] == smp].set_index("term")),
                ("(a) Food, drink, arts and leisure per resident",
                 cor[(cor.measure == "M_a_corr") & (cor["sample"] == smp) & (cor.young == "age20_29")].set_index("term")),
                ("(b) Food, drink, arts and leisure per km$^2$",
                 cor[(cor.measure == "M_b_corr") & (cor["sample"] == smp) & (cor.young == "age20_29")].set_index("term")),
                ("(c) Population-weighted access to food venues",
                 urb[(urb.measure == "M_c") & (urb["sample"] == smp) & (urb.young == "age20_29")].set_index("term"))]
        body += _block(hdr, rows, keys, 5)
    return _tabx(5, ["2020", "2021", "2022", "2022 minus 2020", "Garden $\\times$ 2020"], body)


def density_table() -> str:
    r = pd.read_csv(EXT / "s8b_density_check.csv", dtype={"term": str})
    r = r[r.part == "M_c density"]
    keys = ["2020", "2021", "2022", "2022_minus_2020"]
    body = []
    for smp, sl in (("all 316", "316 authorities"), ("outside London", "284 authorities outside London")):
        for young, yl in (("age20_29", "20 to 29"), ("age25_29", "25 to 29")):
            rows = [(lab, r[(r["sample"] == smp) & (r.young == young) & (r.spec == sp)].set_index("term"))
                    for sp, lab in (("none (departure 8 model)", "No density control"), ("job density", "Job density"),
                                    ("resident density", "Population density"),
                                    ("job and resident density", "Both densities"))]
            body += _block(f"Ages {yl}, {sl}", rows, keys, 4)
    return _tabx(4, ["2020", "2021", "2022", "2022 minus 2020"], body)


def ci(lo, hi, d=2) -> str:
    return f"[{num(lo, d)}, {num(hi, d)}]"


def vm_table() -> str:
    """Venue-mix design: registered decision rule (Panel A) and further registered estimates (Panel B)."""
    t = pd.concat([pd.read_csv(VM / f) for f in ("v5_main.csv", "v6_placebo_age.csv", "v8_robustness.csv")])
    t = t.drop_duplicates("label").set_index("label")
    la = pd.read_csv(VM / "v7_la_panel.csv")

    def msoa(lab, key):
        r = t.loc[key]
        return f"{lab} & {num(r.coef)} & {ci(r.ci_lo, r.ci_hi)} & {pv(r.p_wcb)} & {num(r.coef_per_sd)} \\\\"

    def panel(lab, model, term):
        r = la[(la.model == model) & (la.term == term)].iloc[0]
        return f"{lab} & {num(r.coef)} & {ci(r.ci_low, r.ci_high)} & {pv(r.p_wcb)} & \\\\"

    hdr = lambda s: f"\\multicolumn{{5}}{{@{{}}l}}{{\\textit{{{s}}}}} \\\\"
    return "\n".join([
        hdr("Panel A. Registered decision rule, MSOAs, change from Census 2011 to Census 2021"),
        msoa("(1) Headline, ages 25 to 34", "HEADLINE: 25-34, all controls"),
        msoa("(2) Placebo, change from 2001 to 2011, ages 25 to 34",
             "PLACEBO: 2001-2011 change, 25-34 (2001 excl. no usual address)"),
        msoa("(3) Ages 50 and over", "AGE 50+: 2011-2021 change"),
        msoa("(4) Stacked, ages 25 to 34 minus 50 and over", "STACKED difference 25-34 minus 50+ (MSOA and age-group FE)"),
        "\\midrule",
        hdr("Panel B. Further registered estimates, outside the decision rule"),
        msoa("(5) Ages 20 to 24", "20-24, all controls"),
        msoa("(6) Ages 20 to 34", "20-34, all controls"),
        msoa("(7) District effects only", "25-34, LA FE only"),
        msoa("(8) District effects and teleworkability only", "25-34, LA FE + telework_share only"),
        msoa("(9) District effects and garden access only", "25-34, LA FE + garden_share only"),
        msoa("(10) Top decile of student share dropped",
             "25-34, all controls, top student-share decile dropped (> 0.085)"),
        msoa("(11) OpenStreetMap 2019 venues", "25-34, all controls, OSM treatment"),
        msoa("(12) England and Wales", "England and Wales (Welsh closure dates)"),
        msoa("(13) England outside London", "England excluding London"),
        msoa("(14) Stacked, district-by-age effects", "Stacked difference with LA-by-age-group FE"),
        panel("(15) District panel, year to June 2021", "D: variety-days lost, year to June 2021", "2021"),
        panel("(16) District panel, reopening test, 2022 minus 2021",
              "R: reopening, share of variety closed Apr-Jul 2021", "2022_minus_2021"),
    ])


def arset(s) -> str:
    """Anderson-Rubin set string from rc_core in LaTeX form."""
    if pd.isna(s):
        return ""
    if s == "empty":
        return "empty"
    if s == "[-inf, +inf]":
        return "unbounded"
    s = s.replace("[-inf", "(-inf").replace("+inf]", "+inf)")
    s = re.sub(r"(?<![a-z])-?\d+\.\d+", lambda m: num(float(m.group())), s)
    return s.replace("-inf", "$-\\infty$").replace("+inf", "$+\\infty$").replace(" U ", " $\\cup$ ")


READING = {"inconclusive": "inconclusive", "full recovery": "full recovery", "lasting shift": "lasting shift",
           "shock deepened (above 0)": "shock deepened", "inconclusive (unbounded AR set)": "inconclusive, unbounded",
           "inconclusive (empty AR set)": "inconclusive, empty set"}


def rec_table() -> str:
    """Recovery design: registered headline, further estimates, heterogeneity and placebos."""
    t = pd.concat([pd.read_csv(REC / f) for f in ("r4_estimation.csv", "r5_heterogeneity.csv", "r6_placebos.csv")])
    t = t.set_index("label")

    def row(lab, key):
        r = t.loc[key]
        f = "" if pd.isna(r.fs_F) else num(r.fs_F, 1)
        return (f"{lab} & {num(r.beta)} & {ci(r.ci_lo, r.ci_hi)} & {f} & {arset(r.ar_set)} & "
                f"{READING[r.classification]} \\\\")

    hdr = lambda s: f"\\multicolumn{{6}}{{@{{}}l}}{{\\textit{{{s}}}}} \\\\"
    return "\n".join([
        hdr("Panel A. Registered headline"),
        row("(1) MSOAs, ages 25 to 34, measure (c)", "HEADLINE: MSOA 25-34, IV measure (c)"),
        "\\midrule",
        hdr("Panel B. Further registered estimates"),
        row("(2) MSOAs, 25 to 34, OLS", "MSOA 25-34, OLS"),
        row("(3) MSOAs, 25 to 34, variety-days lost", "MSOA 25-34, IV VDL"),
        row("(4) MSOAs, 20 to 29, measure (c)", "MSOA 20-29, IV measure (c)"),
        row("(5) Districts, 25 to 34, to 2025", "LA 25-34, IV measure (c), to 2025"),
        row("(6) Districts, 25 to 34, to 2024", "LA 25-34, IV measure (c), to 2024"),
        row("(7) Districts, 25 to 34, variety-days lost", "LA 25-34, IV VDL, to 2025"),
        row("(8) Districts, 20 to 29, to 2025", "LA 20-29, IV measure (c), to 2025"),
        row("(9) Districts, 20 to 29, to 2024", "LA 20-29, IV measure (c), to 2024"),
        "\\midrule",
        hdr("Panel C. Registered heterogeneity, MSOAs, ages 25 to 34"),
        row("(10) London", "London"),
        row("(11) Rest of England and Wales", "Rest of England and Wales"),
        row("(12) Density, lowest tercile", "population density tercile: low"),
        row("(13) Density, middle tercile", "population density tercile: middle"),
        row("(14) Density, highest tercile", "population density tercile: high"),
        row("(15) Access, lowest tercile", "measure (c) access tercile: low"),
        row("(16) Access, middle tercile", "measure (c) access tercile: middle"),
        row("(17) Access, highest tercile", "measure (c) access tercile: high"),
        "\\midrule",
        hdr("Panel D. Registered placebos, MSOAs"),
        row("(18) Ages 50 and over", "PLACEBO: ages 50+, 2019-21 shock, 2021-24 recovery"),
        row("(19) Pseudo shock 2015 to 2017, ages 25 to 34",
            "PLACEBO: 25-34 pseudo shock 2015-17, recovery 2017-19 (trend 2011-15)"),
    ])


def rec_series():
    """Horizontal coefficient plot of recovery coefficients with Wald 95% intervals, top to bottom."""
    t = pd.concat([pd.read_csv(REC / f) for f in ("r4_estimation.csv", "r5_heterogeneity.csv", "r6_placebos.csv")])
    t = t.set_index("label")
    rows = [("HEADLINE: MSOA 25-34, IV measure (c)", "Headline, MSOAs, 25 to 34"),
            ("MSOA 25-34, OLS", "OLS, MSOAs, 25 to 34"),
            ("MSOA 20-29, IV measure (c)", "MSOAs, 20 to 29"),
            ("LA 25-34, IV measure (c), to 2025", "Districts, 25 to 34"),
            ("LA 20-29, IV measure (c), to 2025", "Districts, 20 to 29"),
            ("Rest of England and Wales", "Outside London"),
            ("PLACEBO: ages 50+, 2019-21 shock, 2021-24 recovery", "Placebo, ages 50 and over"),
            ("PLACEBO: 25-34 pseudo shock 2015-17, recovery 2017-19 (trend 2011-15)", "Placebo, pseudo shock")]
    n = len(rows)
    pts = " ".join(f"({t.loc[k, 'beta']:.4f},{n - i}) +- ({(t.loc[k, 'ci_hi'] - t.loc[k, 'ci_lo']) / 2:.4f},0)"
                   for i, (k, _) in enumerate(rows))
    ticks = ",".join(f"{{{lab}}}" for _, lab in reversed(rows))
    return pts, ticks


def national_series():
    s2r = pd.read_csv(EXT / "s2_national_ddd.csv", dtype={"term": str})
    a = s2r[(s2r.outcome == "internal") & (s2r["sample"] == "all 316") & (s2r.young == "age20_29")
            & (s2r.comp == "family_0_15_30_49") & (s2r.spec == "(f) both + region x year") & s2r.term.str.fullmatch(r"\d{4}")]
    u = pd.read_csv(EXT / "s8_urban_ddd.csv", dtype={"term": str})
    b = u[(u.measure == "M_c") & (u["sample"] == "all 316") & (u.young == "age20_29") & u.term.str.fullmatch(r"\d{4}")]
    out = []
    for t, dx in ((a, -0.1), (b, 0.1)):
        t = t.assign(x=t.term.astype(int) + dx)
        out.append(es_series(t, 2019 + dx))
    return out


def honest_table() -> str:
    h = pd.read_csv(ES / "honestdid_breakdown.csv")
    lab = {"first_post": "Migration, year to June 2020", "avg_2020_2021": "Migration, 2020 and 2021 average",
           "q4_2021": "Rents, 2021Q4", "avg_2020Q1_2022Q4": "Rents, 2020Q1 to 2022Q4 average"}
    out = []
    for r in h.itertuples():
        out.append(f"{lab[r.target]} & {num(r.estimate)} & [{num(r.orig_lb)}, {num(r.orig_ub)}]"
                   f" & {num(r.breakdown_Mbar_RM, 3)} & {num(r.breakdown_M_SD, 3)} \\\\")
    return "\n".join(out)


def hp_table() -> str:
    s = pd.read_csv(ES / "msoa_summary_table.csv")
    s = s[s["sample"] == "all_quarters"]
    specs = ["baseline", "+dist", "+ptype", "+all4+dist", "headline", "headline+mediators", "+everything"]
    qs = [("avg_closure_2020Q1_2021Q4", "Closure average"), ("2020Q4", "2020Q4"), ("2022Q4", "2022Q4"),
          ("2025Q4", "2025Q4")]
    out = []
    for q, lab in qs:
        t = s[s.period == q].set_index("spec")
        out.append(crow(lab, [100 * t.loc[k, "coef"] for k in specs]))
        out.append(prow([t.loc[k, "p_wcb"] for k in specs]))
    return "\n".join(out)


def access_table() -> str:
    a = pd.read_csv(ES / "msoa_access_regression_table.csv")
    w = a[a.period.isin(["closure_2020Q1_2021Q4", "lagged_2020Q2_2022Q1"])]
    labs = [("D_msoa", "Own-MSOA density"), ("D_access_l15", "Access index, 1.5 km"),
            ("D_access_l10", "Access index, 1 km"), ("D_access_l30", "Access index, 3 km"),
            ("X_ring_0_1", "Ring 0 to 1 km"), ("X_ring_1_2", "Ring 1 to 2 km"), ("X_ring_2_5", "Ring 2 to 5 km")]
    ks = ["closure_2020Q1_2021Q4", "lagged_2020Q2_2022Q1"]
    out = []
    for v, lab in labs:
        t = w[w.treatment_var == v].set_index("period")
        out.append(crow(lab, [100 * t.loc[k, "coef"] for k in ks]))
        out.append(" & " + " & ".join(f"[{num(100 * t.loc[k, 'ci_low'])}, {num(100 * t.loc[k, 'ci_high'])}]"
                                      for k in ks) + " \\\\")
        out.append(prow([t.loc[k, "p_wcb"] for k in ks]))
    return "\n".join(out)


def rent_return_table(avg) -> str:
    out = []
    for r in avg.itertuples():
        lab = "2022Q1 to 2026Q3" if r.name == "avg_2022Q1_latest" else "2023Q3 to 2026Q3"
        out.append(f"{lab} & {num(r.coef)} & [{num(r.ci_low)}, {num(r.ci_high)}] & {pv(r.p_wcb)} \\\\")
    return "\n".join(out)


def rent_closure_text() -> str:
    """Rent event-study coefficients 2020Q2-2021Q2 with bootstrap p-values, for the prose."""
    rt = pd.read_csv(ES / "regression_table.csv", dtype={"period": str})
    r = rt[(rt.outcome == "rents") & (rt.treatment == "continuous") & (rt.spec == "baseline")].set_index("period")
    qs = ["2020Q2", "2020Q3", "2020Q4", "2021Q1", "2021Q2"]
    parts = [f"{num(r.loc[q, 'coef'])} in {q} (p-value {pv(r.loc[q, 'p_wcb']).strip('$')})" for q in qs]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def main():
    tpl = (HERE / "report_template.tex").read_text(encoding="utf-8")
    frags = build()
    missing = set(re.findall(r"<<([A-Z0-9_]+)>>", tpl)) - set(frags)
    assert not missing, f"template placeholders without data: {missing}"
    for k, v in frags.items():
        tpl = tpl.replace(f"<<{k}>>", v)
    out = REPORT / "report.tex"
    out.write_text(tpl, encoding="utf-8")
    print("written", out)


if __name__ == "__main__":
    main()
