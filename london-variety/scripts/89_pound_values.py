"""Convert the headline house-price and rent results into pounds.

House price: average closure-window (2020Q1-2021Q4) amenity coefficient from the headline MSOA specification
(log points per SD of log MSOA amenity density) applied to the median 2019 London sale price (Category A,
D/S/T/F, 32 boroughs, from the matched Land Registry sales): change = (exp(b) - 1) x median price.
Rent: average deviation from the projected pre-2020 rent trend from 2023Q3 to the latest quarter (100 x log
points per SD of borough log amenity density) applied to the London median monthly private rent, October 2018
to September 2019 (ONS/VOA Private Rental Market Statistics, Table 1.7, all categories): change =
(exp(d / 100) - 1) x median rent.
Intervals use the 95% CIs from borough-clustered (rent) and MSOA-clustered (house price) CR1 SEs.
The two "standard deviations" differ: house prices use the SD across 982 MSOAs, rents the SD across 32 boroughs.
"""
import numpy as np
import pandas as pd

from config import CLEAN, OUT, RAW, download

ES = OUT / "event_study"
PRMS_URL = ("https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/housing/datasets/"
            "privaterentalmarketsummarystatisticsinengland/october2018toseptember2019/"
            "privaterentalmarketstatistics13122019.xls")


def london_median_rent_2019() -> float:
    f = download(PRMS_URL, RAW / "ons_prms" / "prms_oct2018_sep2019.xls")
    t = pd.read_excel(f, sheet_name="Table 1.7", header=None, engine="calamine")
    row = t[t.iloc[:, 1] == "E12000007"].iloc[0]
    hdr = t[t.iloc[:, 1] == "Area Code1"].iloc[0]
    return float(row[hdr[hdr == "Median"].index[0]])


def main():
    s = pd.read_parquet(sorted(CLEAN.glob("msoa_sales_*.parquet"))[-1])
    lon = pd.read_csv(CLEAN / "london_amenity_density_2019.csv").la_code
    s19 = s[(s.ppd_category == "A") & s.property_type.isin(["D", "S", "T", "F"]) & (s.price >= 10_000)
            & s.quarter.str.startswith("2019") & s.laua.isin(lon)]
    p50 = float(s19.price.median())
    rent50 = london_median_rent_2019()

    h = pd.read_csv(ES / "msoa_headline_table.csv")
    hc = h[(h.spec == "headline") & (h.period == "avg_closure_2020Q1_2021Q4")].iloc[0]
    r = pd.read_csv(ES / "rent_return_summary.csv")
    rr = r[r.name == "avg_2023Q3_latest"].iloc[0]

    m = pd.read_csv(CLEAN / "msoa_amenity_controls.csv")
    b = pd.read_csv(CLEAN / "event_study_borough_vars.csv")
    sd_msoa, sd_borough = m.log_per1k_IR.std(), np.log(b.per1k_IR).std()

    to_gbp = lambda x, base: (np.exp(x) - 1) * base
    rows = [
        dict(measure="House price, closure window 2020Q1-2021Q4 (headline spec)", base="Median 2019 London sale price",
             base_value=p50, effect_log_points=hc.coef, ci_low=hc.ci_low, ci_high=hc.ci_high, p_wcb=hc.p_wcb,
             gbp=to_gbp(hc.coef, p50), gbp_ci_low=to_gbp(hc.ci_low, p50), gbp_ci_high=to_gbp(hc.ci_high, p50),
             sd_definition=f"1 SD of log I+R units per 1,000 across 982 MSOAs = {sd_msoa:.3f} log points "
                           f"(x{np.exp(sd_msoa):.2f} density)", n_obs=int(hc.n_obs)),
        dict(measure=f"Monthly rent, deviation from pre-2020 trend {rr.period}", base="Median London monthly rent "
             "Oct 2018-Sep 2019 (PRMS)", base_value=rent50, effect_log_points=rr.coef / 100,
             ci_low=rr.ci_low / 100, ci_high=rr.ci_high / 100, p_wcb=rr.p_wcb,
             gbp=to_gbp(rr.coef / 100, rent50), gbp_ci_low=to_gbp(rr.ci_low / 100, rent50),
             gbp_ci_high=to_gbp(rr.ci_high / 100, rent50),
             sd_definition=f"1 SD of log I+R units per 1,000 across 32 boroughs = {sd_borough:.3f} log points "
                           f"(x{np.exp(sd_borough):.2f} density)", n_obs=int(rr.n_obs)),
    ]
    out = pd.DataFrame(rows)
    out.to_csv(ES / "pound_values.csv", index=False)
    for r_ in out.itertuples():
        print(f"{r_.measure}: {100 * r_.effect_log_points:.2f} log pts (CI {100 * r_.ci_low:.2f} to "
              f"{100 * r_.ci_high:.2f}, WCB p {r_.p_wcb:.3f}) x {r_.base} GBP {r_.base_value:,.0f} "
              f"= GBP {r_.gbp:,.0f} (CI {r_.gbp_ci_low:,.0f} to {r_.gbp_ci_high:,.0f}); {r_.sd_definition}")
    print(f"2019 sales used for the median price: {len(s19):,}")


if __name__ == "__main__":
    main()
