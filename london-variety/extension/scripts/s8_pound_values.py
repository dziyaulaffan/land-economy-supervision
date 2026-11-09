"""Departure 8: pound values of the 2020 young-adult responses, using verified location-choice elasticities.

Responses (net moves per 1,000 group residents per SD, ages 20-29 vs family proxy, all 316 LADs, year to June 2020):
  garden access x young x 2020 in the registered headline model (f); and measure (c) (population-weighted FHRS access)
  x young x 2020 in model (f) with measure (c) in place of D (it survives the garden control at p < 0.05).
Conversion: a response R equals the population response to a rent change of dr = (R / 1000) / eps (stock elasticities,
eps = % change in population per 1% rent), or dr = R / f (annual-flow elasticities, f = change in annual net migration
per 1,000 per 1% housing cost), in per cent; value per month = |dr| / 100 x base rent.
Base: England median monthly private rent, 1 Oct 2018-30 Sep 2019 (ONS/VOA Private Rental Market Statistics,
Table 1.7, all categories), the source the pilot used for London.
"""
import pandas as pd

from ext_config import CLEAN, PILOT_RAW


def england_median_rent_2019():
    t = pd.read_excel(PILOT_RAW / "ons_prms" / "prms_oct2018_sep2019.xls", sheet_name="Table 1.7", header=None,
                      engine="calamine")
    hdr = t[t.iloc[:, 1] == "Area Code1"].iloc[0]
    return float(t[t.iloc[:, 1] == "E92000001"].iloc[0][hdr[hdr == "Median"].index[0]])


def main():
    rent = england_median_rent_2019()
    s2 = pd.read_csv(CLEAN / "s2_national_ddd.csv", dtype={"term": str})
    g = s2[(s2.outcome == "internal") & (s2["sample"] == "all 316") & (s2.young == "age20_29") &
           (s2.comp == "family_0_15_30_49") & (s2.spec == "(f) both + region x year") &
           (s2.term == "X_garden:2020")].iloc[0]
    u = pd.read_csv(CLEAN / "s8_urban_ddd.csv", dtype={"term": str})
    c = u[(u.measure == "M_c") & (u["sample"] == "all 316") & (u.young == "age20_29") & (u.term == "2020")].iloc[0]
    resp = {"garden access x young x 2020 (registered headline model)": g,
            "measure (c) pop-weighted FHRS access x young x 2020": c}
    e = pd.read_csv(CLEAN / "s8_elasticities.csv")
    e = e[(e.verified == "yes") & e.converted_elasticity_pop_wrt_rent.notna()].copy()
    e["kind"] = e.units.str.contains("probit").map({True: "annual flow", False: "stock"})
    e["label"] = e.paper.str.split("(").str[0].str.strip() + ", " + e.population.str.split(";").str[0]
    rows = []
    for rlab, r in resp.items():
        for x in e.itertuples():
            el = x.converted_elasticity_pop_wrt_rent
            if x.kind == "stock":
                dr = (r.coef / 1000) / el * 100          # % rent change with the same population effect
                dr_lo, dr_hi = (r.ci_low / 1000) / el * 100, (r.ci_high / 1000) / el * 100
            else:
                f = el * 10                               # pp per year per 1% -> per 1,000 per year per 1%
                dr, dr_lo, dr_hi = r.coef / f, r.ci_low / f, r.ci_high / f
            rows.append(dict(response=rlab, coef=r.coef, p_wcb=r.p_wcb, elasticity_source=x.label, kind=x.kind,
                             elasticity=el, rent_equiv_pct=dr, gbp_month=abs(dr) / 100 * rent,
                             gbp_ci=f"{min(abs(dr_lo), abs(dr_hi)) / 100 * rent:.0f} to "
                                    f"{max(abs(dr_lo), abs(dr_hi)) / 100 * rent:.0f}"
                             if dr_lo * dr_hi > 0 else "interval spans zero"))
    out = pd.DataFrame(rows)
    out.to_csv(CLEAN / "s8_pound_values.csv", index=False)
    L = [f"Base rent: England median monthly private rent Oct 2018-Sep 2019 = £{rent:,.0f}.\n"]
    for rlab, d in out.groupby("response", sort=False):
        L.append(f"**{rlab}**: coefficient {d.coef.iloc[0]:.2f} per 1,000 per SD (WCB p {d.p_wcb.iloc[0]:.3f}).\n")
        L.append("| Elasticity source | Kind | Elasticity | Rent-equivalent change (%) | £ per month | £ range from coefficient 95% CI |")
        L.append("|---|---|---|---|---|---|")
        for x in d.sort_values(["kind", "elasticity"]).itertuples():
            L.append(f"| {x.elasticity_source} | {x.kind} | {x.elasticity:.3f} | {x.rent_equiv_pct:+.2f} | "
                     f"{x.gbp_month:,.2f} | {x.gbp_ci} |")
        for k in ("stock", "annual flow"):
            dk = d[d.kind == k]
            L.append(f"\nRange, {k} elasticities: £{dk.gbp_month.min():,.2f} to £{dk.gbp_month.max():,.2f} a month "
                     f"(median £{dk.gbp_month.median():,.2f}).")
        L.append("")
    (CLEAN / "s8_pound_values.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
