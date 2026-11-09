"""Step 2 check (departure from the pre-analysis plan, added after Step 2): students.

1. Headline specification (f) (teleworkability and garden x young x year, region x young x year effects) plus the
   2011 full-time student share x young x year; ages 20-29 and 25-29 against the family proxy; all 316 LADs and the
   284 outside London.
2. Headline specification excluding the 30 LADs with the highest 2011 student share (of the 316).
3. Leave-one-out 2020 coefficient outside London (headline, 20-29 vs family proxy): contribution = full estimate
   minus the estimate without that LAD; the ten largest contributions in the direction of the full estimate.
WCR bootstrap clustered by LA (B = 9,999) for 1 and 2; point estimates only in the leave-one-out loop.
"""
import pandas as pd

from e_core import B, SEED, cell, ddd_diff, rademacher
from ext_config import CLEAN
import s2_national_ddd as s2

HEAD = ("X_telework", "X_garden")
KEYS = ["2020", "2021", "2022", "2022_minus_2020", "X_garden:2020"]
YOUNG = {"age20_29": "20-29", "age25_29": "25-29"}


def main():
    p = s2.panel("internal")
    ctl = pd.read_csv(CLEAN / "s1_controls_la2023.csv")[["la_code", "student_share", "X_student_share"]]
    c = pd.read_csv(CLEAN / "b3_la_crosssection.csv")[["la_code", "la_name"]]
    p = p.merge(ctl, on="la_code").merge(c, on="la_code").rename(columns={"X_student_share": "X_student"})
    comp = "family_0_15_30_49"
    out, L = [], []

    # 1. student share added
    L.append("### 1. Headline (f) plus student share x young x year, against the family proxy (WCB p)\n")
    L.append("| Sample | Young | Spec | 2020 | 2021 | 2022 | 2022 - 2020 | Garden x 2020 | Student x 2020 | LAs |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for sample in ("all 316", "outside London"):
        q = p if sample == "all 316" else p[~p.london.astype(bool)]
        w = rademacher(B, q.la_code.nunique(), SEED)
        for young, yl in YOUNG.items():
            q = q.assign(dy=q[young] - q[comp])
            for spec, ctrl in (("(f) headline", HEAD), ("(f) + student share", HEAD + ("X_student",))):
                t = ddd_diff(q, ctrl, True, w=w)
                out.append(t.assign(part="student control", sample=sample, young=young, spec=spec))
                st = cell(t, "X_student:2020") if "X_student" in ctrl else ""
                L.append(f"| {sample} | {yl} | {spec} | " + " | ".join(cell(t, k) for k in KEYS)
                         + f" | {st} | {int(t.n_clusters.iloc[0])} |")
                print(L[-1], flush=True)

    # 2. drop the 30 highest student shares
    top = p.drop_duplicates("la_code").nlargest(30, "student_share")[["la_code", "la_name", "student_share",
                                                                      "london"]]
    L.append("\n### 2. Headline (f) excluding the 30 LADs with the highest 2011 student share (WCB p)\n")
    L.append("| Sample | Young | 2020 | 2021 | 2022 | 2022 - 2020 | Garden x 2020 | LAs |")
    L.append("|---|---|---|---|---|---|---|---|")
    for sample in ("all 316", "outside London"):
        q = p[~p.la_code.isin(top.la_code)]
        if sample == "outside London":
            q = q[~q.london.astype(bool)]
        w = rademacher(B, q.la_code.nunique(), SEED)
        for young, yl in YOUNG.items():
            q = q.assign(dy=q[young] - q[comp])
            t = ddd_diff(q, HEAD, True, w=w)
            out.append(t.assign(part="drop top-30 students", sample=sample, young=young, spec="(f) headline"))
            L.append(f"| {sample} | {yl} | " + " | ".join(cell(t, k) for k in KEYS)
                     + f" | {int(t.n_clusters.iloc[0])} |")
            print(L[-1], flush=True)
    L.append("\nExcluded LADs (2011 full-time students aged 18+ per resident aged 16+): "
             + "; ".join(f"{r.la_name} {r.student_share:.1%}" + (" (London)" if r.london else "")
                         for r in top.itertuples()) + ".")

    # 3. leave-one-out outside London
    q = p[~p.london.astype(bool)].assign(dy=lambda x: x.age20_29 - x[comp])
    full = ddd_diff(q, HEAD, True, boot=False).set_index("term").loc["2020", "coef"]
    loo = []
    for b in sorted(q.la_code.unique()):
        e = ddd_diff(q[q.la_code != b], HEAD, True, boot=False).set_index("term").loc["2020", "coef"]
        loo.append((b, e, full - e))
    loo = pd.DataFrame(loo, columns=["la_code", "coef_2020_without", "contribution"]).merge(
        p.drop_duplicates("la_code")[["la_code", "la_name", "region", "D", "student_share"]], on="la_code")
    loo = loo.sort_values("contribution", ascending=full < 0)
    loo.to_csv(CLEAN / "s2b_loo_2020_outside_london.csv", index=False)
    L.append(f"\n### 3. Leave-one-out, 2020 coefficient outside London (headline, 20-29 vs family proxy)\n")
    L.append(f"Full estimate {full:.3f}; leave-one-out range {loo.coef_2020_without.min():.3f} to "
             f"{loo.coef_2020_without.max():.3f} across {len(loo)} LADs.\n")
    L.append("| LAD | Region | D | Student share | 2020 coefficient without it | Contribution |")
    L.append("|---|---|---|---|---|---|")
    for r in loo.head(10).itertuples():
        L.append(f"| {r.la_name} | {r.region} | {r.D:.2f} | {r.student_share:.1%} | {r.coef_2020_without:.3f} | "
                 f"{r.contribution:+.3f} |")
    res = pd.concat(out, ignore_index=True).drop(columns=["t_bootcluster"], errors="ignore")
    res.to_csv(CLEAN / "s2b_student_check.csv", index=False)
    (CLEAN / "s2b_student_check.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[-14:]))


if __name__ == "__main__":
    main()
